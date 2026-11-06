//! Distribución por dispositivo con HPKE RFC 9180, modalidad Base.
//! X25519/HKDF-SHA256/AES-256-GCM. Base cifra al receptor pero NO autentica
//! la identidad del remitente ni prueba que un dispositivo sea confiable.
//! El alta debe autorizarse con sesión + prueba de posesión en una fase futura.
use hpke::{
    aead::AesGcm256, kdf::HkdfSha256, kem::X25519HkdfSha256, setup_receiver, setup_sender,
    Deserializable, Kem as _, OpModeR, OpModeS, Serializable,
};
use std::collections::BTreeMap;
use hpke::rand_core::RngCore;
use zeroize::Zeroizing;

type Kem = X25519HkdfSha256;
const MAGIC: &[u8; 8] = b"SUHPKE01";
const INFO: &[u8] = b"smartuni-2.0/device-key-wrap/v1";
const HEADER_LEN: usize = 8 + 8 + 32;
pub const WRAPPED_LEN: usize = HEADER_LEN + 32 + 16;

#[derive(Debug, PartialEq, Eq)]
pub enum DeviceError {
    Invalid,
    Revoked,
    AuthenticationFailed,
}

/// Clave privada: exclusivamente en almacén seguro del destinatario.
/// El llamador es responsable de custodiarla, nunca enviarla al servidor.
pub fn generate_keypair() -> (Zeroizing<[u8; 32]>, [u8; 32]) {
    let mut csprng = hpke::rand_core::OsRng;
    let (sk, pk) = Kem::gen_keypair(&mut csprng);
    let mut private = Zeroizing::new([0u8; 32]);
    private.copy_from_slice(sk.to_bytes().as_slice());
    let mut public = [0u8; 32];
    public.copy_from_slice(pk.to_bytes().as_slice());
    (private, public)
}

/// Un paquete contiene epoch visible y clave encapsulada HPKE.
/// El recipient debe verificar que su epoch/owner esperado coincidan.
pub fn wrap(
    epoch: u64,
    recipient_public: &[u8; 32],
    content_key: &[u8; 32],
    owner_context: &[u8],
) -> Result<Vec<u8>, DeviceError> {
    if epoch == 0 || owner_context.is_empty() || owner_context.len() > 256 {
        return Err(DeviceError::Invalid);
    }
    let pk = <Kem as hpke::Kem>::PublicKey::from_bytes(recipient_public)
        .map_err(|_| DeviceError::Invalid)?;
    let mut rng = hpke::rand_core::OsRng;
    let (enc, mut sender) =
        setup_sender::<AesGcm256, HkdfSha256, Kem, _>(&OpModeS::Base, &pk, INFO, &mut rng)
            .map_err(|_| DeviceError::Invalid)?;
    let mut out = Vec::with_capacity(WRAPPED_LEN);
    out.extend_from_slice(MAGIC);
    out.extend_from_slice(&epoch.to_be_bytes());
    out.extend_from_slice(enc.to_bytes().as_slice());
    let mut aad = out.clone();
    aad.extend_from_slice(owner_context);
    let encrypted = sender
        .seal(content_key, &aad)
        .map_err(|_| DeviceError::Invalid)?;
    if encrypted.len() != 48 {
        return Err(DeviceError::Invalid);
    }
    out.extend_from_slice(&encrypted);
    Ok(out)
}

pub fn unwrap(
    epoch: u64,
    recipient_private: &[u8; 32],
    package: &[u8],
    owner_context: &[u8],
) -> Result<Zeroizing<[u8; 32]>, DeviceError> {
    if package.len() != WRAPPED_LEN
        || &package[..8] != MAGIC
        || epoch == 0
        || u64::from_be_bytes(
            package[8..16]
                .try_into()
                .map_err(|_| DeviceError::Invalid)?,
        ) != epoch
        || owner_context.is_empty()
        || owner_context.len() > 256
    {
        return Err(DeviceError::Invalid);
    }
    let sk = <Kem as hpke::Kem>::PrivateKey::from_bytes(recipient_private)
        .map_err(|_| DeviceError::Invalid)?;
    let enc = <Kem as hpke::Kem>::EncappedKey::from_bytes(&package[16..48])
        .map_err(|_| DeviceError::Invalid)?;
    let mut receiver =
        setup_receiver::<AesGcm256, HkdfSha256, Kem>(&OpModeR::Base, &sk, &enc, INFO)
            .map_err(|_| DeviceError::AuthenticationFailed)?;
    let mut aad = package[..HEADER_LEN].to_vec();
    aad.extend_from_slice(owner_context);
    let key = receiver
        .open(&package[HEADER_LEN..], &aad)
        .map_err(|_| DeviceError::AuthenticationFailed)?;
    if key.len() != 32 {
        return Err(DeviceError::AuthenticationFailed);
    }
    let mut plaintext = Zeroizing::new([0u8; 32]);
    plaintext.copy_from_slice(&key);
    Ok(plaintext)
}

#[derive(Debug, Default)]
pub struct DeviceRoster {
    epoch: u64,
    devices: BTreeMap<String, ([u8; 32], bool)>,
}

impl DeviceRoster {
    pub fn new() -> Self {
        Self {
            epoch: 1,
            devices: BTreeMap::new(),
        }
    }
    pub fn epoch(&self) -> u64 {
        self.epoch
    }
    pub fn enroll(&mut self, id: &str, public_key: [u8; 32]) -> Result<(), DeviceError> {
        if id.len() < 8
            || id.len() > 128
            || !id
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_'))
            || self.devices.contains_key(id)
        {
            return Err(DeviceError::Invalid);
        }
        self.devices.insert(id.to_string(), (public_key, true));
        Ok(())
    }
    /// Revoca un destinatario y genera una clave NUEVA para el siguiente epoch.
    /// El dueño debe re-cifrar/re-envolver los datos que el retirado conocía;
    /// no existe borrado retroactivo de contenido que éste haya copiado.
    pub fn revoke_and_rotate(&mut self, id: &str) -> Result<(u64, Zeroizing<[u8; 32]>), DeviceError> {
        let next = self.epoch.checked_add(1).ok_or(DeviceError::Invalid)?;
        let device = self.devices.get_mut(id).ok_or(DeviceError::Invalid)?;
        if !device.1 {
            return Err(DeviceError::Revoked);
        }
        let mut next_secret = Zeroizing::new([0u8; 32]);
        hpke::rand_core::OsRng.fill_bytes(next_secret.as_mut());
        device.1 = false;
        self.epoch = next;
        Ok((next, next_secret))
    }
    pub fn wrap_for(
        &self,
        id: &str,
        secret: &[u8; 32],
        owner: &[u8],
    ) -> Result<Vec<u8>, DeviceError> {
        match self.devices.get(id) {
            Some((pk, true)) => wrap(self.epoch, pk, secret, owner),
            Some(_) => Err(DeviceError::Revoked),
            None => Err(DeviceError::Invalid),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn hpke_key_distribution_multiple_devices_and_owner_binding() {
        let (alice_sk, alice_pk) = generate_keypair();
        let (bob_sk, bob_pk) = generate_keypair();
        let key = [17u8; 32];
        let owner = b"owner-uuid-lab";
        let mut roster = DeviceRoster::new();
        roster.enroll("device-alice", alice_pk).unwrap();
        roster.enroll("device-bob", bob_pk).unwrap();
        let a = roster.wrap_for("device-alice", &key, owner).unwrap();
        let b = roster.wrap_for("device-bob", &key, owner).unwrap();
        assert_eq!(&*unwrap(1, &alice_sk, &a, owner).unwrap(), &key);
        assert_eq!(&*unwrap(1, &bob_sk, &b, owner).unwrap(), &key);
        assert!(unwrap(1, &bob_sk, &a, owner).is_err());
        assert!(unwrap(1, &alice_sk, &a, b"other-owner").is_err());
        let mut tampered = a.clone();
        tampered[55] ^= 0x01;
        assert!(unwrap(1, &alice_sk, &tampered, owner).is_err());
    }
    #[test]
    fn revoke_rotates_epoch_prevents_future_wrapping() {
        let (alice_sk, alice_pk) = generate_keypair();
        let (_, bob_pk) = generate_keypair();
        let mut roster = DeviceRoster::new();
        roster.enroll("device-alice", alice_pk).unwrap();
        roster.enroll("device-bob", bob_pk).unwrap();
        let old = roster
            .wrap_for("device-alice", &[6u8; 32], b"owner")
            .unwrap();
        let (epoch, new_key) = roster.revoke_and_rotate("device-alice").unwrap();
        assert_eq!(epoch, 2);
        assert_ne!(&*new_key, &[6u8; 32]);
        assert_eq!(
            roster
                .wrap_for("device-alice", &[7u8; 32], b"owner")
                .unwrap_err(),
            DeviceError::Revoked
        );
        let new_package = roster.wrap_for("device-bob", &new_key, b"owner").unwrap();
        assert!(unwrap(1, &alice_sk, &new_package, b"owner").is_err());
        // Revocar no invalida información ya vista ni descifrada previamente.
        assert_eq!(&*unwrap(1, &alice_sk, &old, b"owner").unwrap(), &[6u8; 32]);
    }
}

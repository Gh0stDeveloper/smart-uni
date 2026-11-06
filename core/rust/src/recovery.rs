//! Copia de recuperación de una clave de contenido de 32 bytes.
//! Argon2id v19 m=65536 KiB, t=3, p=1 + AES-256-GCM.
//! La frase debe ser de alta entropía y creada fuera de la app. Sin escrow.
use aes_gcm::{
    aead::{rand_core::RngCore, Aead, AeadCore, KeyInit, OsRng, Payload},
    Aes256Gcm, Nonce,
};
use argon2::{Algorithm, Argon2, Params, Version};
use zeroize::Zeroizing;

const MAGIC: &[u8; 8] = b"SURECV01";
const SALT_LEN: usize = 16;
const NONCE_LEN: usize = 12;
pub const PACKAGE_LEN: usize = 8 + SALT_LEN + NONCE_LEN + 32 + 16;
const HEADER_LEN: usize = 8 + SALT_LEN + NONCE_LEN;

#[derive(Debug, PartialEq, Eq)]
pub enum RecoveryError {
    InvalidInput,
    Unavailable,
    AuthenticationFailed,
}

fn derive(passphrase: &[u8], salt: &[u8]) -> Result<Zeroizing<[u8; 32]>, RecoveryError> {
    // Un límite evita entradas inmensas/ataques DoS. Entropía real no se puede
    // verificar solo por longitud; se exige frase generada aleatoriamente.
    if !(16..=512).contains(&passphrase.len()) {
        return Err(RecoveryError::InvalidInput);
    }
    let params = Params::new(65536, 3, 1, Some(32)).map_err(|_| RecoveryError::Unavailable)?;
    let mut key = Zeroizing::new([0u8; 32]);
    Argon2::new(Algorithm::Argon2id, Version::V0x13, params)
        .hash_password_into(passphrase, salt, key.as_mut())
        .map_err(|_| RecoveryError::Unavailable)?;
    Ok(key)
}

/// Exporta solo la clave de contenido, nunca una contraseña de login o token.
/// Guardar PACKAGE en medio externo; no dejar passphrase en CLI/logs.
pub fn export(key: &[u8; 32], passphrase: &[u8]) -> Result<[u8; PACKAGE_LEN], RecoveryError> {
    let mut salt = [0u8; SALT_LEN];
    OsRng.fill_bytes(&mut salt);
    let wrap_key = derive(passphrase, &salt)?;
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
    let mut out = [0u8; PACKAGE_LEN];
    out[..8].copy_from_slice(MAGIC);
    out[8..24].copy_from_slice(&salt);
    out[24..36].copy_from_slice(&nonce);
    let cipher =
        Aes256Gcm::new_from_slice(wrap_key.as_ref()).map_err(|_| RecoveryError::Unavailable)?;
    let sealed = cipher
        .encrypt(
            &nonce,
            Payload {
                msg: key,
                aad: &out[..HEADER_LEN],
            },
        )
        .map_err(|_| RecoveryError::Unavailable)?;
    if sealed.len() != 48 {
        return Err(RecoveryError::Unavailable);
    }
    out[HEADER_LEN..].copy_from_slice(&sealed);
    Ok(out)
}

/// No retorna una clave si formato, contraseña, salt, nonce o tag fallan.
pub fn restore(blob: &[u8], passphrase: &[u8]) -> Result<Zeroizing<[u8; 32]>, RecoveryError> {
    if blob.len() != PACKAGE_LEN || &blob[..8] != MAGIC {
        return Err(RecoveryError::InvalidInput);
    }
    let wrap_key = derive(passphrase, &blob[8..24])?;
    let cipher =
        Aes256Gcm::new_from_slice(wrap_key.as_ref()).map_err(|_| RecoveryError::Unavailable)?;
    let plain = cipher
        .decrypt(
            Nonce::from_slice(&blob[24..36]),
            Payload {
                msg: &blob[HEADER_LEN..],
                aad: &blob[..HEADER_LEN],
            },
        )
        .map_err(|_| RecoveryError::AuthenticationFailed)?;
    if plain.len() != 32 {
        return Err(RecoveryError::AuthenticationFailed);
    }
    let mut key = Zeroizing::new([0u8; 32]);
    key.copy_from_slice(&plain);
    Ok(key)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn restore_roundtrip_and_wrong_password_fail() {
        let secret = [39u8; 32];
        let pass = b"prueba ficticia frase secreta bastante larga";
        let pkg = export(&secret, pass).unwrap();
        assert_ne!(&pkg[..8], b"SQLite f");
        assert_eq!(&*restore(&pkg, pass).unwrap(), &secret);
        assert_eq!(
            restore(&pkg, b"frase totalmente distinta e incorrecta").unwrap_err(),
            RecoveryError::AuthenticationFailed
        );
    }
    #[test]
    fn manipulated_salt_nonce_tag_and_header_fail() {
        let pass = b"frase de prueba generada externamente sin uso real";
        let package = export(&[23u8; 32], pass).unwrap();
        for index in [0, 8, 24, 35, 36, PACKAGE_LEN - 1] {
            let mut tampered = package;
            tampered[index] ^= 0x02;
            assert!(restore(&tampered, pass).is_err());
        }
    }
    #[test]
    fn corrupted_length_and_short_password_rejected() {
        assert!(export(&[1u8; 32], b"short").is_err());
        assert!(restore(b"bad", b"passphrase passphrase passphrase").is_err());
    }
}

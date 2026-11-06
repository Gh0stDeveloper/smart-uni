//! AES-256-GCM de RustCrypto 0.10.3, usado aquí para vectores reproducibles.
//! NO define aún formato de almacenamiento, recuperación ni gestión de claves.
//! El modo normal genera nonce aleatorio de 96 bits. NUNCA reutilizar nonce+clave.
use aes_gcm::{
    aead::{Aead, AeadCore, KeyInit, OsRng, Payload},
    Aes256Gcm, Nonce,
};

pub const KEY_LEN: usize = 32;
pub const NONCE_LEN: usize = 12;
pub const TAG_LEN: usize = 16;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Sealed {
    pub nonce: [u8; NONCE_LEN],
    pub ciphertext_and_tag: Vec<u8>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CryptoError {
    EncryptFailed,
    AuthenticationFailed,
}

/// El llamador debe generar, custodiar y destruir su clave fuera de esta API.
pub fn seal_random(
    key: &[u8; KEY_LEN],
    plaintext: &[u8],
    aad: &[u8],
) -> Result<Sealed, CryptoError> {
    let cipher = Aes256Gcm::new_from_slice(key).map_err(|_| CryptoError::EncryptFailed)?;
    let random_nonce = Aes256Gcm::generate_nonce(&mut OsRng);
    let ciphertext_and_tag = cipher
        .encrypt(
            &random_nonce,
            Payload {
                msg: plaintext,
                aad,
            },
        )
        .map_err(|_| CryptoError::EncryptFailed)?;
    let mut nonce = [0u8; NONCE_LEN];
    nonce.copy_from_slice(&random_nonce);
    Ok(Sealed {
        nonce,
        ciphertext_and_tag,
    })
}

/// Fallar cerrado ante ciphertext, etiqueta, AAD, clave o nonce adulterados.
pub fn open(key: &[u8; KEY_LEN], sealed: &Sealed, aad: &[u8]) -> Result<Vec<u8>, CryptoError> {
    let cipher = Aes256Gcm::new_from_slice(key).map_err(|_| CryptoError::AuthenticationFailed)?;
    cipher
        .decrypt(
            Nonce::from_slice(&sealed.nonce),
            Payload {
                msg: &sealed.ciphertext_and_tag,
                aad,
            },
        )
        .map_err(|_| CryptoError::AuthenticationFailed)
}

/// Autoprueba pública con vectores fijos NIST/BoringSSL; no reutilizar las claves.
pub fn known_answer_self_test() -> bool {
    let cipher = match Aes256Gcm::new_from_slice(&[0u8; KEY_LEN]) {
        Ok(cipher) => cipher,
        Err(_) => return false,
    };
    let nonce = Nonce::from_slice(&[0u8; NONCE_LEN]);
    let inputs: [&[u8]; 2] = [&[], &[0u8; 16]];
    let expected = [
        "530f8afbc74536b9a963b4f1c4cb738b",
        "cea7403d4d606b6e074ec5d3baf39d18d0d1c8a799996bf0265b98b5d48ab919",
    ];
    for (msg, reference) in inputs.iter().zip(expected.iter()) {
        let ciphertext = match cipher.encrypt(nonce, Payload { msg, aad: &[] }) {
            Ok(data) => data,
            Err(_) => return false,
        };
        if hex::encode(&ciphertext) != *reference {
            return false;
        }
        if cipher.decrypt(nonce, ciphertext.as_ref()).ok().as_deref() != Some(*msg) {
            return false;
        }
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn known_answer_vectors() {
        assert!(known_answer_self_test());
    }

    #[test]
    fn random_nonce_roundtrip_with_associated_data() {
        let key = [7u8; KEY_LEN];
        let first = seal_random(&key, b"apunte inventado", b"id:test").unwrap();
        let second = seal_random(&key, b"apunte inventado", b"id:test").unwrap();
        assert_ne!(first.nonce, second.nonce);
        assert_ne!(first.ciphertext_and_tag, b"apunte inventado");
        assert_eq!(open(&key, &first, b"id:test").unwrap(), b"apunte inventado");
        assert_eq!(
            open(&key, &second, b"id:test").unwrap(),
            b"apunte inventado"
        );
    }

    #[test]
    fn tag_tampering_and_wrong_aad_fail_closed() {
        let key = [11u8; KEY_LEN];
        let data = seal_random(&key, b"test", b"metadata").unwrap();
        assert_eq!(
            open(&key, &data, b"other").unwrap_err(),
            CryptoError::AuthenticationFailed
        );
        let mut tampered = data;
        *tampered.ciphertext_and_tag.last_mut().unwrap() ^= 0x01;
        assert_eq!(
            open(&key, &tampered, b"metadata").unwrap_err(),
            CryptoError::AuthenticationFailed
        );
    }
}

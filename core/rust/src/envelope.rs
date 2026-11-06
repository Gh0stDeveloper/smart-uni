//! Contenedor binario AES-256-GCM con cabecera versionada y AAD.
use aes_gcm::{
    aead::{Aead, AeadCore, KeyInit, OsRng, Payload},
    Aes256Gcm, Nonce,
};

const MAGIC: &[u8; 8] = b"SUAEAD01";
const ALG_AES256GCM: u8 = 1;
const PREFIX_LEN: usize = 8 + 1 + 2 + 12;
pub const MAX_CONTEXT: usize = 256;
pub const MAX_PLAINTEXT: usize = 8 * 1024 * 1024;

#[derive(Debug, PartialEq, Eq)]
pub enum EnvelopeError {
    Invalid,
    AuthenticationFailed,
}

/// Contexto visible pero autenticado: owner, clase, resource-id y epoch.
/// El nonce aleatorio de 96 bits no debe repetirse para una misma clave.
pub fn seal(key: &[u8; 32], context: &[u8], plaintext: &[u8]) -> Result<Vec<u8>, EnvelopeError> {
    if context.is_empty() || context.len() > MAX_CONTEXT || plaintext.len() > MAX_PLAINTEXT {
        return Err(EnvelopeError::Invalid);
    }
    let cipher = Aes256Gcm::new_from_slice(key).map_err(|_| EnvelopeError::Invalid)?;
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
    let mut output = Vec::with_capacity(PREFIX_LEN + context.len() + plaintext.len() + 16);
    output.extend_from_slice(MAGIC);
    output.push(ALG_AES256GCM);
    output.extend_from_slice(&(context.len() as u16).to_be_bytes());
    output.extend_from_slice(&nonce);
    output.extend_from_slice(context);
    let encrypted = cipher
        .encrypt(
            &nonce,
            Payload {
                msg: plaintext,
                aad: &output,
            },
        )
        .map_err(|_| EnvelopeError::Invalid)?;
    output.extend_from_slice(&encrypted);
    Ok(output)
}

/// Falla cerrado ante cabecera/versión no admitida, AAD distinto o corrupción.
pub fn open(
    key: &[u8; 32],
    expected_context: &[u8],
    input: &[u8],
) -> Result<Vec<u8>, EnvelopeError> {
    if input.len() < PREFIX_LEN + 1 + 16
        || input.len() > PREFIX_LEN + MAX_CONTEXT + MAX_PLAINTEXT + 16
    {
        return Err(EnvelopeError::Invalid);
    }
    if &input[..8] != MAGIC || input[8] != ALG_AES256GCM {
        return Err(EnvelopeError::Invalid);
    }
    let context_len = u16::from_be_bytes([input[9], input[10]]) as usize;
    if context_len == 0
        || context_len > MAX_CONTEXT
        || context_len != expected_context.len()
        || input.len() < PREFIX_LEN + context_len + 16
    {
        return Err(EnvelopeError::Invalid);
    }
    let header_len = PREFIX_LEN + context_len;
    if &input[PREFIX_LEN..header_len] != expected_context {
        return Err(EnvelopeError::AuthenticationFailed);
    }
    let cipher = Aes256Gcm::new_from_slice(key).map_err(|_| EnvelopeError::Invalid)?;
    cipher
        .decrypt(
            Nonce::from_slice(&input[11..23]),
            Payload {
                msg: &input[header_len..],
                aad: &input[..header_len],
            },
        )
        .map_err(|_| EnvelopeError::AuthenticationFailed)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn roundtrip_empty_and_unicode() {
        let key = [7u8; 32];
        for message in [b"".as_slice(), "Texto con ñ y 🔑".as_bytes()] {
            let encrypted = seal(&key, b"notes/owner-a/item-1/epoch-1", message).unwrap();
            assert_ne!(&encrypted[..8], b"SQLite f");
            assert_eq!(
                open(&key, b"notes/owner-a/item-1/epoch-1", &encrypted).unwrap(),
                message
            );
            assert_eq!(
                open(&key, b"notes/owner-b/item-1/epoch-1", &encrypted).unwrap_err(),
                EnvelopeError::AuthenticationFailed
            );
        }
    }
    #[test]
    fn wrong_key_modified_header_ciphertext_and_truncation_rejected() {
        let key = [4u8; 32];
        let ctx = b"files/u1/doc/epoch-3";
        let sealed = seal(&key, ctx, b"ficticio").unwrap();
        assert!(open(&[5u8; 32], ctx, &sealed).is_err());
        for ix in [0, 8, 9, 11, 23, sealed.len() - 1] {
            let mut corrupted = sealed.clone();
            corrupted[ix] ^= 0x01;
            assert!(open(&key, ctx, &corrupted).is_err(), "index {ix}");
        }
        for n in [0, 1, 20, sealed.len() - 1] {
            assert!(open(&key, ctx, &sealed[..n]).is_err());
        }
    }
    #[test]
    fn empty_context_and_oversized_rejected() {
        assert!(seal(&[0u8; 32], b"", b"any").is_err());
        assert!(seal(&[0u8; 32], &vec![0u8; 257], b"any").is_err());
        assert!(seal(&[0u8; 32], b"note", &vec![0u8; MAX_PLAINTEXT + 1]).is_err());
    }
}

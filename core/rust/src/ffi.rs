//! ABI C estable v1: sin transferir ownership ni cruzar panics.
//! Los punteros entrantes deben señalar memoria válida durante la llamada.
//! No autoriza recursos ni proporciona sesión autenticada.

use crate::{contracts::parse_operation, domain::normalize_email};
use std::{panic::catch_unwind, slice, str};

pub const ABI_VERSION: u32 = 1;
pub const OK: i32 = 0;
pub const ERR_POINTER: i32 = -1;
pub const ERR_INVALID: i32 = -2;
pub const ERR_INTERNAL: i32 = -3;

#[no_mangle]
pub extern "C" fn smartuni_abi_version() -> u32 {
    ABI_VERSION
}

fn protected<F: FnOnce() -> i32 + std::panic::UnwindSafe>(function: F) -> i32 {
    catch_unwind(function).unwrap_or(ERR_INTERNAL)
}

/// # Safety
/// ptr debe señalar len bytes legibles. No se acepta NULL, ni len=0.
unsafe fn view<'a>(ptr: *const u8, len: usize) -> Result<&'a [u8], i32> {
    if ptr.is_null() || len == 0 || len > crate::contracts::MAX_OPERATION_BYTES {
        return Err(ERR_POINTER);
    }
    Ok(slice::from_raw_parts(ptr, len))
}

/// Devuelve 0 si el correo cumple la regla local; el llamador conserva el buffer.
///
/// # Safety
/// ptr es válido durante la llamada; len no excede 1 MiB.
#[no_mangle]
pub unsafe extern "C" fn smartuni_validate_email_v1(ptr: *const u8, len: usize) -> i32 {
    protected(|| {
        let input = match view(ptr, len) {
            Ok(input) => input,
            Err(error) => return error,
        };
        match str::from_utf8(input)
            .ok()
            .and_then(|text| normalize_email(text).ok())
        {
            Some(_) => OK,
            None => ERR_INVALID,
        }
    })
}

/// Solo valida forma y versión, NO autorización de la identidad en actor_ref.
///
/// # Safety
/// ptr es válido durante la llamada; len no excede 1 MiB.
#[no_mangle]
pub unsafe extern "C" fn smartuni_validate_operation_v1(ptr: *const u8, len: usize) -> i32 {
    protected(|| {
        let input = match view(ptr, len) {
            Ok(input) => input,
            Err(error) => return error,
        };
        if parse_operation(input).is_ok() {
            OK
        } else {
            ERR_INVALID
        }
    })
}

/// Autoprueba criptográfica KAT; no recibe claves ni cifra datos externos.
#[no_mangle]
pub extern "C" fn smartuni_crypto_self_test_v1() -> i32 {
    protected(|| {
        if crate::crypto::known_answer_self_test() {
            OK
        } else {
            ERR_INVALID
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn abi_version_and_email() {
        assert_eq!(smartuni_abi_version(), 1);
        assert_eq!(
            unsafe { smartuni_validate_email_v1(b"User@UNI.EDU".as_ptr(), 12) },
            OK
        );
        assert_eq!(
            unsafe { smartuni_validate_email_v1(b"bad".as_ptr(), 3) },
            ERR_INVALID
        );
        assert_eq!(
            unsafe { smartuni_validate_email_v1(std::ptr::null(), 0) },
            ERR_POINTER
        );
    }

    #[test]
    fn abi_operation_and_invalid_pointer() {
        let payload = br#"{"schema_version":"1.0.0","operation":"notes.create","operation_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","actor_ref":"student@example.edu","occurred_at":"2026-11-06T04:00:00Z","payload":{}}"#;
        assert_eq!(
            unsafe { smartuni_validate_operation_v1(payload.as_ptr(), payload.len()) },
            OK
        );
        assert_eq!(
            unsafe { smartuni_validate_operation_v1(b"{}".as_ptr(), 2) },
            ERR_INVALID
        );
        assert_eq!(
            unsafe { smartuni_validate_operation_v1(std::ptr::null(), 1) },
            ERR_POINTER
        );
    }
}

/// Interfaz de bytes para contenedores y recuperación. El llamador es dueño de
/// las entradas/salidas y debe limpiarlas de memoria cuando contengan secretos.
/// Los buffers de salida NO pueden solaparse con ninguno de entrada.
///
/// # Safety
/// Todos los punteros no NULL deben ser válidos para sus longitudes indicadas
/// durante la llamada; salida válida, escribible y sin alias. La función no
/// puede verificar si un puntero arbitrario de C es realmente legible.
unsafe fn copy_output<F>(out: *mut u8, capacity: usize, written: *mut usize, operation: F) -> i32
where
    F: FnOnce() -> Result<Vec<u8>, i32> + std::panic::UnwindSafe,
{
    if written.is_null() || out.is_null() || capacity == 0 || capacity > 9 * 1024 * 1024 {
        return ERR_POINTER;
    }
    *written = 0;
    match catch_unwind(operation) {
        Ok(Ok(value)) if value.len() <= capacity => {
            std::ptr::copy_nonoverlapping(value.as_ptr(), out, value.len());
            *written = value.len();
            OK
        }
        Ok(Ok(_)) => ERR_POINTER,
        Ok(Err(error)) => error,
        Err(_) => ERR_INTERNAL,
    }
}

/// # Safety
/// ptr debe apuntar a len bytes legibles; len=0 es válido solo si ptr no es NULL.
unsafe fn bytes_limit<'a>(ptr: *const u8, len: usize, max: usize) -> Result<&'a [u8], i32> {
    if ptr.is_null() || len > max { return Err(ERR_POINTER); }
    Ok(slice::from_raw_parts(ptr, len))
}

/// AES-256-GCM para datos del cliente; metadata context autenticada.
/// # Safety
/// key: 32 bytes; context: 1..256 bytes; plain: <=8 MiB. Punteros de entrada
/// válidos, output válido, escribible, no solapado. El llamador borra su clave.
#[no_mangle]
pub unsafe extern "C" fn smartuni_seal_record_v1(
    key: *const u8, key_len: usize, context: *const u8, context_len: usize,
    plain: *const u8, plain_len: usize,
    out: *mut u8, capacity: usize, written: *mut usize,
) -> i32 {
    copy_output(out, capacity, written, || {
        let key_in = bytes_limit(key, key_len, 32)?;
        let ctx = bytes_limit(context, context_len, 256)?;
        let payload = bytes_limit(plain, plain_len, crate::envelope::MAX_PLAINTEXT)?;
        let secret: &[u8; 32] = key_in.try_into().map_err(|_| ERR_POINTER)?;
        crate::envelope::seal(secret, ctx, payload).map_err(|_| ERR_INVALID)
    })
}

/// # Safety
/// Reglas de punteros/buffers iguales a seal; bytes de ciphertext <=8MiB+300.
#[no_mangle]
pub unsafe extern "C" fn smartuni_open_record_v1(
    key: *const u8, key_len: usize, context: *const u8, context_len: usize,
    blob: *const u8, blob_len: usize,
    out: *mut u8, capacity: usize, written: *mut usize,
) -> i32 {
    copy_output(out, capacity, written, || {
        let secret: &[u8; 32] = bytes_limit(key, key_len, 32)?.try_into().map_err(|_| ERR_POINTER)?;
        let ctx = bytes_limit(context, context_len, 256)?;
        let input = bytes_limit(blob, blob_len, crate::envelope::MAX_PLAINTEXT + 300)?;
        crate::envelope::open(secret, ctx, input).map_err(|_| ERR_INVALID)
    })
}

/// # Safety
/// Clave 32 bytes y passphrase de 16..512 bytes, output mínimo 84 bytes.
#[no_mangle]
pub unsafe extern "C" fn smartuni_export_recovery_v1(
    key: *const u8, key_len: usize, passphrase: *const u8, pass_len: usize,
    out: *mut u8, capacity: usize, written: *mut usize,
) -> i32 {
    copy_output(out, capacity, written, || {
        let secret: &[u8; 32] = bytes_limit(key, key_len, 32)?.try_into().map_err(|_| ERR_POINTER)?;
        let phrase = bytes_limit(passphrase, pass_len, 512)?;
        crate::recovery::export(secret, phrase).map(|x| x.to_vec()).map_err(|_| ERR_INVALID)
    })
}

/// # Safety
/// Copia de recuperación de 84 bytes; passphrase 16..512; output 32 bytes.
#[no_mangle]
pub unsafe extern "C" fn smartuni_restore_recovery_v1(
    blob: *const u8, blob_len: usize, passphrase: *const u8, pass_len: usize,
    out: *mut u8, capacity: usize, written: *mut usize,
) -> i32 {
    copy_output(out, capacity, written, || {
        let package = bytes_limit(blob, blob_len, crate::recovery::PACKAGE_LEN)?;
        let phrase = bytes_limit(passphrase, pass_len, 512)?;
        crate::recovery::restore(package, phrase).map(|x| x.to_vec()).map_err(|_| ERR_INVALID)
    })
}

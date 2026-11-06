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

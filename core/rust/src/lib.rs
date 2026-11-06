//! Núcleo SMART UNI: dominio y contratos versionados sin IO.
pub mod contracts;
pub mod domain;
pub mod ffi;
pub const CORE_VERSION: &str = env!("CARGO_PKG_VERSION");
pub const CONTRACT_VERSION: &str = "1.0.0";
pub const LEGACY_STORAGE_VERSION: u32 = 1;

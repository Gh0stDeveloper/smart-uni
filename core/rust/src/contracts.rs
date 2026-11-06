//! Contratos v1; actor_ref es dato no confiable y no confiere autorización.
use crate::{domain::normalize_email, CONTRACT_VERSION};
use chrono::DateTime;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{error::Error, fmt};

pub const MAX_OPERATION_BYTES: usize = 1024 * 1024;
pub const OPERATIONS: &[&str] = &[
    "notes.create",
    "notes.update",
    "notes.delete",
    "tasks.create",
    "tasks.toggle",
    "events.create",
    "friends.add",
    "materials.import",
    "materials.delete",
    "profile.update",
];
pub const ERROR_CODES: &[&str] = &[
    "VALIDATION_ERROR",
    "UNAUTHENTICATED",
    "FORBIDDEN",
    "NOT_FOUND",
    "CONFLICT",
    "UNSUPPORTED_VERSION",
    "DATA_CORRUPT",
];

#[derive(Debug, PartialEq, Eq)]
pub enum ContractError {
    InvalidJson,
    TooLarge,
    UnsupportedVersion,
    InvalidOperation,
    InvalidIdentifier,
    InvalidActorReference,
    InvalidTimestamp,
    InvalidPayload,
}
impl ContractError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "UNSUPPORTED_VERSION",
            Self::InvalidJson => "DATA_CORRUPT",
            _ => "VALIDATION_ERROR",
        }
    }
}
impl fmt::Display for ContractError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{self:?}")
    }
}
impl Error for ContractError {}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperationEnvelope {
    pub schema_version: String,
    pub operation: String,
    pub operation_id: String,
    pub actor_ref: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub base_revision: Option<u64>,
    pub occurred_at: String,
    pub payload: Value,
}
pub fn is_lowercase_hex_128(s: &str) -> bool {
    s.len() == 32
        && s.bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
pub fn parse_operation(bytes: &[u8]) -> Result<OperationEnvelope, ContractError> {
    if bytes.len() > MAX_OPERATION_BYTES {
        return Err(ContractError::TooLarge);
    }
    let raw: Value = serde_json::from_slice(bytes).map_err(|_| ContractError::InvalidJson)?;
    if raw.get("entity_id").is_some_and(Value::is_null)
        || raw.get("base_revision").is_some_and(Value::is_null)
    {
        return Err(ContractError::InvalidJson);
    }
    let e: OperationEnvelope =
        serde_json::from_value(raw).map_err(|_| ContractError::InvalidJson)?;
    if e.schema_version != CONTRACT_VERSION {
        return Err(ContractError::UnsupportedVersion);
    }
    if !OPERATIONS.contains(&e.operation.as_str()) {
        return Err(ContractError::InvalidOperation);
    }
    if !is_lowercase_hex_128(&e.operation_id)
        || e.entity_id
            .as_ref()
            .is_some_and(|id| !is_lowercase_hex_128(id))
    {
        return Err(ContractError::InvalidIdentifier);
    }
    let normalized =
        normalize_email(&e.actor_ref).map_err(|_| ContractError::InvalidActorReference)?;
    if normalized != e.actor_ref {
        return Err(ContractError::InvalidActorReference);
    }
    if DateTime::parse_from_rfc3339(&e.occurred_at).is_err() {
        return Err(ContractError::InvalidTimestamp);
    }
    if !e.payload.is_object() {
        return Err(ContractError::InvalidPayload);
    }
    Ok(e)
}
#[cfg(test)]
mod tests {
    use super::*;
    const VALID: &str = r#"{"schema_version":"1.0.0","operation":"notes.create","operation_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","actor_ref":"student@example.edu","occurred_at":"2026-11-06T04:00:00Z","payload":{"title":"demo"}}"#;
    #[test]
    fn valid_roundtrip() {
        let op = parse_operation(VALID.as_bytes()).unwrap();
        assert_eq!(op.operation, "notes.create");
        assert!(parse_operation(&serde_json::to_vec(&op).unwrap()).is_ok());
    }
    #[test]
    fn reject_version() {
        assert_eq!(
            parse_operation(VALID.replace("1.0.0", "9.0.0").as_bytes()).unwrap_err(),
            ContractError::UnsupportedVersion
        );
    }
    #[test]
    fn reject_actor() {
        assert_eq!(
            parse_operation(
                VALID
                    .replace("student@example.edu", "STUDENT@EXAMPLE.EDU")
                    .as_bytes()
            )
            .unwrap_err(),
            ContractError::InvalidActorReference
        );
    }
    #[test]
    fn reject_fields() {
        assert_eq!(
            parse_operation(VALID.replace("notes.create", "user.delete").as_bytes()).unwrap_err(),
            ContractError::InvalidOperation
        );
        assert_eq!(
            parse_operation(
                VALID
                    .replace(r#""payload":{"title":"demo"}"#, r#""payload":{},"extra":0"#)
                    .as_bytes()
            )
            .unwrap_err(),
            ContractError::InvalidJson
        );
        assert_eq!(
            parse_operation(
                VALID
                    .replace(
                        r#""payload":{"title":"demo"}"#,
                        r#""payload":{},"entity_id":null"#
                    )
                    .as_bytes()
            )
            .unwrap_err(),
            ContractError::InvalidJson
        );
    }
    #[test]
    fn reject_ids_date_and_payload() {
        assert_eq!(
            parse_operation(
                VALID
                    .replace("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "invalid")
                    .as_bytes()
            )
            .unwrap_err(),
            ContractError::InvalidIdentifier
        );
        assert_eq!(
            parse_operation(VALID.replace("2026-11-06T04:00:00Z", "bad").as_bytes()).unwrap_err(),
            ContractError::InvalidTimestamp
        );
        assert_eq!(
            parse_operation(
                VALID
                    .replace(r#""payload":{"title":"demo"}"#, r#""payload":"x""#)
                    .as_bytes()
            )
            .unwrap_err(),
            ContractError::InvalidPayload
        );
    }
    #[test]
    fn guard_size_and_codes() {
        assert_eq!(
            parse_operation(&vec![0u8; MAX_OPERATION_BYTES + 1]).unwrap_err(),
            ContractError::TooLarge
        );
        assert_eq!(
            ContractError::UnsupportedVersion.code(),
            "UNSUPPORTED_VERSION"
        );
        assert_eq!(OPERATIONS.len(), 10);
        assert_eq!(ERROR_CODES.len(), 7);
    }
}

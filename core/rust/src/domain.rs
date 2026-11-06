//! Reglas puras de dominio; el email local NO autentica a nadie.
use std::{error::Error, fmt};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DomainError {
    InvalidEmail,
    InvalidName,
    InvalidCareer,
    InvalidPassword,
}
impl fmt::Display for DomainError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{self:?}")
    }
}
impl Error for DomainError {}

pub fn normalize_email(input: &str) -> Result<String, DomainError> {
    let value = input.trim();
    if !value.is_ascii() || value.len() > 254 {
        return Err(DomainError::InvalidEmail);
    }
    let (local, domain) = value.split_once('@').ok_or(DomainError::InvalidEmail)?;
    if local.is_empty()
        || !local.bytes().all(|b| b.is_ascii_alphanumeric() || b"._%+-".contains(&b))
        || domain.contains('@')
        || !domain.bytes().all(|b| b.is_ascii_alphanumeric() || b".-".contains(&b))
    {
        return Err(DomainError::InvalidEmail);
    }
    let (before_dot, tld) = domain.rsplit_once('.').ok_or(DomainError::InvalidEmail)?;
    if before_dot.is_empty() || tld.len() < 2 || !tld.bytes().all(|b| b.is_ascii_alphabetic()) {
        return Err(DomainError::InvalidEmail);
    }
    Ok(value.to_ascii_lowercase())
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StudentInput {
    pub name: String,
    pub email: String,
    pub career: String,
}
pub fn validate_student(
    name: &str,
    email: &str,
    career: &str,
    password: &str,
) -> Result<StudentInput, DomainError> {
    let email = normalize_email(email)?;
    let name = name.trim();
    let career = career.trim();
    if name.chars().count() < 3 {
        return Err(DomainError::InvalidName);
    }
    if career.chars().count() < 3 {
        return Err(DomainError::InvalidCareer);
    }
    if password.chars().count() < 8 {
        return Err(DomainError::InvalidPassword);
    }
    Ok(StudentInput { name: name.into(), email, career: career.into() })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn normalize() {
        assert_eq!(normalize_email("  MARIA+1@UNI.EDU  ").unwrap(), "maria+1@uni.edu");
    }
    #[test]
    fn invalid_email() {
        for x in ["sin-arroba", "a@b", "a@@uni.edu", "a@uni.c3", "a@uni.édu"] {
            assert!(normalize_email(x).is_err(), "{x}");
        }
    }
    #[test]
    fn student() {
        let user = validate_student(" María Pérez ", "MARIA@UNI.EDU", "Ingeniería", "ClaveSegura123").unwrap();
        assert_eq!((user.name.as_str(), user.email.as_str()), ("María Pérez", "maria@uni.edu"));
        assert_eq!(user.career, "Ingeniería");
        assert_eq!(
            validate_student("A", "a@uni.edu", "Ingeniería", "ClaveSegura123").unwrap_err(),
            DomainError::InvalidName
        );
        assert_eq!(
            validate_student("Alumna", "a@uni.edu", "Ingeniería", "123").unwrap_err(),
            DomainError::InvalidPassword
        );
    }
}

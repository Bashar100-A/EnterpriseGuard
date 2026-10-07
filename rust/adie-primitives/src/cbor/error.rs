//! ADIE CBOR error codes.
//!
//! Normative source: spec/WIRE-FORMAT-0.2.md §9.
//! 14 distinct codes. Adding a code requires a spec version bump (I34).

use core::fmt;

/// Every rejection emitted by the ADIE CBOR profile layer.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CborError {
    /// CBOR parse failure (ciborium could not decode the bytes).
    Malformed { detail: String },
    /// Bytes remain after the top-level CBOR data item.
    Trailing { extra: usize },
    /// Indefinite-length string, array, or map encountered.
    Indefinite,
    /// Floating-point value encountered (major type 7, additional 25/26/27).
    Float,
    /// CBOR tag encountered (major type 6).
    Tag { tag: u64 },
    /// Duplicate map key encountered during structural walk.
    DuplicateKey,
    /// Integer encoded in a non-shortest form.
    NonCanonicalInt,
    /// Map keys not in RFC 8949 deterministic order.
    NonCanonicalMap,
    /// Text string is not valid UTF-8 (surfaces from ciborium).
    InvalidUtf8,
    /// A field has the wrong type (per WIRE-FORMAT-0.2 §3).
    TypeMismatch { field: &'static str, expected: &'static str },
    /// A required field is missing.
    MissingField { field: &'static str },
    /// A top-level or critical-context field is not in the registry.
    UnknownCritical { label: u64 },
    /// dcp_version is not exactly "2.1".
    Version { got: String },
    /// Interpretation requires external state not present in the certificate.
    Ambiguous { field: &'static str },
}

impl CborError {
    /// Stable identifier, matching WIRE-FORMAT-0.2 §9.
    pub fn code(&self) -> &'static str {
        match self {
            CborError::Malformed { .. }        => "E_WIRE_MALFORMED",
            CborError::Trailing { .. }         => "E_WIRE_TRAILING",
            CborError::Indefinite              => "E_WIRE_INDEFINITE",
            CborError::Float                   => "E_WIRE_FLOAT",
            CborError::Tag { .. }              => "E_WIRE_TAG",
            CborError::DuplicateKey            => "E_WIRE_DUP_KEY",
            CborError::NonCanonicalInt         => "E_WIRE_NONCANONICAL_INT",
            CborError::NonCanonicalMap         => "E_WIRE_NONCANONICAL_MAP",
            CborError::InvalidUtf8             => "E_WIRE_INVALID_UTF8",
            CborError::TypeMismatch { .. }     => "E_WIRE_TYPE_MISMATCH",
            CborError::MissingField { .. }     => "E_WIRE_MISSING_FIELD",
            CborError::UnknownCritical { .. }  => "E_WIRE_UNKNOWN_CRITICAL",
            CborError::Version { .. }          => "E_WIRE_VERSION",
            CborError::Ambiguous { .. }        => "E_WIRE_AMBIGUOUS",
        }
    }
}

impl fmt::Display for CborError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CborError::Malformed { detail } =>
                write!(f, "{}: {}", self.code(), detail),
            CborError::Trailing { extra } =>
                write!(f, "{}: {} byte(s) after top-level item", self.code(), extra),
            CborError::Indefinite =>
                write!(f, "{}: indefinite-length item", self.code()),
            CborError::Float =>
                write!(f, "{}: floating-point value", self.code()),
            CborError::Tag { tag } =>
                write!(f, "{}: tag {}", self.code(), tag),
            CborError::DuplicateKey =>
                write!(f, "{}: duplicate map key", self.code()),
            CborError::NonCanonicalInt =>
                write!(f, "{}: integer not in shortest form", self.code()),
            CborError::NonCanonicalMap =>
                write!(f, "{}: map keys not in deterministic order", self.code()),
            CborError::InvalidUtf8 =>
                write!(f, "{}: text not valid UTF-8", self.code()),
            CborError::TypeMismatch { field, expected } =>
                write!(f, "{}: field {:?} must be {}", self.code(), field, expected),
            CborError::MissingField { field } =>
                write!(f, "{}: missing field {:?}", self.code(), field),
            CborError::UnknownCritical { label } =>
                write!(f, "{}: unknown critical label {}", self.code(), label),
            CborError::Version { got } =>
                write!(f, "{}: dcp_version must be \"2.1\", got {:?}", self.code(), got),
            CborError::Ambiguous { field } =>
                write!(f, "{}: field {:?} requires external state", self.code(), field),
        }
    }
}

impl std::error::Error for CborError {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn codes_are_stable() {
        // Every variant maps to its normative code from WIRE-FORMAT-0.2 §9.
        assert_eq!(CborError::Malformed { detail: String::new() }.code(), "E_WIRE_MALFORMED");
        assert_eq!(CborError::Trailing { extra: 1 }.code(), "E_WIRE_TRAILING");
        assert_eq!(CborError::Indefinite.code(), "E_WIRE_INDEFINITE");
        assert_eq!(CborError::Float.code(), "E_WIRE_FLOAT");
        assert_eq!(CborError::Tag { tag: 1 }.code(), "E_WIRE_TAG");
        assert_eq!(CborError::DuplicateKey.code(), "E_WIRE_DUP_KEY");
        assert_eq!(CborError::NonCanonicalInt.code(), "E_WIRE_NONCANONICAL_INT");
        assert_eq!(CborError::NonCanonicalMap.code(), "E_WIRE_NONCANONICAL_MAP");
        assert_eq!(CborError::InvalidUtf8.code(), "E_WIRE_INVALID_UTF8");
        assert_eq!(CborError::TypeMismatch { field: "x", expected: "y" }.code(), "E_WIRE_TYPE_MISMATCH");
        assert_eq!(CborError::MissingField { field: "x" }.code(), "E_WIRE_MISSING_FIELD");
        assert_eq!(CborError::UnknownCritical { label: 99 }.code(), "E_WIRE_UNKNOWN_CRITICAL");
        assert_eq!(CborError::Version { got: "2.0".into() }.code(), "E_WIRE_VERSION");
        assert_eq!(CborError::Ambiguous { field: "x" }.code(), "E_WIRE_AMBIGUOUS");
    }

    #[test]
    fn display_includes_code() {
        let e = CborError::Trailing { extra: 3 };
        let s = format!("{}", e);
        assert!(s.starts_with("E_WIRE_TRAILING"));
        assert!(s.contains("3"));
    }

    #[test]
    fn display_missing_field_shows_name() {
        let e = CborError::MissingField { field: "binding" };
        let s = format!("{}", e);
        assert!(s.contains("E_WIRE_MISSING_FIELD"));
        assert!(s.contains("binding"));
    }

    #[test]
    fn display_version_shows_value() {
        let e = CborError::Version { got: "9.9".into() };
        let s = format!("{}", e);
        assert!(s.contains("E_WIRE_VERSION"));
        assert!(s.contains("9.9"));
    }

    #[test]
    fn equality_holds_for_same_variant() {
        assert_eq!(CborError::Float, CborError::Float);
        assert_eq!(CborError::Tag { tag: 5 }, CborError::Tag { tag: 5 });
        assert_ne!(CborError::Tag { tag: 5 }, CborError::Tag { tag: 6 });
    }
}

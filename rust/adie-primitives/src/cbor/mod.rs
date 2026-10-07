//! ADIE CBOR profile (Phase 3, Gate 1, 3A.2).
//!
//! Layered over ciborium (codec primitive) per CBOR-LIB-EVAL-001.
//! The ADIE profile enforces WIRE-FORMAT-0.2 §7-§9.
//!
//! Module layout (filled incrementally in D.1..D.6):
//!   error    - rejection codes (14, normative)
//!   value    - AdieValue (profile types only)
//!   profile  - validate() authority
//!   encoder  - canonical serializer
//!   decoder  - parser + strict validation

pub mod error;
pub mod value;
pub mod profile;
pub mod rawcheck;
pub mod encoder;
pub mod decoder;

pub use error::CborError;
pub use value::AdieValue;
pub use encoder::encode;
pub use decoder::decode;

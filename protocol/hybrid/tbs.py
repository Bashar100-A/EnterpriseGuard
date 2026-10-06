"""ADIE hybrid signing — TBS (To-Be-Signed) builder.

spec/HYBRID-CRYPTO-0.1.md §5:
    TBS = "ADIE-SIG-V2\\0" || JCS(certificate_without_signatures)

The domain tag is exactly 12 bytes:
    41 44 49 45 2D 53 49 47 2D 56 32 00
    A  D  I  E  -  S  I  G  -  V  2  \\0
"""
from protocol.core.jcs import canonical_bytes


# Exact 12-byte domain tag. Do not extend or shorten.
DOMAIN_TAG = b"ADIE-SIG-V2\x00"

assert len(DOMAIN_TAG) == 12, "domain tag must be 12 bytes"


def build_tbs(cert_without_signatures: dict) -> bytes:
    """Build the ADIE v2 To-Be-Signed byte sequence.

    Args:
        cert_without_signatures: a certificate dict where the
            signatures (DCP 2.1) or signature (DCP 2.0) field has
            already been removed (not set to null).

    Returns:
        DOMAIN_TAG || JCS(cert_without_signatures)
    """
    if not isinstance(cert_without_signatures, dict):
        raise TypeError("certificate must be a dict")

    if "signatures" in cert_without_signatures:
        raise ValueError(
            "cert has 'signatures' field; remove it before calling build_tbs")
    if "signature" in cert_without_signatures:
        raise ValueError(
            "cert has 'signature' field; remove it before calling build_tbs")

    body = canonical_bytes(cert_without_signatures)
    return DOMAIN_TAG + body


__all__ = ["DOMAIN_TAG", "build_tbs"]

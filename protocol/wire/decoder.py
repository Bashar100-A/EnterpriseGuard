"""ADIE strict CBOR decoder (Phase 3, Gate 1, 3A.3).

Mirror of rust/adie-primitives/src/cbor/decoder.rs.

Normative source: WIRE-FORMAT-0.2 §7, §8, §9.

Pipeline (in order):
  1. rawcheck.scan_top_level         -- byte-level gate
  2. cbor2.loads(hardened flags)     -- parse to Python object
  3. profile.validate                -- profile authority
  4. encoder.encode                  -- canonical re-encode
  5. bytewise comparison             -- canonicality of input

Each layer catches a distinct class of violation:
  - rawcheck:  trailing bytes, indefinite lengths, floats, tags,
               non-shortest integer and length encodings (AUTHORITATIVE)
  - cbor2:     parse errors, plus defense-in-depth rejects
               (allow_duplicate_keys, allow_indefinite, max_depth,
                tag_hook)
  - profile:   integer keys only, sorted, deduplicated, valid types
  - encoder:   re-emits canonical form
  - comparison: catches unsorted map keys

The decoder is NOT the sole authority. rawcheck, profile, and the
encoder each enforce a slice of WIRE-FORMAT-0.2.

DEFECT-021: cbor2's tag_hook does not intercept built-in semantic
tags (0 = date string, 1 = epoch timestamp, 2 = bignum, 3 = neg
bignum). Therefore rawcheck runs first and rejects any major type 6
on raw bytes. tag_hook is defense-in-depth only.
"""
from __future__ import annotations

import cbor2

from protocol.wire import rawcheck
from protocol.wire.encoder import encode as _encode
from protocol.wire.error import CborError, Malformed, NonCanonicalMap
from protocol.wire.profile import validate as _validate_profile
from protocol.wire.value import AdieValue

MAX_DEPTH = 32


class _TagRejected(Exception):
    """Sentinel raised from tag_hook. Converted to Malformed."""


def _raise_on_tag(tag, value):  # noqa: ARG001
    """Defense-in-depth: reject any tag cbor2 tries to interpret."""
    raise _TagRejected(f"tag {tag}")


def decode(data: bytes) -> AdieValue:
    """Decode CBOR bytes into an AdieValue.

    Rejects every non-canonical, malformed, or out-of-profile input
    with a specific error code (WIRE-FORMAT-0.2 §9).
    """
    if not isinstance(data, (bytes, bytearray)):
        raise Malformed("input must be bytes")
    data = bytes(data)

    # 1. Raw-byte structural validation. AUTHORITATIVE for tags,
    #    indefinite lengths, floats, non-shortest encodings, and
    #    trailing bytes.
    rawcheck.scan_top_level(data)

    # 2. Parse with cbor2, hardened explicitly. Every flag is
    #    mandatory (Commander order §3-§5).
    try:
        obj = cbor2.loads(
            data,
            allow_indefinite=False,
            allow_duplicate_keys=False,
            max_depth=MAX_DEPTH,
            tag_hook=_raise_on_tag,
        )
    except _TagRejected as e:
        # Defense-in-depth surfaced a tag that rawcheck should have
        # caught. Reject as malformed since we cannot recover the
        # original tag number from cbor2's exception text reliably.
        raise Malformed(f"tag rejected at cbor2 layer: {e}")
    except cbor2.CBORDecodeError as e:
        # cbor2 6.1.5 raises CBORDecodeError for allow_duplicate_keys
        # and allow_indefinite violations. Match on the message.
        msg = str(e).lower()
        if "duplicate" in msg:
            from protocol.wire.error import DuplicateKey
            raise DuplicateKey()
        if "indefinite" in msg:
            from protocol.wire.error import Indefinite
            raise Indefinite()
        raise Malformed(f"cbor2 parse: {type(e).__name__}: {e}")
    except ValueError as e:
        # Older cbor2 or other library paths.
        msg = str(e).lower()
        if "duplicate" in msg:
            from protocol.wire.error import DuplicateKey
            raise DuplicateKey()
        if "indefinite" in msg:
            from protocol.wire.error import Indefinite
            raise Indefinite()
        raise Malformed(f"cbor2 decode: {e}")

    # 3. Profile validation. Returns AdieValue with maps sorted and
    #    duplicate-free; rejects forbidden types and unknown variants.
    av = _validate_profile(obj)

    # 4. Canonical re-encode.
    re_encoded = _encode(av)

    # 5. Bytewise comparison. After rawcheck (shortest encodings) and
    #    profile (sorted maps), the only possible divergence is an
    #    unsorted map in the input. That is exactly what
    #    E_WIRE_NONCANONICAL_MAP identifies.
    if re_encoded != data:
        raise NonCanonicalMap()

    return av


__all__ = ["decode", "MAX_DEPTH"]

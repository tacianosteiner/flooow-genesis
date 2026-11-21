"""Fixed S03OBSE2 decoder and independent PAIR constraint reconstruction.

These checks do not authenticate a channel, qualify/accept a source, or admit
an artifact. Expectations must come from the existing independently governed
source/authority boundary, never from the candidate record being checked.
No ledger, key issuer, callback provider, SQL, network or production bridge.
"""
import hashlib
import hmac
import struct
import unicodedata

MAX_FRAME = 1048576
MAX_ROWS = 64
CONSUMER = b"S03:DESIGN/AUTHENTICATED_SELF_IDENTITY"


class InvalidEvidence(ValueError):
    pass


class Cursor:
    def __init__(self, body):
        self.body = body
        self.offset = 0

    def take(self, size):
        if size < 0 or size > len(self.body) - self.offset:
            raise InvalidEvidence("TRUNCATED_OR_OVERFLOW")
        result = self.body[self.offset:self.offset + size]
        self.offset += size
        return result

    def u32(self):
        return struct.unpack(">I", self.take(4))[0]

    def u64(self):
        return struct.unpack(">Q", self.take(8))[0]

    def flag(self):
        value = self.u32()
        if value not in (0, 1):
            raise InvalidEvidence("INVALID_PRESENCE_TAG")
        return value == 1

    def ref(self):
        kind, size = self.u32(), self.u32()
        if not kind or not 1 <= size <= 96:
            raise InvalidEvidence("INVALID_TYPED_REFERENCE")
        value = self.take(size)
        if not any(value):
            raise InvalidEvidence("EMPTY_TYPED_REFERENCE")
        return kind, value

    def name(self):
        size = self.u32()
        if not 1 <= size < 64:
            raise InvalidEvidence("INVALID_NAME_SIZE")
        raw = self.take(size)
        if any(byte < 32 or byte == 127 for byte in raw):
            raise InvalidEvidence("INVALID_NAME_CONTROL")
        try:
            value = raw.decode("utf-8", "strict")
        except UnicodeError as error:
            raise InvalidEvidence("INVALID_UTF8") from error
        if unicodedata.normalize("NFC", value) != value:
            raise InvalidEvidence("NONCANONICAL_NAME")
        return raw

    def target(self):
        references = tuple(self.ref() for _ in range(7))
        generation, server_start, backend_start = self.u64(), self.u64(), self.u64()
        identifiers = tuple(self.u32() for _ in range(3))
        if not generation or not all(identifiers):
            raise InvalidEvidence("MISSING_TARGET_IDENTITY")
        if server_start in (1 << 63, (1 << 63) - 1) or backend_start in (1 << 63, (1 << 63) - 1):
            raise InvalidEvidence("INFINITE_PG_TIMESTAMP")
        return references, generation, server_start, backend_start, identifiers, self.name()

    def source(self):
        refs = tuple(self.ref() for _ in range(4))
        digest = self.take(32)
        if not any(digest):
            raise InvalidEvidence("MISSING_SOURCE_INTEGRITY_BINDING")
        return refs, digest


def decode_receipt(frame):
    if type(frame) is not bytes or not 64 <= len(frame) <= MAX_FRAME:
        raise InvalidEvidence("INVALID_FRAME_BOUND")
    if not hmac.compare_digest(hashlib.sha256(frame[:-32]).digest(), frame[-32:]):
        raise InvalidEvidence("FRAME_INTEGRITY_FAILURE")
    reader = Cursor(frame[:-32])
    if reader.take(8) != b"S03OBSE2" or reader.u32() != 2:
        raise InvalidEvidence("UNSUPPORTED_PRIVATE_FORMAT")
    role, output_kind, status, diagnostics = reader.u32(), reader.u32(), reader.u32(), reader.u64()
    if role not in (1, 2) or output_kind != 1 or status > 9:
        raise InvalidEvidence("INVALID_ROLE_OR_PROMOTION")
    vector = tuple(reader.u32() for _ in range(9))
    if any(value not in (1, 2, 3) for value in vector):
        raise InvalidEvidence("INVALID_BINDING_VECTOR")
    if reader.take(len(CONSUMER)) != CONSUMER:
        raise InvalidEvidence("CONSUMER_SUBSTITUTION")
    target = reader.target()
    observer = tuple(reader.ref() for _ in range(5))
    origin = reader.ref()
    # policy/challenge/boot/timens/barrier/acquisition/snapshot/custody/authentication
    domain = tuple(reader.ref() for _ in range(9))
    observed = reader.u64(), reader.u64()
    root_interval = reader.u64(), reader.u64()
    lease = reader.u64(), reader.u64(), reader.u64(), reader.u64()
    original = tuple(reader.u64() for _ in range(3)) if reader.flag() else None
    sources = []
    for _ in range(8):
        expected = reader.source()
        state, presented = None, None
        if reader.flag():
            state = reader.u32()
            if state not in range(1, 7):
                raise InvalidEvidence("INVALID_SOURCE_STATE")
            if reader.flag():
                if state != 1:
                    raise InvalidEvidence("UNAVAILABLE_SOURCE_PAYLOAD")
                presented = reader.source()
        sources.append((expected, state, presented))
    actual, population, coverage, rows = None, None, None, []
    if reader.flag():
        actual, population, coverage, count = reader.target(), reader.ref(), reader.u32(), reader.u32()
        if count > MAX_ROWS:
            raise InvalidEvidence("POPULATION_BOUND_EXCEEDED")
        for _ in range(count):
            ordinal = reader.u32()
            bridge = reader.target() if reader.flag() else None
            public_ids = tuple(reader.u32() for _ in range(3))
            public_name = reader.name() if reader.flag() else None
            public_ref = reader.ref() if reader.flag() else None
            native = None
            if reader.flag():
                native = (reader.ref() if reader.flag() else None, reader.u32(), reader.u32())
            backend_type = None
            if reader.flag():
                backend_type = reader.name() if reader.flag() else None
            rows.append((ordinal, bridge, public_ids, public_name, public_ref, native, backend_type))
    if reader.offset != len(reader.body):
        raise InvalidEvidence("TRAILING_OR_AMBIGUOUS_FRAME")
    return {
        "role": role, "status": status, "diagnostics": diagnostics, "binding_vector": vector,
        "target": target, "observer": observer, "origin": origin, "domain": domain,
        "observed": observed, "root_interval": root_interval, "lease": lease, "original": original,
        "sources": tuple(sources), "actual": actual, "population": population, "coverage": coverage,
        "rows": tuple(rows), "digest": frame[-32:],
    }


def reconstruct_pair_constraints(expected_by_role, frames, use_boottime_us):
    """Reconstruct fixed PAIR constraints against independently held expectations.

    A matching result remains EVIDENCE_ONLY. Neither this function nor a hash
    establishes actual channel origin, root/source acceptance, barrier validity,
    qualification, admission or economic truth. The governed acquisition
    membrane must independently establish those before using these checks.
    """
    if type(use_boottime_us) is not int or use_boottime_us <= 0:
        raise InvalidEvidence("INDEPENDENT_USE_TIME_REQUIRED")
    # Reject iterators and oversized collections before any decoding/allocation.
    # An untrusted generator must never control the work performed here.
    if type(frames) not in (tuple, list) or len(frames) != 2:
        raise InvalidEvidence("BOUNDED_PAIR_COLLECTION_REQUIRED")
    receipts = tuple(decode_receipt(frame) for frame in frames)
    if len(receipts) != 2 or {receipt["role"] for receipt in receipts} != {1, 2}:
        raise InvalidEvidence("BOTH_DISTINCT_ROLES_REQUIRED")
    by_role = {receipt["role"]: receipt for receipt in receipts}
    reasons = []
    intervals = []
    for role in (1, 2):
        receipt, expected = by_role[role], expected_by_role[role]
        for field in ("target", "observer", "origin", "domain", "lease", "root_interval"):
            if receipt[field] != expected[field]:
                reasons.append(f"ROLE_{role}_{field.upper()}_BINDING_MISMATCH")
        if tuple(source[0] for source in receipt["sources"]) != expected["sources"]:
            reasons.append(f"ROLE_{role}_EXPECTED_SOURCE_BINDING_MISMATCH")
        if any(state != 1 or presented != claimed for claimed, state, presented in receipt["sources"]):
            reasons.append(f"ROLE_{role}_SOURCE_UNAVAILABLE_OR_INTEGRITY_FAILURE")
        if receipt["status"] != 0 or receipt["diagnostics"] or receipt["binding_vector"] != (1,) * 9:
            reasons.append(f"ROLE_{role}_NONPOSITIVE_EVIDENCE")
        if receipt["original"] is None or receipt["actual"] != expected["target"]:
            reasons.append(f"ROLE_{role}_ORIGINAL_SUBJECT_NOT_ESTABLISHED")
        if receipt["population"] != expected["population"] or receipt["coverage"] != 1:
            reasons.append(f"ROLE_{role}_COVERAGE_NOT_ESTABLISHED")
        start, finish = receipt["observed"]
        lower, upper, max_age, root_barrier = expected["lease"]
        originals = [receipt["root_interval"]]
        if receipt["original"] is not None:
            original_start, original_finish, original_barrier = receipt["original"]
            originals.append((original_start, original_finish))
            if use_boottime_us > original_barrier:
                reasons.append(f"ROLE_{role}_SOURCE_BARRIER_EXPIRED")
        for source_start, source_finish in originals:
            if not (lower <= source_start <= source_finish <= start <= finish <= use_boottime_us < upper):
                reasons.append(f"ROLE_{role}_ORIGINAL_INTERVAL_NOT_COVERED")
            if use_boottime_us - source_start > max_age:
                reasons.append(f"ROLE_{role}_ORIGINAL_TOO_OLD")
        if max_age <= 0 or use_boottime_us > root_barrier:
            reasons.append(f"ROLE_{role}_ROOT_BARRIER_OR_POLICY_UNAVAILABLE")
        intervals.extend(originals + [(start, finish)])
        expected_members = expected["members"] if role == 2 else (expected["target"],)
        observed_members = tuple(row[1] for row in receipt["rows"])
        if len(observed_members) != len(expected_members) or set(observed_members) != set(expected_members):
            reasons.append(f"ROLE_{role}_MEMBER_SET_MISMATCH")
        if len(set(row[0] for row in receipt["rows"])) != len(receipt["rows"]):
            reasons.append(f"ROLE_{role}_DUPLICATE_SOURCE_ORDINAL")
        if set(row[0] for row in receipt["rows"]) != set(range(len(receipt["rows"]))):
            reasons.append(f"ROLE_{role}_SOURCE_ORDINAL_OUT_OF_RANGE")
        for _, bridge, public_ids, public_name, public_ref, native, backend_type in receipt["rows"]:
            if bridge is None or native is None or native[0] is None or public_ref is None:
                reasons.append(f"ROLE_{role}_MEMBER_NOT_ESTABLISHED")
                continue
            if public_ids != bridge[4] or public_name != bridge[5] or native[0] != bridge[0][2]:
                reasons.append(f"ROLE_{role}_MEMBER_FACT_CONTRADICTION")
            if native[1:] != (1, 1) or backend_type != b"client backend":
                reasons.append(f"ROLE_{role}_MEMBER_LIVENESS_OR_TYPE_UNAVAILABLE")
    health, census = by_role[1], by_role[2]
    # Full principal, retained birth, session and channel identities; never PID-only.
    for index in (0, 1, 3, 4):
        if health["observer"][index] == census["observer"][index]:
            reasons.append("OBSERVER_ROLE_ORIGIN_COLLAPSE")
    for receipt in receipts:
        target_refs = receipt["target"][0]
        if receipt["observer"][0] == target_refs[6] or receipt["observer"][1] == target_refs[2] or receipt["observer"][3] == target_refs[3]:
            reasons.append("OBSERVER_IMPERSONATES_TARGET")
    if health["target"] != census["target"] or health["domain"] != census["domain"]:
        reasons.append("PAIR_COMPARISON_DOMAIN_MISMATCH")
    return {
        "kind": "PAIR_S03_PREREQUISITE_EVIDENCE_V1_CONSTRAINT_CHECKS",
        "boundary": "EVIDENCE_ONLY",
        "matching_under_independently_supplied_expectations": not reasons,
        "reasons": tuple(reasons),
        "combined_original_span": (min(start for start, _ in intervals), max(end for _, end in intervals)),
        "source_acceptance": "NOT_ESTABLISHED_BY_THIS_CHECK",
        "actual_channel_origin": "NOT_ESTABLISHED_BY_THIS_CHECK",
        "actual_mutation_barrier_validity": "NOT_ESTABLISHED_BY_THIS_CHECK",
        "qualification_or_admission": "NOT_PERFORMED",
    }

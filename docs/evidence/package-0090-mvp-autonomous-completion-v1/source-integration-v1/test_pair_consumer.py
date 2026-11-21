"""Synthetic private-codec/PAIR tests. No accepted source or authority fixture."""
import copy
import hashlib
import struct
import unittest
from pair_consumer import CONSUMER, InvalidEvidence, decode_receipt, reconstruct_pair_constraints


def ref(value):
    return 1, value.encode("ascii")


TARGET = (tuple(ref(value) for value in ("context", "server", "birth", "session", "registry", "participant", "principal")), 1, 10, 20, (1, 2, 3), b"reader")
DOMAIN = tuple(ref(value) for value in ("policy", "challenge", "boot", "timens", "barrier", "acquisition", "snapshot", "custody", "authentication"))
SOURCES = tuple((tuple(ref(f"source-{i}-{field}") for field in ("id", "authority", "provenance", "acceptance")), hashlib.sha256(str(i).encode()).digest()) for i in range(8))


def expectations(role):
    prefix = "health" if role == 1 else "census"
    return {
        "target": TARGET, "observer": tuple(ref(prefix + "-" + field) for field in ("principal", "birth", "context", "session", "channel")),
        "origin": ref(prefix + "-origin"), "domain": DOMAIN, "lease": (1000, 10000, 9000, 9500),
        "root_interval": (2000, 2010), "sources": SOURCES, "population": ref("population"), "members": (TARGET,),
    }


class Writer:
    def __init__(self): self.value = bytearray()
    def raw(self, value): self.value.extend(value)
    def u32(self, value): self.raw(struct.pack(">I", value))
    def u64(self, value): self.raw(struct.pack(">Q", value))
    def ref(self, value):
        self.u32(value[0]); self.u32(len(value[1])); self.raw(value[1])
    def name(self, value): self.u32(len(value)); self.raw(value)
    def source(self, value):
        for item in value[0]: self.ref(item)
        self.raw(value[1])
    def target(self, value):
        for item in value[0]: self.ref(item)
        for item in value[1:4]: self.u64(item)
        for item in value[4]: self.u32(item)
        self.name(value[5])


def frame(role, expected=None, *, count=1, ordinal=0, original=(2300, 2310, 9500), consumer=CONSUMER):
    expected = expectations(role) if expected is None else expected
    writer = Writer()
    writer.raw(b"S03OBSE2"); writer.u32(2); writer.u32(role); writer.u32(1); writer.u32(0); writer.u64(0)
    for _ in range(9): writer.u32(1)
    writer.raw(consumer); writer.target(expected["target"])
    for item in expected["observer"]: writer.ref(item)
    writer.ref(expected["origin"])
    for item in expected["domain"]: writer.ref(item)
    for item in (2400, 2410) + expected["root_interval"] + expected["lease"]: writer.u64(item)
    writer.u32(1)
    for item in original: writer.u64(item)
    for source in expected["sources"]:
        writer.source(source); writer.u32(1); writer.u32(1); writer.u32(1); writer.source(source)
    writer.u32(1); writer.target(expected["target"]); writer.ref(expected["population"]); writer.u32(1); writer.u32(count)
    writer.u32(ordinal); writer.u32(1); writer.target(expected["target"])
    for item in expected["target"][4]: writer.u32(item)
    writer.u32(1); writer.name(expected["target"][5]); writer.u32(1); writer.ref(ref("public-row"))
    writer.u32(1); writer.u32(1); writer.ref(expected["target"][0][2]); writer.u32(1); writer.u32(1)
    writer.u32(1); writer.u32(1); writer.name(b"client backend")
    body = bytes(writer.value)
    return body + hashlib.sha256(body).digest()


class PairTests(unittest.TestCase):
    def setUp(self): self.expected = {role: expectations(role) for role in (1, 2)}

    def test_unbounded_iterator_rejected_without_iteration(self):
        def hostile():
            raise AssertionError("must never iterate")
            yield b""
        with self.assertRaises(InvalidEvidence):
            reconstruct_pair_constraints(self.expected, hostile(), 2500)

    def test_oversized_collection_rejected_before_decoding(self):
        with self.assertRaisesRegex(InvalidEvidence, "BOUNDED_PAIR"):
            reconstruct_pair_constraints(self.expected, (b"",) * 100, 2500)

    def test_out_of_range_source_ordinal_is_not_positive(self):
        result = reconstruct_pair_constraints(self.expected, (frame(1, ordinal=0xffffffff), frame(2)), 2500)
        self.assertFalse(result["matching_under_independently_supplied_expectations"])
        self.assertIn("ROLE_1_SOURCE_ORDINAL_OUT_OF_RANGE", result["reasons"])

    def test_matching_constraints_remain_evidence_only_not_acceptance(self):
        result = reconstruct_pair_constraints(self.expected, (frame(1), frame(2)), 2500)
        self.assertTrue(result["matching_under_independently_supplied_expectations"])
        self.assertEqual(result["boundary"], "EVIDENCE_ONLY")
        self.assertEqual(result["source_acceptance"], "NOT_ESTABLISHED_BY_THIS_CHECK")
        self.assertEqual(result["actual_channel_origin"], "NOT_ESTABLISHED_BY_THIS_CHECK")

    def test_bit_mutation_cannot_authenticate_by_recomputed_source_claim(self):
        modified = bytearray(frame(1)); modified[60] ^= 1
        with self.assertRaises(InvalidEvidence): decode_receipt(bytes(modified))

    def test_both_roles_required_no_one_observer_fallback(self):
        with self.assertRaises(InvalidEvidence): reconstruct_pair_constraints(self.expected, (frame(1), frame(1)), 2500)

    def test_full_target_identity_not_pid_alone(self):
        other = copy.deepcopy(self.expected[2])
        refs = list(other["target"][0]); refs[2] = ref("reused-pid-new-birth")
        other["target"] = (tuple(refs),) + other["target"][1:]
        result = reconstruct_pair_constraints(self.expected, (frame(1), frame(2, other)), 2500)
        self.assertFalse(result["matching_under_independently_supplied_expectations"])

    def test_distinct_origin_not_merely_role_number(self):
        other = copy.deepcopy(self.expected[2]); other["observer"] = self.expected[1]["observer"]
        expected = {1: self.expected[1], 2: other}
        result = reconstruct_pair_constraints(expected, (frame(1), frame(2, other)), 2500)
        self.assertIn("OBSERVER_ROLE_ORIGIN_COLLAPSE", result["reasons"])

    def test_original_interval_cannot_predate_lease(self):
        result = reconstruct_pair_constraints(self.expected, (frame(1, original=(900, 950, 9500)), frame(2)), 2500)
        self.assertIn("ROLE_1_ORIGINAL_INTERVAL_NOT_COVERED", result["reasons"])

    def test_use_after_expiry_does_not_renew_original_evidence(self):
        result = reconstruct_pair_constraints(self.expected, (frame(1), frame(2)), 10001)
        self.assertFalse(result["matching_under_independently_supplied_expectations"])

    def test_source_expected_and_actual_claims_cannot_replace_independent_binding(self):
        other = copy.deepcopy(self.expected[2]); sources = list(other["sources"])
        refs = list(sources[0][0]); refs[3] = ref("self-approved")
        sources[0] = tuple(refs), sources[0][1]; other["sources"] = tuple(sources)
        result = reconstruct_pair_constraints(self.expected, (frame(1), frame(2, other)), 2500)
        self.assertIn("ROLE_2_EXPECTED_SOURCE_BINDING_MISMATCH", result["reasons"])

    def test_count_limit_checked_before_rows(self):
        with self.assertRaises(InvalidEvidence): decode_receipt(frame(1, count=65))

    def test_consumer_substitution_fails_closed(self):
        with self.assertRaises(InvalidEvidence): decode_receipt(frame(1, consumer=b"X" * len(CONSUMER)))

    def test_truncation_and_trailing_content_fail_closed(self):
        for value in (frame(1)[:50], frame(1)[:-1]):
            with self.assertRaises(InvalidEvidence): decode_receipt(value)
        body = frame(1)[:-32] + b"extra"
        with self.assertRaises(InvalidEvidence): decode_receipt(body + hashlib.sha256(body).digest())


if __name__ == "__main__": unittest.main()

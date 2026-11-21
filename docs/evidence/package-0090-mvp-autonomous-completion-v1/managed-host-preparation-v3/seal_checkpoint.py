"""Immutable continuation checkpoint, not a completion/acceptance seal."""
import hashlib
import json
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[4]
output = root / "docs/evidence/package-0090-mvp-autonomous-completion-v1"
destination = output / "checkpoints" / sys.argv[1]
destination.mkdir(parents=True, exist_ok=False)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
antecedent = next((root / "docs/evidence").glob("*realization-v1-continuation-v1"))
bindings = json.loads((antecedent / "sha256-manifest.json").read_text(encoding="utf-8-sig"))["files"]
failures = [name for name, expected in bindings.items() if sha(root / name) != expected]
assert not failures, failures
checkpoint = {
    "CURRENT_GATE": "Existing HOST-managed immutable policy-proposal custody; actual issuer decision/acceptance still pending",
    "CURRENT_HEAD": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
    "BRANCH": subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip(),
    "FROZEN_BASELINE": "cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb",
    "AUTHORITY": "FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1",
    "DELEGATION": "User explicitly authorized separate independent reviewer context",
    "COMPLETED_OBLIGATIONS": [
        "Antecedent59 files reverified unchanged at this checkpoint",
        "64 exact parsed synthetic native cases;576 deterministic context/source mutations",
        "Temporal/source-read qualification fixes independently reviewed",
        "Private C codec/PAIR interop synthetic;14 PAIR tests;2 independent counterexamples repaired",
        "Kernel immutable export mutation negatives passed",
        "Real NEW disposable Reader SCRAM session: two children exec/confinement before session acquisition; sealed public4 self-row; original intervals and hashes reconstructed",
        "Separate OS principals and socket DAC independently verified in NEW clusters",
        "Both confined children independently polled same retained kernel pidfd live before/after export and stale after own session close; independently reconstructed",
        "Pre-Reader raw boot/timens/PGsystemID/database/Reader flags/server-start measurements; exact int8 and PG2000 wire bits reconstructed independently",
        "Raw expected-bootstrap actually sealed RO before Reader/children, original source/read intervals distinct; independently reconstructed",
        "Existing actual desktop-linux namedpipe/daemon and Windows backend/principal metadata independently corroborated, no roottrust/approval inferred",
        "Immutable precompiled image, no runtimecodebinds/runtimecompile; externalmanager binds real publisher ELF/birth/ns before its own privatebootstrap publication",
        "Separate UID10003 holds UNACCEPTEDpolicyproposal+rawcontext only after externally managed birth gate; receiver verifies SCM_CREDENTIALS+retainedpidfd and ROsealedrecordhash; no activation/approval",
        "Observer-repair-v3 same4fixed Linuxx86_64effects,3SHAimports,64+576regressions,8EIOinjections,4before/afterdeferredcancelcases; independent42guard observations and4EAGAINinjections passed",
        "Independent custody review v2: hostile parent environment and6 additional syscall negatives per child passed",
        "Web lint/build25tests; selected backend unit suite836tests previously passed; full updatedAPI70tests passed;2 real disposable PG persistence classes",
        "HTTP+realPG projection remainsBLOCKED/NOT_ASSEMBLED/nulltotal, authorized-org isolation and completecase/lineage GET immutability verified; product commitb445d260",
        "Disposable migrations001..042 validate/repeat; V043 not executed"
    ],
    "OPEN_OBLIGATIONS": [
        "Actual qualified issuer/bootstrap and source acceptance lineage; current runtime probes are not accepted sources",
        "Full owner/session credential custody, challenge one-use and generation/revocation integration",
        "Independently controlled immutable expected-bootstrap publication; current pre-Reader facts are raw measurements, not accepted manifests",
        "Actual existingHOSTpolicy-custodian delegation and explicit scoped provisioning decision plus distinct qualification/acceptance/activation/revocation; managed custody is not approval",
        "During-write/asynchronous cancellation and fixed-syscall kernel/platform/effect qualification",
        "Actual S02 closed roster and S03 bridge, native birth/auth/custody/barrier exports",
        "Qualify and independently accept both observer/source integrations before four canonical artifact inputs",
        "Frozen33 native and66 threat obligations; canonical350; N1;V2 and remaining gates",
        "Real integrated main/negative E2E and golden path; prior visual CUA attempt blocked by automatic review",
        "Final repository audit, scoped commit and final evidence seal"
    ],
    "TEST_COUNTS": {"web":25,"selected_backend_unit_preceding_run":836,"updated_API_suite":70,"selected_PG_test_classes":2,
                    "PAIR_synthetic_unit":14,"native_synthetic_cases":64,"context_bit_mutations":576,
                    "fixed_syscall_EIO_cases":8,"deferred_cancel_before_after_cases":4,
                    "native_frozen33_proven":0},
    "ATTACK_COUNTS": {"frozen66_proven":0,"classification":"New negative probes do not replace frozen denominators"},
    "COMPLETE_CANONICAL_DECISION_EVALUATORS":"NOT_ESTABLISHED",
    "SOURCE_ACCEPTANCE":"NOT_ESTABLISHED",
    "HISTORICAL_AUTHORITY_GAP":"NOT_ESTABLISHED_UNCHANGED",
    "NEXT_GATE":"Independently review managedv3 policy-proposal custody, then engineer actual existingHOSTpolicy decision and protected acceptance control; keep lease/source acceptanceNOT_ESTABLISHED until all gates truly pass",
    "HARD_STOPS_IF_ANY":[],
    "MVP_FINALIZED":"NO",
    "SEAL_SCOPE":"Continuation only; active work continues; no qualification/acceptance/admission/finalization"
}
(destination / "checkpoint.json").write_text(json.dumps(checkpoint,indent=2)+"\n",encoding="utf-8")
files = {path.relative_to(root).as_posix():sha(path) for path in output.rglob("*")
         if path.is_file() and "checkpoints" not in path.relative_to(output).parts and path.name != "checkpoint.json"}
files[(destination / "checkpoint.json").relative_to(root).as_posix()] = sha(destination / "checkpoint.json")
(destination / "sha256-manifest.json").write_text(json.dumps({"algorithm":"SHA256","scope":"Frozen checkpoint of then-current files; future edits require new checkpoint","files":files},indent=2)+"\n",encoding="utf-8")
(output / "checkpoint.json").write_text(json.dumps(checkpoint,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"checkpoint":str(destination),"files":len(files),"manifest_sha256":sha(destination / "sha256-manifest.json"),"antecedent_verified":len(bindings)}))

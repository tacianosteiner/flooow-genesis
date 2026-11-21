import hashlib
import json
import pathlib
import sys

execution_path = pathlib.Path(sys.argv[1]) if sys.argv[1] else None
result_path = pathlib.Path(sys.argv[2])

review = {
    "schema_version": 1,
    "review_class": "INDEPENDENT_MECHANICAL_REVIEW_ONLY",
    "semantic_source_acceptance": "NOT_ESTABLISHED",
    "qualification_authority": "NOT_ESTABLISHED",
    "execution_record_present": False,
    "execution_exit_zero": False,
    "private_credential_marker": False,
    "custody_marker": False,
    "not_established_marker": False,
    "forbidden_semantic_claims": [],
    "mechanical_result": "NOT_ESTABLISHED",
}

if execution_path and execution_path.exists():
    review["execution_record_present"] = True
    review["execution_record_sha256"] = hashlib.sha256(
        execution_path.read_bytes()
    ).hexdigest()

    data = json.loads(execution_path.read_text(encoding="utf-8-sig"))

    review["execution_exit_zero"] = data.get("exit_code") == 0

    stdout = str(data.get("stdout", ""))

    review["private_credential_marker"] = (
        "PASS PRIVATE_EPHEMERAL_READER_CREDENTIAL_MECHANICS" in stdout
    )

    review["custody_marker"] = (
        "PASS SELF_SESSION_PGSTAT_CUSTODY_PROBE" in stdout
    )

    review["not_established_marker"] = "NOT_ESTABLISHED" in stdout

    forbidden = [
        "SOURCE_ACCEPTANCE=ESTABLISHED",
        "SOURCE_ACCEPTANCE=ACCEPTED",
        "QUALIFICATION=ESTABLISHED",
        "QUALIFICATION=ACCEPTED",
        "POLICY_ACTIVATION=ESTABLISHED",
        "GENERATION=ESTABLISHED",
        "CANONICAL_ADMISSION=ESTABLISHED",
    ]

    review["forbidden_semantic_claims"] = [
        value for value in forbidden if value in stdout
    ]

    if (
        review["execution_exit_zero"]
        and review["private_credential_marker"]
        and review["custody_marker"]
        and review["not_established_marker"]
        and not review["forbidden_semantic_claims"]
    ):
        review["mechanical_result"] = "PASS"

result_path.write_text(
    json.dumps(review, indent=2) + "\n",
    encoding="utf-8"
)

if review["forbidden_semantic_claims"]:
    sys.exit(20)

if review["mechanical_result"] == "PASS":
    sys.exit(0)

sys.exit(10)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
# NON-EXECUTED HANDOFF; STAGE=FC01_NEGATIVE
# This flag is deliberately false. Changing it is not itself governance evidence.
$ExplicitStageAuthorization = $false
if (-not $ExplicitStageAuthorization) { throw "AUTHORIZATION REQUIRED" }
& (Join-Path $PSScriptRoot '01-VERIFY-BASELINE.ps1')
# Preconditions: Approved complete control denominator, fresh isolated fixture per case, null/constraint/rowcount/adversarial cases, evidence and cleanup.
# No command/runner is dynamically accepted: an unreviewed script hash is not authority.
# The current SQL/fixture/native gates remain HOLD.
throw "CONTRACT OR EXECUTION RECIPE INCOMPLETE: FC01_NEGATIVE; DO NOT EXECUTE"

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
# NON-EXECUTED HANDOFF; STAGE=FC01_POSITIVE
# This flag is deliberately false. Changing it is not itself governance evidence.
$ExplicitStageAuthorization = $false
if (-not $ExplicitStageAuthorization) { throw "AUTHORIZATION REQUIRED" }
& (Join-Path $PSScriptRoot '01-VERIFY-BASELINE.ps1')
# Preconditions: All fixture preflight proofs, separately authorized 13-path execution, exact source/binary hashes and isolated synthetic context.
# No command/runner is dynamically accepted: an unreviewed script hash is not authority.
# The current SQL/fixture/native gates remain HOLD.
throw "CONTRACT OR EXECUTION RECIPE INCOMPLETE: FC01_POSITIVE; DO NOT EXECUTE"

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
# NON-EXECUTED HANDOFF; STAGE=NATIVE_HEALTH
# This flag is deliberately false. Changing it is not itself governance evidence.
$ExplicitStageAuthorization = $false
if (-not $ExplicitStageAuthorization) { throw "AUTHORIZATION REQUIRED" }
& (Join-Path $PSScriptRoot '01-VERIFY-BASELINE.ps1')
# Preconditions: Separately reviewed native implementation and independent process anchoring/continuous census/liveness/enforcement witnesses.
# No command/runner is dynamically accepted: an unreviewed script hash is not authority.
# The current SQL/fixture/native gates remain HOLD.
throw "CONTRACT OR EXECUTION RECIPE INCOMPLETE: NATIVE_HEALTH; DO NOT EXECUTE"

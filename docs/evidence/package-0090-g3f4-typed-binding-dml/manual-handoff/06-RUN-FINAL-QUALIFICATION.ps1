$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
# NON-EXECUTED HANDOFF; STAGE=FINAL_DISPOSABLE_QUALIFICATION
# This flag is deliberately false. Changing it is not itself governance evidence.
$ExplicitStageAuthorization = $false
if (-not $ExplicitStageAuthorization) { throw "AUTHORIZATION REQUIRED" }
& (Join-Path $PSScriptRoot '01-VERIFY-BASELINE.ps1')
# Preconditions: Full final immutable-source matrix including dependent FC03/04/05/07, native health, ownership, cleanup and historical integrity. Canonical final runner remains separate.
# No command/runner is dynamically accepted: an unreviewed script hash is not authority.
# The current SQL/fixture/native gates remain HOLD.
throw "CONTRACT OR EXECUTION RECIPE INCOMPLETE: FINAL_DISPOSABLE_QUALIFICATION; DO NOT EXECUTE"

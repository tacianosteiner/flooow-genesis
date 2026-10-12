$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
# NON-EXECUTED HANDOFF; STAGE=FIXTURE_PREFLIGHT
# This flag is deliberately false. Changing it is not itself governance evidence.
$ExplicitStageAuthorization = $false
if (-not $ExplicitStageAuthorization) { throw "AUTHORIZATION REQUIRED" }
& (Join-Path $PSScriptRoot '01-VERIFY-BASELINE.ps1')
# Preconditions: Contract closure and source/catalog/implicit DML/SQL-external fixture completeness, hash-bound disposable fixture, explicit execution scope.
# No command/runner is dynamically accepted: an unreviewed script hash is not authority.
# The current SQL/fixture/native gates remain HOLD.
throw "CONTRACT OR EXECUTION RECIPE INCOMPLETE: FIXTURE_PREFLIGHT; DO NOT EXECUTE"

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
# Read-only collection to console; no network, process signal, cleanup or output-file overwrite.
$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$CaseRoot = Join-Path $RepoRoot 'docs\evidence\package-0090-g3f4-typed-binding-dml'
$branch = (& git -C $RepoRoot branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branch -ne 'checkpoint/package-0090-cloud-handoff') { throw 'BRANCH MISMATCH' }
Write-Output $branch
& git -C $RepoRoot rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'HEAD READ FAILED' }
& git -C $RepoRoot status --short
if ($LASTEXITCODE -ne 0) { throw 'STATUS READ FAILED' }
$paths = @(
    (Join-Path $CaseRoot 'semantic-checkpoint\SEMANTIC-STATUS.json'),
    (Join-Path $CaseRoot 'semantic-checkpoint\WITNESS-DESIGN-REVIEW.json'),
    (Join-Path $CaseRoot 'manual-handoff\FINAL-HANDOFF-STATUS.json')
)
foreach ($path in $paths) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'REQUIRED EVIDENCE MISSING' }
    Get-Content -LiteralPath $path -Raw -Encoding UTF8
    Get-FileHash -LiteralPath $path -Algorithm SHA256
}
Write-Output 'COLLECTION_ONLY; DOES_NOT_ASSERT_ROOM_OPERATIONAL_OR_QUALIFICATION_PASS'

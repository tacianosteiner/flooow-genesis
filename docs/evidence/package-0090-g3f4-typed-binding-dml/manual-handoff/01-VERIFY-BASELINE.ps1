$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$ExpectedBranch = 'checkpoint/package-0090-cloud-handoff'
$InputHead = '406b446d0b00abf1a45d86c7c8baeee640bc9d4d'
$branch = (& git -C $RepoRoot branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branch -ne $ExpectedBranch) { throw 'BASELINE BRANCH MISMATCH' }
$head = (& git -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'LOCAL HEAD READ FAILED' }
$remoteLine = & git -C $RepoRoot ls-remote --exit-code origin ("refs/heads/" + $ExpectedBranch)
if ($LASTEXITCODE -ne 0) { throw 'REMOTE HEAD READ FAILED' }
$remoteHead = ($remoteLine -split '\s+')[0]
if ($head -ne $remoteHead) { throw 'LOCAL REMOTE DIVERGENCE' }
& git -C $RepoRoot merge-base --is-ancestor $InputHead $head
if ($LASTEXITCODE -ne 0) { throw 'INPUT LINEAGE MISMATCH' }
$dirty = @(& git -C $RepoRoot status --porcelain=v1)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw 'WORKTREE MUST BE CLEAN' }
$scope = @(& git -C $RepoRoot diff --name-only $InputHead $head)
if ($LASTEXITCODE -ne 0) { throw 'SCOPE READ FAILED' }
foreach ($name in $scope) {
    if (-not $name.StartsWith('docs/evidence/package-0090-g3f4-typed-binding-dml/', [StringComparison]::Ordinal)) { throw 'OUT OF HANDOFF SCOPE CHANGE' }
}
$manifestPath = Join-Path $PSScriptRoot 'HANDOFF-SHA256.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($entry in $manifest.files.PSObject.Properties) {
    $path = [IO.Path]::GetFullPath((Join-Path $RepoRoot $entry.Name))
    if (-not $path.StartsWith($RepoRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'MANIFEST PATH ESCAPE' }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'MANIFEST FILE MISSING' }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Value) { throw 'MANIFEST HASH MISMATCH' }
}
& git -C $RepoRoot diff --check
if ($LASTEXITCODE -ne 0) { throw 'DIFF CHECK FAILED' }
Write-Output ('BASELINE_VERIFIED HEAD=' + $head)
Write-Output 'CONTRACT_CLOSURE=HOLD; NO EXECUTION AUTHORITY CREATED'

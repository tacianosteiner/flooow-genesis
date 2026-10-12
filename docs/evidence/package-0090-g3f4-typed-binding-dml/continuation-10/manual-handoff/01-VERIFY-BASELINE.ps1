$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
try {
    $ExpectedRepo = 'C:\Users\xmz_r\Downloads\flooow-v042-implementation'
    $RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..'))
    $CwdRoot = [IO.Path]::GetFullPath((Get-Location).ProviderPath)
    if ($RepoRoot -ne $ExpectedRepo -or $CwdRoot -ne $ExpectedRepo) { throw 'EXACT WORKTREE/CWD MISMATCH' }
    $Branch = (& git -C $RepoRoot branch --show-current)
    if ($LASTEXITCODE -ne 0 -or $Branch -ne 'checkpoint/package-0090-cloud-handoff') { throw 'BRANCH MISMATCH' }
    $Head = (& git -C $RepoRoot rev-parse HEAD)
    if ($LASTEXITCODE -ne 0) { throw 'HEAD READ FAILED' }
    $RemoteLine = (& git -C $RepoRoot ls-remote --exit-code origin refs/heads/checkpoint/package-0090-cloud-handoff)
    if ($LASTEXITCODE -ne 0 -or -not $RemoteLine) { throw 'REMOTE READ FAILED' }
    $RemoteHead = ($RemoteLine -split '\s+')[0]
    if ($Head -ne $RemoteHead) { throw 'LOCAL/REMOTE DIVERGENCE' }
    & git -C $RepoRoot merge-base --is-ancestor 2109a564bc8555925ebef3dc0bf391e162a21eba $Head
    if ($LASTEXITCODE -ne 0) { throw 'RESUME LINEAGE MISMATCH' }
    $Dirty = @(& git -C $RepoRoot status --porcelain=v1)
    if ($LASTEXITCODE -ne 0 -or $Dirty.Count -ne 0) { throw 'WORKTREE DIRTY' }
    $Scope = @(& git -C $RepoRoot diff --name-only 2109a564bc8555925ebef3dc0bf391e162a21eba $Head)
    if ($LASTEXITCODE -ne 0) { throw 'SCOPE READ FAILED' }
    foreach ($Name in $Scope) {
        if (-not $Name.StartsWith('docs/evidence/package-0090-g3f4-typed-binding-dml/', [StringComparison]::Ordinal)) { throw 'SCOPE VIOLATION' }
    }
    $Manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'HANDOFF-SHA256.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($Entry in $Manifest.files.PSObject.Properties) {
        $File = [IO.Path]::GetFullPath((Join-Path $RepoRoot $Entry.Name))
        if (-not $File.StartsWith($RepoRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'MANIFEST PATH ESCAPE' }
        if (-not (Test-Path -LiteralPath $File -PathType Leaf)) { throw 'MANIFEST FILE MISSING' }
        $Hash = (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($Hash -ne $Entry.Value) { throw 'MANIFEST HASH MISMATCH' }
    }
    & git -C $RepoRoot diff --check
    if ($LASTEXITCODE -ne 0) { throw 'DIFF CHECK FAILED' }
    Write-Output ('VERIFIED_HEAD=' + $Head)
    Write-Output 'READ_ONLY_BASELINE_CHECK; CONTRACT_CLOSURE=HOLD'
    Write-Output 'RESULT=PASS'
    exit 0
} catch {
    Write-Output ('FAILURE=' + $_.Exception.Message)
    Write-Output 'RESULT=FAIL'
    exit 1
}

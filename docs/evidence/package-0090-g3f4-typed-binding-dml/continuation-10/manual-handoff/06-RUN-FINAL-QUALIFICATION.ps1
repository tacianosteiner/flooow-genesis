$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
try {
    $ExpectedRepo = 'C:\Users\xmz_r\Downloads\flooow-v042-implementation'
    $RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..'))
    $CwdRoot = [IO.Path]::GetFullPath((Get-Location).ProviderPath)
    if ($RepoRoot -ne $ExpectedRepo -or $CwdRoot -ne $ExpectedRepo) { throw 'EXACT WORKTREE/CWD MISMATCH' }
    $Branch = (& git -C $RepoRoot branch --show-current)
    if ($LASTEXITCODE -ne 0 -or $Branch -ne 'checkpoint/package-0090-cloud-handoff') { throw 'BRANCH MISMATCH' }
    $ContractComplete = $false
    $RecipeComplete = $false
    $ExplicitStageAuthorization = $false
    if (-not $ContractComplete -or -not $RecipeComplete) { throw 'CONTRACT/RECIPE INCOMPLETE: 06-RUN-FINAL-QUALIFICATION; AUTHORIZATION ALONE CANNOT REMOVE HOLD' }
    if (-not $ExplicitStageAuthorization) { throw 'HASH_BOUND STAGE AUTHORIZATION REQUIRED' }
    throw 'NO EXECUTION RECIPE INSTALLED; SOURCE REVIEW REQUIRED'
    Write-Output 'RESULT=PASS'
    exit 0
} catch {
    Write-Output ('FAILURE=' + $_.Exception.Message)
    Write-Output 'RESULT=FAIL'
    exit 1
}

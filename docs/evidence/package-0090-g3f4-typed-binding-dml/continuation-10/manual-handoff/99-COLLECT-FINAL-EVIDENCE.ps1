$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
try {
    $ExpectedRepo = 'C:\Users\xmz_r\Downloads\flooow-v042-implementation'
    $RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..'))
    $CwdRoot = [IO.Path]::GetFullPath((Get-Location).ProviderPath)
    if ($RepoRoot -ne $ExpectedRepo -or $CwdRoot -ne $ExpectedRepo) { throw 'EXACT WORKTREE/CWD MISMATCH' }
    $Branch = (& git -C $RepoRoot branch --show-current)
    if ($LASTEXITCODE -ne 0 -or $Branch -ne 'checkpoint/package-0090-cloud-handoff') { throw 'BRANCH MISMATCH' }
    $CaseRoot = Join-Path $RepoRoot 'docs\evidence\package-0090-g3f4-typed-binding-dml'
    $Paths = @('continuation-07\EXPANDED-IDENTIFIER-SUMMARY.json', 'continuation-07\EXPANDED-VARIADIC-BINDINGS.json', 'continuation-08\EXPANDED-DML-STATUS.json', 'continuation-09\CALL-BINDING-STATUS.json', 'continuation-10\RESUME-STATUS.json')
    foreach ($Relative in $Paths) {
        $File = Join-Path $CaseRoot $Relative
        $Text = Get-Content -LiteralPath $File -Raw -Encoding UTF8
        $Parsed = $Text | ConvertFrom-Json
        if (-not $Parsed) { throw 'INVALID REQUIRED EVIDENCE' }
        Write-Output $Text
        Get-FileHash -LiteralPath $File -Algorithm SHA256
    }
    Write-Output 'READ_ONLY_COLLECTION_COMPLETED; RESULT REFERS ONLY TO COLLECTION; ROOM_OPERATIONAL=NO'
    Write-Output 'RESULT=PASS'
    exit 0
} catch {
    Write-Output ('FAILURE=' + $_.Exception.Message)
    Write-Output 'RESULT=FAIL'
    exit 1
}

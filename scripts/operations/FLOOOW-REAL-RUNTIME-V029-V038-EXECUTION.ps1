[CmdletBinding()]
param(
  [switch]$ExecuteRealMigration,
  [string]$ConfirmationToken,
  [Parameter(Mandatory=$false)][string]$ExecutionRepositoryHead
)
$ErrorActionPreference='Stop'
$ExpectedPostgresVersion='18.4'; $ExpectedFlywayVersion='13.2.0'
$ExpectedPackage='00544f9280bb510b7540d207dfe3562e92424ed69f22e9ae2a4ebd1b16cd3511'
$RealPostgresContainer='flooow-genesis-postgres-1'; $RealVolume='flooow-genesis_flooow-postgres-data'
$MigrationLocation='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration'
$Expected=@{
'V030__create_reconciliation_case_revision_assessment_lineage.sql'='d0c9479cb152f1793fd3b7d4d4a7b072a5b29f813feb7444a38241b4ab85a248'; 'V031__create_financial_reconciliation_policy_authority.sql'='f7131a21178d3ed17b154ff2b574d5f27b6d8b57c913f025f384a90424e53ba7'; 'V032__create_financial_ledger_materialization_lineage.sql'='35f00160e777312f39080257ee755d91e067bff461e5aae6f44ae1aaf4a96289'; 'V033__create_omie_transaction_evidence_v3_source_evidence.sql'='eb37c36c9be3025054592048ed910421b9df905ea00c9b31b860bfaccf52e3e4'; 'V034__create_command_authorization.sql'='8745476ccc76d6d0b9b100489f317f6cead44afd0072998401d94c3b595bc5d9'; 'V035__create_explicit_transaction_identity.sql'='697cb21228ceb0237462c59fa70db9d92e673c7e8b034dfc68964ccd01703030'; 'V036__add_transaction_identity_withdrawal.sql'='57fd0e49be6cd5a382009e8af22cfe603ab4c960fe5084ca79404916a4d175cc'; 'V037__add_controlled_command_authority_provisioning.sql'='c19a45d17774450747e1f4f6ad50745a085b37b621abbe1937f134bf688604ce'; 'V038__add_revenue_promotion_economic_observation_lineage.sql'='a9e6388595e63f5bd541ffcacf247847983b3fc48e23bc7e1695574f429b626b' }
function Fail([string]$m){throw "ABORT: $m"}
function Assert([bool]$c,[string]$m){if(-not $c){Fail $m}}
function PackageHash {
 $lines=foreach($n in ($Expected.Keys|Sort-Object)){ $p=Join-Path $MigrationLocation $n; Assert (Test-Path $p) "Missing migration $n"; $h=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower(); Assert ($h -eq $Expected[$n]) "Hash mismatch $n"; "$n`:$h" }
 $actualFiles=(Get-ChildItem $MigrationLocation -Filter 'V0*.sql'|Where-Object Name -match '^V03[0-8]__'|Sort-Object Name|ForEach-Object Name); Assert (($actualFiles -join '|') -eq (($Expected.Keys|Sort-Object)-join '|')) 'Migration set mismatch'
 $sha=New-Object Security.Cryptography.SHA256Managed; (($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($lines -join "`n")+"`n"))|ForEach-Object {$_.ToString('x2')})-join '')
}
function Sql([string]$q) {
  $value = docker exec $RealPostgresContainer psql -U flooow -d flooow -At -v ON_ERROR_STOP=1 -c $q
  Assert ($LASTEXITCODE -eq 0) 'SQL command failed'
  return ($value | Out-String).Trim()
}
function Count([string]$table) { return (Sql "SELECT count(*) FROM $table") }
function RequireEq([string]$actual,[string]$expected,[string]$name) { Assert ($actual -eq $expected) "$name expected $expected actual $actual" }
function Require-PostgresReady {
  $deadline = (Get-Date).AddSeconds(60)
  do {
    docker exec $RealPostgresContainer pg_isready -U flooow -d flooow | Out-Null
    if ($LASTEXITCODE -eq 0) { return }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $deadline)
  Fail 'PostgreSQL readiness timeout'
}
function Assert-ComposeProvenance {
  $compose = Get-Content -LiteralPath 'compose.yaml' -Raw
  Assert ($compose -match '(?ms)^\s*postgres:\s*\r?\n\s*image:\s*postgres:18\.4\s*$') 'compose PostgreSQL image'
  $databaseUrlDeclarations = [regex]::Matches($compose, '(?m)^\s*DATABASE_URL\s*:').Count
  Assert ($databaseUrlDeclarations -eq 1) 'compose DATABASE_URL topology'
  Assert ($compose -match 'jdbc:postgresql://postgres:5432/flooow') 'compose DATABASE_URL target'
}
function Assert-RuntimeProvenance {
  Assert ((docker inspect -f '{{.Name}}' $RealPostgresContainer).Trim('/') -eq $RealPostgresContainer) 'PostgreSQL container'
  $mountedVolume = (docker inspect -f '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql"}}{{.Name}}{{end}}{{end}}' $RealPostgresContainer).Trim()
  RequireEq $mountedVolume $RealVolume 'PostgreSQL volume at /var/lib/postgresql'
  RequireEq (Sql 'SHOW server_version') $ExpectedPostgresVersion 'PostgreSQL version'
  RequireEq (Sql 'SHOW data_directory') '/var/lib/postgresql/18/docker' 'PostgreSQL data directory'
}
function Assert-PreMigrationDatabase {
  Assert-RuntimeProvenance
  RequireEq (Sql "SELECT COALESCE(max(version::integer),-1) FROM flyway_schema_history WHERE success=true AND version ~ '^[0-9]+$'") '29' 'Flyway numeric pre-state'
  foreach($entry in @(@('integration_mercado_livre_order_source_observation','85'),@('marketplace_order_occurrence_source_promotion','21'),@('marketplace_order_identity_registry','12'),@('integration_omie_transaction_evidence','400'))) { RequireEq (Count $entry[0]) $entry[1] $entry[0] }
  foreach($table in 'command_principal','command_credential_revision','command_permission_grant','command_authority_operation','marketplace_transaction_identity_decision','marketplace_transaction_identity_head') { RequireEq (Sql "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='$table'") '0' "pre-migration absence $table" }
}
function Assert-PostMigrationDatabase {
  Assert-RuntimeProvenance
  RequireEq (Sql "SELECT COALESCE(max(version::integer),-1) FROM flyway_schema_history WHERE success=true AND version ~ '^[0-9]+$'") '38' 'Flyway numeric post-state'
  RequireEq (Sql 'SELECT count(*) FROM flyway_schema_history WHERE success=false') '0' 'Flyway failed rows'
  foreach($entry in @(@('integration_mercado_livre_order_source_observation','85'),@('marketplace_order_occurrence_source_promotion','21'),@('marketplace_order_identity_registry','12'),@('integration_omie_transaction_evidence','400'),@('command_principal','0'),@('command_credential_revision','0'),@('command_permission_grant','0'),@('command_authority_operation','0'),@('marketplace_transaction_identity_decision','0'),@('marketplace_transaction_identity_head','0'),@('integration_omie_transaction_evidence_v3','0'),@('integration_omie_transaction_evidence_v3_line','0'))) { RequireEq (Count $entry[0]) $entry[1] $entry[0] }
  Assert ([bool](docker volume inspect $script:snapshot 2>$null)) 'snapshot volume missing'
}
function Assert-NoUnexpectedDatabaseWriterSessions {
  $rows = Sql "SELECT pid || '|' || usename || '|' || coalesce(application_name,'') || '|' || coalesce(client_addr::text,'') || '|' || backend_type || '|' || coalesce(state,'') || '|' || coalesce(xact_start::text,'') || '|' || coalesce(query_start::text,'') FROM pg_stat_activity WHERE datname='flooow' AND pid <> pg_backend_pid() ORDER BY pid"
  if ([string]::IsNullOrWhiteSpace($rows)) { return }
  $unexpected = @($rows -split "`r?`n" | Where-Object { $parts = $_ -split '\|', 9; $parts.Count -ge 5 -and $parts[4] -eq 'client backend' })
  Assert ($unexpected.Count -eq 0) "unexpected database client session(s): $($unexpected -join '; ')"
}
function Assert-NoLongTransactionsOrV036Locks {
  $longTransactionThresholdSeconds = 60
  $longTransactions = Sql "SELECT count(*) FROM pg_stat_activity WHERE datname='flooow' AND pid <> pg_backend_pid() AND backend_type='client backend' AND xact_start IS NOT NULL AND extract(epoch FROM clock_timestamp()-xact_start) > $longTransactionThresholdSeconds"
  RequireEq $longTransactions '0' 'long client transactions'
  $v036Locks = Sql "SELECT count(*) FROM pg_locks l JOIN pg_class c ON c.oid=l.relation JOIN pg_stat_activity a ON a.pid=l.pid WHERE c.relname IN ('marketplace_transaction_identity_decision','marketplace_transaction_identity_head') AND a.datname='flooow' AND a.pid <> pg_backend_pid() AND a.backend_type='client backend'"
  RequireEq $v036Locks '0' 'V036 relation locks'
}
function Preflight {
  git fetch origin
  Assert ($LASTEXITCODE -eq 0) 'git fetch origin'
  Assert ((git branch --show-current) -eq 'main') 'branch'
  Assert ((git status --porcelain).Length -eq 0) 'worktree/index'
  Assert ((git rev-parse HEAD) -eq $ExecutionRepositoryHead) 'HEAD'
  Assert ((git rev-parse origin/main) -eq $ExecutionRepositoryHead) 'origin/main'
  RequireEq (PackageHash) $ExpectedPackage 'migration package'
  Assert-ComposeProvenance
  Assert-RuntimeProvenance
}
function Stage([string]$name,[scriptblock]$body) { Write-Host "STAGE_$name = START"; try { & $body; Write-Host "STAGE_$name = PASS" } catch { Write-Host "STAGE_$name = FAIL"; throw } }

Write-Host 'Contract: V029->V038. No authority activation.'
RequireEq (PackageHash) $ExpectedPackage 'migration package'
if (-not $ExecuteRealMigration) { Write-Host 'Destructive stages disabled. Use -ExecuteRealMigration -ConfirmationToken I_UNDERSTAND_REAL_V029_TO_V038 -ExecutionRepositoryHead <committed SHA>.'; exit 0 }
Assert ($ConfirmationToken -eq 'I_UNDERSTAND_REAL_V029_TO_V038') 'confirmation token'
Assert (-not [string]::IsNullOrWhiteSpace($ExecutionRepositoryHead)) 'execution HEAD'

$script:H_PASS = $false
$script:I_PASS = $false
$script:api = @()
$script:snapshot = ''

Stage A { Preflight; Assert-PreMigrationDatabase }
Stage B {
  $script:api = @(docker ps -aq --filter 'label=com.docker.compose.service=api')
  Assert ($script:api.Count -eq 1) 'API topology'
  docker stop $script:api[0] | Out-Null
  Assert ((docker inspect -f '{{.State.Running}}' $script:api[0]).Trim() -eq 'false') 'API stop verification'
  Assert-NoUnexpectedDatabaseWriterSessions
}
Stage C {
  Assert-PreMigrationDatabase
  docker stop $RealPostgresContainer | Out-Null
  Assert ((docker inspect -f '{{.State.Running}}' $RealPostgresContainer).Trim() -eq 'false') 'PostgreSQL stop verification'
  $script:snapshot = "flooow-genesis-real-v029-snapshot-$(Get-Date -Format yyyyMMddHHmmss)"
  docker volume inspect $script:snapshot 2>$null | Out-Null
  Assert ($LASTEXITCODE -ne 0) 'snapshot collision'
  docker volume create $script:snapshot | Out-Null
  Assert ($LASTEXITCODE -eq 0) 'snapshot volume creation'
  docker run --rm -v "${RealVolume}:/from:ro" -v "${script:snapshot}:/to" alpine:3.21 sh -ceu 'cp -a /from/. /to/'
  Assert ($LASTEXITCODE -eq 0) 'stopped PostgreSQL physical snapshot copy'
}
Stage D {
  docker run --rm -v "${script:snapshot}:/snapshot:ro" alpine:3.21 test -f /snapshot/18/docker/PG_VERSION
  Assert ($LASTEXITCODE -eq 0) 'snapshot PG_VERSION file'
  $snapshotMajor = (docker run --rm -v "${script:snapshot}:/snapshot:ro" alpine:3.21 cat /snapshot/18/docker/PG_VERSION | Out-String).Trim()
  RequireEq $snapshotMajor '18' 'snapshot PostgreSQL major version'
  docker run --rm -v "${script:snapshot}:/snapshot:ro" alpine:3.21 test -f /snapshot/18/docker/global/pg_control
  Assert ($LASTEXITCODE -eq 0) 'snapshot pg_control file'
  docker run --rm -v "${script:snapshot}:/snapshot:ro" alpine:3.21 test -d /snapshot/18/docker/base
  Assert ($LASTEXITCODE -eq 0) 'snapshot base directory'
  docker run --rm -v "${script:snapshot}:/snapshot:ro" alpine:3.21 test -d /snapshot/18/docker/pg_wal
  Assert ($LASTEXITCODE -eq 0) 'snapshot pg_wal directory'
  docker start $RealPostgresContainer | Out-Null
  Require-PostgresReady
}
Stage E { Assert-PreMigrationDatabase; Assert-NoUnexpectedDatabaseWriterSessions; Assert-NoLongTransactionsOrV036Locks }

$mount = (Resolve-Path $MigrationLocation).Path
$envLines = docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' $RealPostgresContainer
$passwordLine = $envLines | Where-Object { $_ -like 'POSTGRES_PASSWORD=*' } | Select-Object -First 1
Assert ($null -ne $passwordLine) 'database password unavailable'
$password = $passwordLine.Substring('POSTGRES_PASSWORD='.Length)
$hadFlywayPassword = Test-Path Env:FLYWAY_PASSWORD
$previousFlywayPassword = $env:FLYWAY_PASSWORD
$env:FLYWAY_PASSWORD = $password
Remove-Variable password
$flywayRun = @('--rm','--network',"container:$RealPostgresContainer",'--env','FLYWAY_PASSWORD','--mount',"type=bind,source=$mount,target=/flyway/sql,readonly",'flyway/flyway:13.2.0','-url=jdbc:postgresql://127.0.0.1:5432/flooow','-user=flooow','-locations=filesystem:/flyway/sql','-outOfOrder=false','-validateOnMigrate=true','-target=38')
try {
  Stage F {
    $flywayVersion = (& docker run --rm flyway/flyway:13.2.0 -v | Out-String)
    Assert ($LASTEXITCODE -eq 0 -and $flywayVersion -match '(?m)13\.2\.0') 'Flyway binary version'
    $infoJson = (& docker run @flywayRun info -outputType=json | Out-String)
    Assert ($LASTEXITCODE -eq 0) 'Flyway info'
    $info = $infoJson | ConvertFrom-Json
    $migrations = @($info.migrations)
    $pending = @($migrations | Where-Object { $_.state -eq 'Pending' } | ForEach-Object { [int]$_.version } | Sort-Object)
    $expectedPending = @(30,31,32,33,34,35,36,37,38)
    Assert (($pending -join ',') -eq ($expectedPending -join ',')) 'exact Flyway pending set'
    $appliedAfter29 = @($migrations | Where-Object { $_.state -eq 'Success' -and [int]$_.version -ge 30 })
    Assert ($appliedAfter29.Count -eq 0) 'unexpected applied migration >= V030'
    & docker run @flywayRun validate
    Assert ($LASTEXITCODE -eq 0) 'Flyway validate'
  }
  Stage G { & docker run @flywayRun migrate; Assert ($LASTEXITCODE -eq 0) 'Flyway migrate' }
  Stage H { Assert-PostMigrationDatabase; $script:H_PASS = $true }
  Stage I {
    $env:GRADLE_USER_HOME = "$env:USERPROFILE\.gradle"
    & .\gradlew.bat :applications:marketplace-operations-persistence-postgres:test --tests 'io.flooow.marketplace.persistence.postgres.PostgresReconciliationCaseRevisionLineageSchemaTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresFinancialReconciliationPolicySourceTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresFinancialLedgerMaterializationLineageSchemaTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresCommandAuthorizationTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresControlledCommandAuthorityIssuerTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresTransactionIdentityWriterTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresMarketplaceOrderRevenueLineageTest' --no-daemon --console=plain
    Assert ($LASTEXITCODE -eq 0) 'migration regressions'
    $script:I_PASS = $true
  }
  Stage J {
    Assert ($script:H_PASS -and $script:I_PASS) 'post-migration and regression gates'
    Assert-PostMigrationDatabase
    docker start $script:api[0] | Out-Null
    $apiStabilityObservationSeconds = 20
    $deadline = (Get-Date).AddSeconds($apiStabilityObservationSeconds)
    do {
      $state = docker inspect -f '{{.State.Running}}|{{.State.Restarting}}|{{.State.ExitCode}}' $script:api[0]
      Assert ($state.Trim() -eq 'true|false|0') 'API stability observation'
      Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    Write-Host "API_STABILITY_GUARD = PASS"
    Write-Host "SNAPSHOT_VOLUME=$script:snapshot"
  }
} finally {
  if ($hadFlywayPassword) { $env:FLYWAY_PASSWORD = $previousFlywayPassword } else { Remove-Item Env:FLYWAY_PASSWORD -ErrorAction SilentlyContinue }
}

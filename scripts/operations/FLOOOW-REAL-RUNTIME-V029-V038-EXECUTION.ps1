[CmdletBinding()]
param(
  [switch]$ExecuteRealMigration,
  [string]$ConfirmationToken,
  [Parameter(Mandatory=$false)][string]$ExecutionRepositoryHead
)
$ErrorActionPreference='Stop'
$ExpectedHeadPre='f3d9efa81f2f9f295c30b905a8ef025178faa8c6'
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
function Sql([string]$q){docker exec $RealPostgresContainer psql -U flooow -d flooow -At -v ON_ERROR_STOP=1 -c $q}
function Count([string]$table){(Sql "SELECT count(*) FROM $table").Trim()}
function RequireEq([string]$actual,[string]$expected,[string]$name){Assert ($actual -eq $expected) "$name expected $expected actual $actual"}
function Preflight {
 Assert ((git branch --show-current)-eq 'main') 'branch'; Assert ((git status --porcelain).Length -eq 0) 'worktree'; Assert ((git rev-parse HEAD)-eq $ExecutionRepositoryHead) 'HEAD'; Assert ((git rev-parse origin/main)-eq $ExecutionRepositoryHead) 'origin/main'; RequireEq (PackageHash) $ExpectedPackage 'migration package'; Assert ((docker inspect -f '{{.Name}}' $RealPostgresContainer).Trim('/') -eq $RealPostgresContainer) 'container'; Assert ((docker inspect -f '{{range .Mounts}}{{if eq .Name "flooow-genesis_flooow-postgres-data"}}{{.Name}}{{end}}{{end}}' $RealPostgresContainer) -eq $RealVolume) 'volume'; RequireEq (Sql 'SHOW server_version') $ExpectedPostgresVersion 'PostgreSQL'; RequireEq (Sql 'SELECT max(version) FROM flyway_schema_history WHERE success') '29' 'Flyway pre'; RequireEq (Count 'integration_mercado_livre_order_source_observation') '85' 'V021'; RequireEq (Count 'marketplace_order_occurrence_source_promotion') '21' 'V022 promotion'; RequireEq (Count 'marketplace_order_identity_registry') '12' 'V022 registry'; RequireEq (Count 'integration_omie_transaction_evidence') '400' 'V026'; foreach($t in 'command_principal','command_credential_revision','command_permission_grant','command_authority_operation','marketplace_transaction_identity_decision','marketplace_transaction_identity_head'){RequireEq (Sql "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='$t'") '0' "pre absent $t"}
}
Write-Host 'Contract: V029->V038. No authority activation.'; Assert ((PackageHash)-eq $ExpectedPackage) 'package hash'
if(-not $ExecuteRealMigration){Write-Host 'Destructive stages disabled. Use -ExecuteRealMigration -ConfirmationToken I_UNDERSTAND_REAL_V029_TO_V038 -ExecutionRepositoryHead <committed SHA>.'; exit 0}
Assert ($ConfirmationToken -eq 'I_UNDERSTAND_REAL_V029_TO_V038') 'confirmation token'
Assert (-not [string]::IsNullOrWhiteSpace($ExecutionRepositoryHead)) 'execution HEAD'
function Stage($n,$b){Write-Host "STAGE_$n = START";try{&$b;Write-Host "STAGE_$n = PASS"}catch{Write-Host "STAGE_$n = FAIL";throw}}
$H_PASS=$false;$I_PASS=$false
Stage A {Preflight}
Stage B {$script:api=@(docker ps -aq --filter 'label=com.docker.compose.service=api');Assert ($api.Count -eq 1) 'API topology';docker stop $api[0]|Out-Null;Assert ((docker inspect -f '{{.State.Running}}' $api[0])-eq 'false') 'API running'}
Stage C {docker stop $RealPostgresContainer|Out-Null;Assert ((docker inspect -f '{{.State.Running}}' $RealPostgresContainer)-eq 'false') 'PostgreSQL running';$script:snapshot="flooow-genesis-real-v029-snapshot-$(Get-Date -Format yyyyMMddHHmmss)";docker volume create $snapshot|Out-Null;docker run --rm -v "${RealVolume}:/from:ro" -v "${snapshot}:/to" alpine:3.21 sh -ceu 'cp -a /from/. /to/'}
Stage D {docker run --rm -v "${snapshot}:/snapshot:ro" alpine:3.21 sh -ceu 'test "$(cat /snapshot/18/docker/PG_VERSION)" = 18; test -f /snapshot/18/docker/global/pg_control; test -d /snapshot/18/docker/base; test -d /snapshot/18/docker/pg_wal';docker start $RealPostgresContainer|Out-Null}
Stage E {Preflight}
$mount=(Resolve-Path $MigrationLocation).Path
$envLines=docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' $RealPostgresContainer
$passwordLine=$envLines | Where-Object { $_ -like 'POSTGRES_PASSWORD=*' } | Select-Object -First 1
Assert ($null -ne $passwordLine) 'database password unavailable'
$password=$passwordLine.Substring('POSTGRES_PASSWORD='.Length)
$fly=@('--rm','--network',"container:$RealPostgresContainer",'--mount',"type=bind,source=$mount,target=/flyway/sql,readonly",'flyway/flyway:13.2.0','-url=jdbc:postgresql://127.0.0.1:5432/flooow','-user=flooow',"-password=$password",'-locations=filesystem:/flyway/sql','-outOfOrder=false','-validateOnMigrate=true','-target=38')
Stage F { & docker run @fly validate; Assert ($LASTEXITCODE -eq 0) 'validate' }
Stage G { & docker run @fly migrate; Assert ($LASTEXITCODE -eq 0) 'migrate' }
Stage H { RequireEq (Sql 'SELECT max(version) FROM flyway_schema_history WHERE success') '38' 'post Flyway'; RequireEq (Sql 'SELECT count(*) FROM flyway_schema_history WHERE NOT success') '0' 'failed Flyway'; foreach($x in @(@('integration_mercado_livre_order_source_observation','85'),@('marketplace_order_occurrence_source_promotion','21'),@('marketplace_order_identity_registry','12'),@('integration_omie_transaction_evidence','400'),@('command_principal','0'),@('command_credential_revision','0'),@('command_permission_grant','0'),@('command_authority_operation','0'),@('marketplace_transaction_identity_decision','0'),@('marketplace_transaction_identity_head','0'),@('integration_omie_transaction_evidence_v3','0'),@('integration_omie_transaction_evidence_v3_line','0'))){RequireEq (Count $x[0]) $x[1] $x[0]}; Assert (docker volume inspect $snapshot 2>$null) 'snapshot missing'; $script:H_PASS=$true }
Stage I { $env:GRADLE_USER_HOME="$env:USERPROFILE\.gradle"; & .\gradlew.bat :applications:marketplace-operations-persistence-postgres:test --tests 'io.flooow.marketplace.persistence.postgres.PostgresReconciliationCaseRevisionLineageSchemaTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresFinancialReconciliationPolicySourceTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresFinancialLedgerMaterializationLineageSchemaTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresCommandAuthorizationTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresControlledCommandAuthorityIssuerTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresTransactionIdentityWriterTest' --tests 'io.flooow.marketplace.persistence.postgres.PostgresMarketplaceOrderRevenueLineageTest' --no-daemon --console=plain; Assert ($LASTEXITCODE -eq 0) 'regressions'; $script:I_PASS=$true }
Stage J { Assert ($H_PASS -and $I_PASS) 'H/I required'; docker start $api[0]|Out-Null; Remove-Variable password; Write-Host "SNAPSHOT_VOLUME=$snapshot" }

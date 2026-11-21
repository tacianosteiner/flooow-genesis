$ErrorActionPreference = 'Stop'
$outputPath = $PSScriptRoot
$parentPath = Join-Path (Split-Path $outputPath -Parent) 'authority-receipt.json'
$receipt = [ordered]@{
    PARENT_AUTHORITY = 'FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1'
    CHILD_AUTHORITY_ID = 'PACKAGE_0090_EXISTING_HOST_CONTROL_ORIGIN_READONLY_V1'
    PURPOSE = 'Observe actual existing local HOST control executor for prospective policy/source custody'
    SCOPE = 'Read-only local Docker daemon/context, client executable integrity and selected Windows service/process metadata'
    INPUTS = @('Existing local Docker client/context', 'Current Windows execution principal', 'com.docker.service', 'com.docker.backend')
    PERMITTED_EFFECTS = @('docker info/version/context inspect metadata reads', 'CIM selected service metadata', 'Selected process creation/path and Authenticode metadata', 'Write new evidence in this directory')
    PROHIBITED_EFFECTS = @('DB', 'network outside existing local HOST endpoint', 'credentials/tokens', 'service/process mutation', 'policy approval/activation', 'source acceptance', 'V043', 'B02')
    PRECONDITIONS = 'Current project mandate; no container or service is started/stopped by this capture'
    EXIT_CONDITIONS = 'Preserve observed facts, missing metadata and error outcomes; do not equate machine privilege with authority'
    EXPIRY_OR_TERMINATION = 'End of bounded local metadata capture'
    PARENT_BOUNDARY_HASH_OR_REFERENCE = @{ path = '../authority-receipt.json'; sha256 = (Get-FileHash -LiteralPath $parentPath -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$receipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $outputPath 'authority-receipt.json') -Encoding UTF8
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$dockerCommand = Get-Command docker -CommandType Application | Select-Object -First 1
$dockerPath = $dockerCommand.Source
$dockerSignature = Get-AuthenticodeSignature -LiteralPath $dockerPath
$contextName = (& docker context show | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Docker context metadata unavailable' }
$contextRaw = (& docker context inspect $contextName | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'Docker context inspection unavailable' }
$context = ($contextRaw | ConvertFrom-Json)[0]
# Do not emit unneeded proxy, registry or other full daemon configuration.
$infoRaw = (& docker info --format '{{json .}}' | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'Docker daemon metadata unavailable' }
$info = $infoRaw | ConvertFrom-Json
$services = @(Get-CimInstance Win32_Service -Filter "Name='com.docker.service'" | Select-Object Name, State, StartName, ProcessId, PathName)
$processes = @(Get-Process -Name 'com.docker.backend' -ErrorAction SilentlyContinue | Select-Object -First 4 | ForEach-Object {
    $processPath = $_.Path
    $signature = if ($processPath) { Get-AuthenticodeSignature -LiteralPath $processPath } else { $null }
    [ordered]@{
        name = $_.ProcessName
        pid = $_.Id
        creation_time_utc = $_.StartTime.ToUniversalTime().ToString('o')
        executable = $processPath
        executable_sha256 = if ($processPath) { (Get-FileHash -LiteralPath $processPath -Algorithm SHA256).Hash.ToLowerInvariant() } else { 'NOT_ESTABLISHED' }
        signature_status = if ($signature) { $signature.Status.ToString() } else { 'NOT_ESTABLISHED' }
        signer_subject = if ($signature -and $signature.SignerCertificate) { $signature.SignerCertificate.Subject } else { 'NOT_ESTABLISHED' }
    }
})
$record = [ordered]@{
    classification = 'EXISTING_HOST_CONTROL_ORIGIN_METADATA_ONLY_NOT_TRUST_OR_POLICY_ACCEPTANCE'
    captured_at_utc = [DateTime]::UtcNow.ToString('o')
    execution_principal = @{ name = $identity.Name; sid = $identity.User.Value; authentication_type = $identity.AuthenticationType }
    docker_client = @{
        executable = $dockerPath
        sha256 = (Get-FileHash -LiteralPath $dockerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        signature_status = $dockerSignature.Status.ToString()
        signer_subject = if ($dockerSignature.SignerCertificate) { $dockerSignature.SignerCertificate.Subject } else { 'NOT_ESTABLISHED' }
    }
    docker_context = @{ name = $contextName; endpoint = $context.Endpoints.docker.Host }
    daemon = @{ id = $info.ID; name = $info.Name; server_version = $info.ServerVersion; os_type = $info.OSType; operating_system = $info.OperatingSystem; kernel_version = $info.KernelVersion; security_options = $info.SecurityOptions }
    docker_windows_service = $services
    selected_backend_processes = $processes
    authority_limits = @('OS identity/privilege is not project authority', 'Docker metadata is not independently approved HOST delegation', 'File signature/hash is not policy acceptance', 'Actual custodian process/context/channel and independent acceptance remain required', 'No policy or source is approved or activated by this capture')
    shared_db_contacted = $false
    production_contacted = $false
    original_db_contacted = $false
}
$record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $outputPath 'control-origin-metadata.json') -Encoding UTF8
[ordered]@{ classification = $record.classification; docker_context = $contextName; endpoint_type = ($context.Endpoints.docker.Host -split ':')[0]; services_observed = $services.Count; backend_processes_observed = $processes.Count } | ConvertTo-Json -Compress

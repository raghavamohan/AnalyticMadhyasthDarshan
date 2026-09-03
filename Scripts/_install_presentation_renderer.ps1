param(
    [string]$Profile = "libreoffice-ci-candidate",
    [string]$CacheDirectory = ""
)

$ErrorActionPreference = "Stop"

$manifestPath = Join-Path $PSScriptRoot "presentation-pipeline.json"
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$renderer = $manifest.rendererProfiles.$Profile
if ($null -eq $renderer) {
    throw "Unknown presentation renderer profile: $Profile"
}
if ($renderer.engine -ne "libreoffice") {
    throw "Installer supports LibreOffice profiles only; $Profile uses $($renderer.engine)"
}
if (-not $renderer.installer.url -or -not $renderer.installer.sha256) {
    throw "Renderer profile $Profile has no pinned installer URL/SHA-256"
}

if (-not $CacheDirectory) {
    $base = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }
    $CacheDirectory = Join-Path $base "presentation-renderers"
}
$cache = [IO.Path]::GetFullPath($CacheDirectory)
New-Item -ItemType Directory -Force -Path $cache | Out-Null
$installer = Join-Path $cache "LibreOffice-$($renderer.version)-x86_64.msi"
$expected = $renderer.installer.sha256.ToLowerInvariant()

if (Test-Path -LiteralPath $installer) {
    $cached = (Get-FileHash -Algorithm SHA256 -LiteralPath $installer).Hash.ToLowerInvariant()
    if ($cached -ne $expected) {
        Remove-Item -LiteralPath $installer -Force
    }
}
if (-not (Test-Path -LiteralPath $installer)) {
    Write-Host "Downloading pinned LibreOffice $($renderer.version) installer"
    Invoke-WebRequest -UseBasicParsing -Uri $renderer.installer.url -OutFile $installer
}
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $installer).Hash.ToLowerInvariant()
if ($actual -ne $expected) {
    throw "LibreOffice installer SHA-256 mismatch: expected $expected, got $actual"
}

$sofficeExe = Join-Path $env:ProgramFiles "LibreOffice\program\soffice.exe"
$soffice = Join-Path $env:ProgramFiles "LibreOffice\program\soffice.com"
$installedVersion = ""
if (Test-Path -LiteralPath $soffice) {
    $versionOutput = & $soffice --version
    if ($versionOutput -match "(\d+\.\d+\.\d+\.\d+)") {
        $installedVersion = $Matches[1]
    }
}
if ($installedVersion -ne $renderer.version) {
    $arguments = @(
        "/i",
        "`"$installer`"",
        "/qn",
        "/norestart",
        "ALLUSERS=1"
    )
    $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $arguments `
        -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -notin @(0, 3010)) {
        throw "LibreOffice installer failed with exit code $($process.ExitCode)"
    }
}

if (-not (Test-Path -LiteralPath $sofficeExe) -or -not (Test-Path -LiteralPath $soffice)) {
    throw "LibreOffice executable/console launcher not found after installation"
}
$versionOutput = & $soffice --version
$versionMatch = [regex]::Match([string]$versionOutput, "(\d+\.\d+\.\d+\.\d+)")
if (-not $versionMatch.Success) {
    throw "Could not parse LibreOffice version: $versionOutput"
}
$actualVersion = $versionMatch.Groups[1].Value
if ($actualVersion -ne $renderer.version) {
    throw "Installed LibreOffice $actualVersion; profile requires $($renderer.version)"
}
Write-Host "Installed verified $Profile (LibreOffice $($renderer.version))"

# Download open-access / public-domain references into References/
# Usage:
#   .\Scripts\_download_references.ps1
#   .\Scripts\_download_references.ps1 -Tag "McTaggart 1908" -Tag "Hashemi 2025"
#   .\Scripts\_download_references.ps1 -DryRun
#   .\Scripts\_download_references.ps1 -Force
param(
    [string[]]$Tag,
    [switch]$DryRun,
    [switch]$Force,
    [switch]$SkipCacheSync
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
$PyScript = Join-Path $ScriptDir '_download_references.py'

$args = @($PyScript)
foreach ($t in $Tag) {
    $args += @('--tag', $t)
}
if ($DryRun) { $args += '--dry-run' }
if ($Force) { $args += '--force' }
if ($SkipCacheSync) { $args += '--skip-cache-sync' }

python @args

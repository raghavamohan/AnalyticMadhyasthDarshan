# Remove a study from Studies/ and update catalog files.
# Usage:
#   .\Scripts\_remove_study.ps1 Study-Slug
#   .\Scripts\_remove_study.ps1 Why-Humans-Are-Not-Just-Material -DryRun
#   .\Scripts\_remove_study.ps1 Study-Slug -Yes
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Slug,

    [switch]$DryRun,
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
$PyScript = Join-Path $ScriptDir '_remove_study.py'

$args = @($PyScript, $Slug)
if ($DryRun) { $args += '--dry-run' }
if ($Yes) { $args += '--yes' }

python @args

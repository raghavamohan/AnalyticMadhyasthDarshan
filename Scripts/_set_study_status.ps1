# Change a study between Draft and Released status.
# Usage:
#   .\Scripts\_set_study_status.ps1 Study-Slug -Status released
#   .\Scripts\_set_study_status.ps1 Study-Slug -Status draft
#   .\Scripts\_set_study_status.ps1 Study-Slug
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Slug,

    [ValidateSet('draft', 'released')]
    [string]$Status,
    [switch]$DryRun,
    [switch]$SkipPdf,
    [switch]$NoCheckTimestamps
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
$PyScript = Join-Path $ScriptDir '_set_study_status.py'

$args = @($PyScript, $Slug)
if ($Status) { $args += @('--status', $Status) }
if ($DryRun) { $args += '--dry-run' }
if ($SkipPdf) { $args += '--skip-pdf' }
if ($NoCheckTimestamps) { $args += '--no-check-timestamps' }

python @args

# Add a study PDF to Studies/ and update catalog files.
# Usage:
#   .\Scripts\_add_study.ps1 path\to\paper.pdf
#   .\Scripts\_add_study.ps1 paper.pdf -Title "My Study" -Description "Summary" -Tags "MVD, SB, JV"
#   .\Scripts\_add_study.ps1 paper.pdf -DryRun
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Pdf,

    [string]$Title,
    [string]$Slug,
    [string]$Description,
    [string]$Tags,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
$PyScript = Join-Path $ScriptDir '_add_study.py'

$args = @($PyScript, (Resolve-Path $Pdf).Path)
if ($Title) { $args += @('--title', $Title) }
if ($Slug) { $args += @('--slug', $Slug) }
if ($Description) { $args += @('--description', $Description) }
if ($Tags) { $args += @('--tags', $Tags) }
if ($DryRun) { $args += '--dry-run' }
if ($Force) { $args += '--force' }

python @args

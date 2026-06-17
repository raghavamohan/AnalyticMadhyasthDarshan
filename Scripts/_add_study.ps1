# Add or register a study and update catalog files.
# Usage:
#   .\Scripts\_add_study.ps1 path\to\Study.md
#   .\Scripts\_add_study.ps1 path\to\external.pdf
#   .\Scripts\_add_study.ps1 Study.md -Category Ontology -Description "Summary" -Tags "MVD, SB, JV"
#   .\Scripts\_add_study.ps1 Study.md -Status ongoing -DryRun
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Input,

    [string]$Title,
    [string]$Slug,
    [string]$Category,
    [string]$Description,
    [string]$Tags,
    [ValidateSet('draft', 'released', 'ongoing')]
    [string]$Status = 'draft',
    [switch]$Formal,
    [switch]$DryRun,
    [switch]$Force,
    [switch]$SkipPdf,
    [switch]$NoCheckTimestamps
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
$PyScript = Join-Path $ScriptDir '_add_study.py'

$args = @($PyScript, (Resolve-Path $Input).Path)
if ($Title) { $args += @('--title', $Title) }
if ($Slug) { $args += @('--slug', $Slug) }
if ($Category) { $args += @('--category', $Category) }
if ($Description) { $args += @('--description', $Description) }
if ($Tags) { $args += @('--tags', $Tags) }
$args += @('--status', $Status)
if ($Formal) { $args += '--formal' }
if ($DryRun) { $args += '--dry-run' }
if ($Force) { $args += '--force' }
if ($SkipPdf) { $args += '--skip-pdf' }
if ($NoCheckTimestamps) { $args += '--no-check-timestamps' }

python @args

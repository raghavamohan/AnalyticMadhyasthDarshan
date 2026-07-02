# Rename a study slug and sync proposal-tracking metadata.
# Usage:
#   .\Scripts\_rename_study.ps1 -From Old-Slug -To New-Slug
#   .\Scripts\_rename_study.ps1 -From Old-Slug -To New-Slug -Title "New display title"
#   .\Scripts\_rename_study.ps1 -From Old-Slug -To New-Slug -MetadataOnly
param(
    [Parameter(Mandatory = $true)]
    [string]$From,

    [Parameter(Mandatory = $true)]
    [string]$To,

    [string]$Title,
    [int]$Issue,
    [switch]$MetadataOnly,
    [switch]$SkipIssue,
    [switch]$SkipPdf,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
$PyScript = Join-Path $ScriptDir '_rename_study.py'

$args = @($PyScript, '--from', $From, '--to', $To)
if ($Title) { $args += @('--title', $Title) }
if ($Issue) { $args += @('--issue', $Issue) }
if ($MetadataOnly) { $args += '--metadata-only' }
if ($SkipIssue) { $args += '--skip-issue' }
if ($SkipPdf) { $args += '--skip-pdf' }
if ($DryRun) { $args += '--dry-run' }

python @args

# Run all reference integrity checks for Studies/ and References/
# Usage:
#   .\Scripts\_check_references.ps1
#   .\Scripts\_check_references.ps1 -Study Knowledge-Knower-And-Known
#   .\Scripts\_check_references.ps1 -SkipPdf
param(
    [string]$Study,
    [switch]$SkipPdf
)

$ErrorActionPreference = 'Stop'
$PyScript = Join-Path $PSScriptRoot '_check_references.py'

$args = @($PyScript)
if ($Study) { $args += @('--study', $Study) }
if ($SkipPdf) { $args += '--skip-pdf' }

python @args

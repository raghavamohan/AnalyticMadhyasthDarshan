param(
    [string]$Work = 'E:\MD-Transcription',
    [string]$OutputDir = '',
    [string]$PreviewDir = '',
    [Parameter(Mandatory = $true)][string]$NodeExe,
    [Parameter(Mandatory = $true)][string]$NodeModules,
    [string[]]$Only = @(),
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$nodePath = (Resolve-Path -LiteralPath $NodeExe).Path
$modulesPath = (Resolve-Path -LiteralPath $NodeModules).Path
$builderPath = Join-Path $PSScriptRoot '_build_transcription_review_xlsx.mjs'
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$runtimePath = Join-Path $tempRoot ('md-transcription-xlsx-' + [guid]::NewGuid().ToString('N'))
$resolvedRuntime = [System.IO.Path]::GetFullPath($runtimePath)
if (-not $resolvedRuntime.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to create runtime outside the temporary root: $resolvedRuntime"
}

try {
    New-Item -ItemType Directory -Path $resolvedRuntime | Out-Null
    New-Item -ItemType Junction -Path (Join-Path $resolvedRuntime 'node_modules') -Target $modulesPath | Out-Null
    Copy-Item -LiteralPath $builderPath -Destination (Join-Path $resolvedRuntime 'builder.mjs')

    $arguments = @((Join-Path $resolvedRuntime 'builder.mjs'), '--work', $Work)
    if ($OutputDir) { $arguments += @('--output-dir', $OutputDir) }
    if ($PreviewDir) { $arguments += @('--preview-dir', $PreviewDir) }
    if ($Only.Count -gt 0) { $arguments += '--only'; $arguments += $Only }
    if ($Force) { $arguments += '--force' }

    & $nodePath @arguments
    if ($LASTEXITCODE -ne 0) { throw "Excel review workbook builder exited $LASTEXITCODE" }
}
finally {
    if (Test-Path -LiteralPath $resolvedRuntime) {
        $checkedRuntime = [System.IO.Path]::GetFullPath($resolvedRuntime)
        if ($checkedRuntime.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $checkedRuntime -Recurse -Force
        }
    }
}

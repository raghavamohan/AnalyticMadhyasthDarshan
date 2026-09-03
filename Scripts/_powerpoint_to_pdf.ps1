param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$powerPoint = $null
$presentation = $null

try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    try { $powerPoint.Visible = -1 } catch { }
    try { $powerPoint.DisplayAlerts = 1 } catch { }

    # Open(FileName, ReadOnly, Untitled, WithWindow); integers avoid COM boolean
    # coercion differences across PowerShell versions.
    $presentation = $powerPoint.Presentations.Open($InputPath, 1, 0, 0)
    # ppSaveAsPDF = 32. SaveAs is more consistent across installed Office builds
    # than ExportAsFixedFormat's optional-argument COM signature.
    $presentation.SaveAs($OutputPath, 32)
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    }
    if ($null -ne $powerPoint) {
        $powerPoint.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

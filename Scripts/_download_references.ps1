# Downloads cited references for Studies into References/
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$RefRoot = Join-Path $Root 'References'

$dirs = @(
    $RefRoot,
    (Join-Path $RefRoot 'Madhyasth-Darshan'),
    (Join-Path $RefRoot 'Advaita-Vedanta'),
    (Join-Path $RefRoot 'Comparative-Philosophy'),
    (Join-Path $RefRoot 'Science')
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

function Save-Url {
    param(
        [string]$Url,
        [string]$Dest
    )
    $destPath = Join-Path $RefRoot $Dest
    Write-Host "Downloading $Dest ..."
    Invoke-WebRequest -Uri $Url -OutFile $destPath -UserAgent 'Mozilla/5.0' -MaximumRedirection 5
    if ((Get-Item $destPath).Length -lt 1024) {
        throw "Download too small, likely failed: $Dest"
    }
}

# Advaita Vedanta, comparative philosophy (AV, SV), and open-access science papers.
# ATR and commercial science books: see References/NOT-DOWNLOADED.md.
$downloads = @(
    @{
        Dest = 'Advaita-Vedanta\BU-Brihadaranyaka-Upanishad-Madhavananda.pdf'
        Urls = @(
            'https://archive.org/download/Brihadaranyaka.Upanishad.Shankara.Bhashya.by.Swami.Madhavananda/Brihadaranyaka.Upanishad.Shankara.Bhashya.by.Swami.Madhavananda.pdf',
            'https://archive.org/download/in.ernet.dli.2015.20823/in.ernet.dli.2015.20823.pdf'
        )
    },
    @{
        Dest = 'Advaita-Vedanta\CU-Chandogya-Upanishad-Gambhirananda.pdf'
        Urls = @('https://archive.theaum.org/books/advaita/chandogya-upanishad-swami-gambhirananda-rk.pdf')
    },
    @{
        Dest = 'Advaita-Vedanta\BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf'
        Urls = @('http://michaelsudduth.com/wp-content/uploads/2013/01/Srimad-Bhagavad-Gita-Shankara-Bhashya-English.pdf')
    },
    @{
        Dest = 'Advaita-Vedanta\VC-Vivekachudamani-Madhavananda.pdf'
        Urls = @('https://www.vivekananda.net/PDFBooks/Vivekashudamani.pdf')
    },
    @{
        Dest = 'Advaita-Vedanta\DDV-Drig-Drishya-Viveka-Nikhilananda.pdf'
        Urls = @('https://vivekananda.net/PDFBooks/Others/DrgDrsyaViveka1931.pdf')
    },
    @{
        Dest = 'Advaita-Vedanta\MU-Mandukya-Upanishad-Gambhirananda.pdf'
        Urls = @('https://tomdas.com/wp-content/uploads/2023/09/mandukya-upanishad-with-shankaracharya-commentary-and-karika-of-gaudapada-english-trans.-by-swami-gambhirananda-advaita-ashrama-calcutta_text.pdf')
    },
    @{
        Dest = 'Advaita-Vedanta\Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf'
        Urls = @('https://archive.org/download/dli.bengal.10689.13276/10689.13276.pdf')
    },
    @{
        Dest = 'Advaita-Vedanta\BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf'
        Urls = @('https://estudantedavedanta.net/Brahma_Sutra_Swami_Gambhirananda.pdf')
    },
    @{
        Dest = 'Comparative-Philosophy\AV-Shankara-Stanford-Encyclopedia.html'
        Urls = @('https://plato.stanford.edu/entries/shankara/')
    },
    @{
        Dest = 'Comparative-Philosophy\SV-Vivekananda-Practical-Vedanta.pdf'
        Urls = @('https://www.vivekananda.net/PDFBooks/PracticalVedanta.pdf')
    },
    @{
        Dest = 'Science\Chalmers-1995-Facing-Up-to-the-Problem-of-Consciousness.pdf'
        Urls = @('https://consc.net/papers/facing.pdf')
    },
    @{
        Dest = 'Science\Nagel-1974-What-Is-It-Like-to-Be-a-Bat.pdf'
        Urls = @('https://www.cs.ox.ac.uk/activities/ieg/e-library/sources/nagel_bat.pdf')
    },
    @{
        Dest = 'Science\Strawson-2006-Realistic-Monism-Panpsychism.pdf'
        Urls = @('https://consc.net/event/reef/strawsonmonism.pdf')
    }
)

foreach ($item in $downloads) {
    $saved = $false
    foreach ($url in $item.Urls) {
        try {
            Save-Url -Url $url -Dest $item.Dest
            $saved = $true
            break
        }
        catch {
            Write-Warning "Failed $($item.Dest) from $url : $($_.Exception.Message)"
        }
    }
    if (-not $saved) {
        Write-Warning "All URLs failed for $($item.Dest)"
    }
}

Write-Host 'Reference download complete. See References\README.md and References\NOT-DOWNLOADED.md.'

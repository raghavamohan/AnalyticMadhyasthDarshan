# Downloads cited references for Studies into References/
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$RefRoot = Join-Path $Root 'References'

$dirs = @(
    $RefRoot,
    (Join-Path $RefRoot 'Madhyasth-Darshan'),
    (Join-Path $RefRoot 'Advaita-Vedanta'),
    (Join-Path $RefRoot 'Comparative-Philosophy'),
    (Join-Path $RefRoot 'Science'),
    (Join-Path $RefRoot 'Modern-Philosophy')
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
    },
    @{
        Dest = 'Modern-Philosophy\Frankish-2016-Illusionism-Theory-Consciousness.pdf'
        Urls = @('https://raw.githubusercontent.com/k0711/kf_articles/master/Frankish_Illusionism%20as%20a%20theory%20of%20consciousness_eprint.pdf')
    },
    @{
        Dest = 'Modern-Philosophy\Jarczewski-Riggs-2025-Socializing-Virtue-Epistemology.pdf'
        Urls = @('https://ruj.uj.edu.pl/bitstreams/5b802d21-6dd8-4450-8767-a715e4175d9b/download')
    },
    @{
        Dest = 'Modern-Philosophy\Limanowski-Blankenburg-2013-Minimal-Self-Models-Free-Energy-Principle.pdf'
        Urls = @('https://www.frontiersin.org/articles/10.3389/fnhum.2013.00547/pdf')
    },
    @{
        Dest = 'Modern-Philosophy\Melloni-et-al-2025-Adversarial-Testing-Consciousness-Theories.pdf'
        Urls = @('https://www.nature.com/articles/s41586-025-08888-1.pdf')
    },
    @{
        Dest = 'Modern-Philosophy\Piredda-2024-Tacitly-Situated-Self.pdf'
        Urls = @('https://link.springer.com/content/pdf/10.1007/s11245-024-10044-9.pdf')
    },
    @{
        Dest = 'Modern-Philosophy\Tufft-et-al-2024-Flow-Active-Inference.pdf'
        Urls = @('https://www.frontiersin.org/articles/10.3389/fpsyg.2024.1354719/pdf')
    },
    @{
        Dest = 'Modern-Philosophy\Wiese-2024-Artificial-Consciousness-Free-Energy-Principle.pdf'
        Urls = @('https://link.springer.com/content/pdf/10.1007/s11098-024-02182-y.pdf')
    },
    @{
        Dest = 'Modern-Philosophy\SEP-Concept-of-the-Aesthetic.html'
        Urls = @('https://plato.stanford.edu/entries/aesthetic-concept/')
    },
    @{
        Dest = 'Modern-Philosophy\SEP-Kant-Aesthetics-Teleology.html'
        Urls = @('https://plato.stanford.edu/entries/kant-aesthetics/')
    },
    @{
        Dest = 'Modern-Philosophy\SEP-Definition-of-Art.html'
        Urls = @('https://plato.stanford.edu/entries/art-definition/')
    },
    @{
        Dest = 'Modern-Philosophy\SEP-Environmental-Aesthetics.html'
        Urls = @('https://plato.stanford.edu/entries/environmental-aesthetics/')
    },
    @{
        Dest = 'Modern-Philosophy\SEP-Aesthetics-of-Everyday.html'
        Urls = @('https://plato.stanford.edu/entries/aesthetics-of-everyday/')
    },
    @{
        Dest = 'Comparative-Philosophy\Poorvam-Sadharanikarana-Rasa.html'
        Urls = @('https://poorvam.com/article.php?slug=s-dh-ra-kara-a-underlying-process-for-experiencing-rasa')
    },
    @{
        Dest = 'Modern-Philosophy\Whitehead-1929-Process-and-Reality.pdf'
        Urls = @('https://archive.org/download/processrealityes0000unse/processrealityes0000unse.pdf')
    },
    @{
        Dest = 'Modern-Philosophy\Russell-1921-The-Analysis-of-Mind.pdf'
        Urls = @('https://archive.org/download/analysisofmind00russ/analysisofmind00russ.pdf')
    },
    @{
        Dest = 'Modern-Philosophy\Mach-1914-The-Analysis-of-Sensations.pdf'
        Urls = @('https://archive.org/download/analysisofsensat00machuoft/analysisofsensat00machuoft.pdf')
    },
    @{
        Dest = 'Science\Ashtekar-Singh-2011-Loop-Quantum-Cosmology-Status-Report.pdf'
        Urls = @('https://arxiv.org/pdf/1108.0893.pdf')
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

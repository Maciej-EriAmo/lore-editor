# Weryfikacja artefaktów standalone po build_nuitka (Sprint A / release)
$ErrorActionPreference = "Stop"
# scripts/dev/<this> → repo root (dwa poziomy w górę od scripts/, trzy od pliku)
$Repo = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$Dist = Join-Path $Repo "dist"
$Folder = Join-Path $Dist "run_lore_editor.dist"
$Exe = Join-Path $Folder "run_lore_editor.exe"
$Zip = Join-Path $Dist "LoreEditor-0.7.9-win64.zip"

$fail = @()
function Ok($m) { Write-Host "[OK] $m" -ForegroundColor Green }
function Bad($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; $script:fail += $m }

if (-not (Test-Path $Exe)) { Bad "brak $Exe" } else {
    $mb = [math]::Round((Get-Item $Exe).Length / 1MB, 1)
    Ok "exe $mb MB"
}
if (-not (Test-Path $Zip)) { Bad "brak $Zip" } else {
    $mb = [math]::Round((Get-Item $Zip).Length / 1MB, 1)
    Ok "zip $mb MB"
}

$sjp = Join-Path $Folder "lore\data\sjp\pl_PL.dic"
if (Test-Path $sjp) { Ok "SJP pl_PL.dic" } else { Bad "brak SJP w paczce: $sjp" }

$enUi = Join-Path $Folder "lore\locales\en\ui.json"
if (Test-Path $enUi) { Ok "locales/en/ui.json" } else { Bad "brak EN locale: $enUi" }

$stale = Get-ChildItem $Dist -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^LoreEditor-0\.7\.[0-8]-win64\.(zip|exe)$' }
if ($stale) {
    Bad ("stare artefakty w dist/ (przenieś do archive/): " + ($stale.Name -join ", "))
} else {
    Ok "brak mylących ZIP/EXE < 0.7.9 w dist/"
}

# Product version z PE (gdy dostępne)
try {
    $vi = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($Exe)
    if ($vi.ProductVersion -match '0\.7\.9') { Ok "ProductVersion=$($vi.ProductVersion)" }
    else { Bad "ProductVersion=$($vi.ProductVersion) (oczekiwano 0.7.9*)" }
} catch {
    Write-Host "[WARN] nie odczytano FileVersionInfo: $_" -ForegroundColor Yellow
}

if ($fail.Count) {
    Write-Host "`nVERIFY_FAIL ($($fail.Count))" -ForegroundColor Red
    exit 1
}
Write-Host "`nVERIFY_OK" -ForegroundColor Green
exit 0

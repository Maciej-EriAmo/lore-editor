# Opcjonalne czcionki dla Lore Editor (Lexend, OpenDyslexic, Courier Prime)
# Uruchom jako administrator jeśli instalujesz do C:\Windows\Fonts

param(
    [string]$TargetDir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
)

$ErrorActionPreference = "Stop"
Write-Host "=== Lore Editor — czcionki opcjonalne ===" -ForegroundColor Cyan
Write-Host "Folder docelowy: $TargetDir"
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

$fonts = @(
    @{
        Name = "Lexend"
        Url  = "https://github.com/googlefonts/lexend/raw/main/fonts/ttf/Lexend-Regular.ttf"
        File = "Lexend-Regular.ttf"
    },
    @{
        Name = "OpenDyslexic"
        Url  = "https://github.com/antijingoist/opendyslexic/raw/master/compiled/OpenDyslexic-Regular.otf"
        File = "OpenDyslexic-Regular.otf"
    }
)

foreach ($f in $fonts) {
    $dest = Join-Path $TargetDir $f.File
    if (Test-Path $dest) {
        Write-Host "  OK  $($f.Name) — już jest" -ForegroundColor Green
        continue
    }
    Write-Host "  Pobieram $($f.Name)…"
    try {
        Invoke-WebRequest -Uri $f.Url -OutFile $dest -UseBasicParsing
        Write-Host "  Zapisano: $dest" -ForegroundColor Green
    } catch {
        Write-Warning "  Nie udało się pobrać $($f.Name): $_"
        Write-Host "  Pobierz ręcznie i zainstaluj z menu Wygląd w edytorze."
    }
}

Write-Host ""
Write-Host "Courier Prime: https://fonts.google.com/specimen/Courier+Prime" -ForegroundColor Yellow
Write-Host "Po instalacji uruchom ponownie Lore Editor." -ForegroundColor Cyan
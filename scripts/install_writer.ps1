# Instalator DEV (wymaga Pythona) — pip -e + skrót do run_lore_editor.py
# Dla pisarza bez Pythona: .\scripts\build_nuitka.ps1  potem  .\scripts\install_standalone.ps1
param(
    [string]$Project = "MojaPowiesc",
    # Docelowy folder powieści; domyślnie: <rodzic_repo>\dokumenty\lore
    [string]$ProjectDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "=== Lore Editor — instalacja ===" -ForegroundColor Cyan

Write-Host "Instalacja pakietów Python..."
pip install --upgrade "cynober-db>=8.0.1"
pip install --upgrade -e $RepoRoot

$Python = (Get-Command python).Source
$Launcher = Join-Path $RepoRoot "run_lore_editor.py"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Lore Editor.lnk"

# Domyślny katalog pracy: ../dokumenty/lore względem repo (albo -ProjectDir)
$DefaultWork = Join-Path (Split-Path -Parent $RepoRoot) "dokumenty\lore"
if (-not $ProjectDir) {
    $ProjectDir = $DefaultWork
}
New-Item -ItemType Directory -Force -Path $ProjectDir | Out-Null

$Wsh = New-Object -ComObject WScript.Shell
$Sc = $Wsh.CreateShortcut($ShortcutPath)
$Sc.TargetPath = $Python
$Sc.Arguments = "`"$Launcher`" --project-dir `"$ProjectDir`" --project $Project"
$Sc.WorkingDirectory = $ProjectDir
$Sc.Description = "Lore Editor"
$Sc.Save()

Write-Host ""
Write-Host "Gotowe!" -ForegroundColor Green
Write-Host "  Skrót: $ShortcutPath"
Write-Host "  Katalog pracy: $ProjectDir"
Write-Host "  lore-editor                          # domyslnie ../dokumenty/lore"
Write-Host "  lore-editor --project-dir <folder>   # wskazany katalog"
Write-Host "  cd <folder-z-.lore-project> && lore-editor"
Write-Host "  Przy 1. uruchomieniu: .lore-history/ (backup — nie usuwaj)"
Write-Host "  Kopia zapasowa: caly folder + .lore-history/"
Write-Host "  Sieć (opcjonalnie): cynober-server — protokol Karmazyn, nie zwykle TCP/HTTP (port 8080)"
Write-Host "  Pomoc w aplikacji: F1 -> Siec: Karmazyn i Cynober DB"
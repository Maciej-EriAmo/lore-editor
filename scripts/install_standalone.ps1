# Instalacja samodzielnej aplikacji Lore Editor (bez Pythona na maszynie docelowej)
# Wymaga wczesniej: .\scripts\build_nuitka.ps1
# Kopiuje dist\run_lore_editor.dist -> %LOCALAPPDATA%\LoreEditor i tworzy skrot na pulpicie.
param(
    [string]$Source = "",
    [string]$InstallDir = "",
    [string]$ProjectDir = "",
    [string]$Project = "lore"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not $Source) {
    $Source = Join-Path $RepoRoot "dist\run_lore_editor.dist"
}
if (-not $InstallDir) {
    $InstallDir = Join-Path $env:LOCALAPPDATA "LoreEditor"
}
if (-not $ProjectDir) {
    $ProjectDir = Join-Path $env:USERPROFILE "dokumenty\lore"
}

Write-Host "=== Lore Editor - instalacja standalone ===" -ForegroundColor Cyan

if (-not (Test-Path $Source)) {
    throw "Brak folderu buildu: $Source`nUruchom najpierw: .\scripts\build_nuitka.ps1"
}

$ExeSrc = Get-ChildItem -Path $Source -Filter "run_lore_editor.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ExeSrc) {
    $ExeSrc = Get-ChildItem -Path $Source -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
}
if (-not $ExeSrc) {
    throw "Brak pliku .exe w $Source"
}

Write-Host "Zrodlo:  $Source"
Write-Host "Cel:     $InstallDir"
Write-Host "Powiesc: $ProjectDir"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $ProjectDir | Out-Null

Write-Host "Kopiowanie plikow aplikacji..."
& robocopy $Source $InstallDir /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
$rc = $LASTEXITCODE
if ($rc -ge 8) { throw "robocopy failed with code $rc" }

$ExePath = Join-Path $InstallDir $ExeSrc.Name
if (-not (Test-Path $ExePath)) {
    throw "Po kopiowaniu brak exe: $ExePath"
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Lore Editor.lnk"
$Wsh = New-Object -ComObject WScript.Shell
$Sc = $Wsh.CreateShortcut($ShortcutPath)
$Sc.TargetPath = $ExePath
$Sc.Arguments = "--project-dir `"$ProjectDir`" --project $Project"
$Sc.WorkingDirectory = $ProjectDir
$Sc.Description = "Lore Editor - edytor lore (samodzielna aplikacja)"
$IconCandidate = Join-Path $InstallDir "run_lore_editor.exe"
if (Test-Path $IconCandidate) { $Sc.IconLocation = "$IconCandidate,0" }
$Sc.Save()

$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
New-Item -ItemType Directory -Force -Path $StartMenu | Out-Null
$StartLnk = Join-Path $StartMenu "Lore Editor.lnk"
Copy-Item $ShortcutPath $StartLnk -Force

$Info = @{
    installed_at = (Get-Date).ToString("o")
    source       = $Source
    exe          = $ExePath
    project_dir  = $ProjectDir
} | ConvertTo-Json
Set-Content -Path (Join-Path $InstallDir "install.json") -Value $Info -Encoding UTF8

Write-Host ""
Write-Host "Gotowe!" -ForegroundColor Green
Write-Host "  Aplikacja:  $ExePath"
Write-Host "  Powiesc:    $ProjectDir"
Write-Host "  Pulpit:     $ShortcutPath"
Write-Host "  Menu Start: $StartLnk"
Write-Host ""
Write-Host "Uruchom skrot Lore Editor - nie wymaga Pythona."
Write-Host "Pliki wynikowe (rozdzialy, .kafd, historia) trafiaja do folderu powiesci,"
Write-Host "nie do katalogu instalacji."

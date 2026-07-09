# Instalator Lore Editor dla pisarza — Cynober + skrót pulpitu
param(
    [string]$Project = "MojaPowiesc"
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

$Wsh = New-Object -ComObject WScript.Shell
$Sc = $Wsh.CreateShortcut($ShortcutPath)
$Sc.TargetPath = $Python
$Sc.Arguments = "`"$Launcher`" --project $Project"
$Sc.WorkingDirectory = $RepoRoot
$Sc.Description = "Lore Editor"
$Sc.Save()

Write-Host ""
Write-Host "Gotowe!" -ForegroundColor Green
Write-Host "  Skrót: $ShortcutPath"
Write-Host "  Z folderu projektu: cd <folder> && lore-editor"
Write-Host "  Lub utwórz .lore-project z linią: name=$Project"
Write-Host "  Serwer zespołu: cynober-server  (port 8080)"
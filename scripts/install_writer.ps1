# Instalator Lore Editor dla pisarza — Cynober + AstraEdit + skrót pulpitu
param(
    [string]$Project = "MojaPowiesc"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VendorDir = Join-Path $RepoRoot "vendor\Astraedit"
$AstraRepo = "https://github.com/Maciej-EriAmo/Astraedit.git"

Write-Host "=== Lore Editor — instalacja ===" -ForegroundColor Cyan

Write-Host "Instalacja pakietów Python..."
pip install --upgrade "cynober-db>=8.0.1"
pip install --upgrade -e $RepoRoot

if (-not (Test-Path (Join-Path $VendorDir "Astraedit-4.5.py"))) {
    Write-Host "Klonowanie AstraEdit do vendor..."
    New-Item -ItemType Directory -Force -Path (Split-Path $VendorDir) | Out-Null
    if (Test-Path $VendorDir) {
        Remove-Item -Recurse -Force $VendorDir
    }
    git clone --depth 1 $AstraRepo $VendorDir
} else {
    Write-Host "AstraEdit już w vendor — pomijam klon."
}

$Python = (Get-Command python).Source
$Launcher = Join-Path $RepoRoot "run_lore_editor.py"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Lore Editor.lnk"

$Wsh = New-Object -ComObject WScript.Shell
$Sc = $Wsh.CreateShortcut($ShortcutPath)
$Sc.TargetPath = $Python
$Sc.Arguments = "`"$Launcher`" --project $Project --astraedit"
$Sc.WorkingDirectory = $RepoRoot
$Sc.Description = "Lore Editor + AstraEdit"
$Sc.Save()

Write-Host ""
Write-Host "Gotowe!" -ForegroundColor Green
Write-Host "  Skrót: $ShortcutPath"
Write-Host "  Standalone: python run_lore_editor.py --project $Project"
Write-Host "  AstraEdit:  python run_lore_editor.py --project $Project --astraedit"
Write-Host "  Serwer zespołu: cynober-server  (port 8080)"
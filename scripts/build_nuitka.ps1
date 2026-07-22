# Budowa samodzielnej aplikacji Lore Editor (Nuitka standalone)
# Wymaga: Python 3.10+, pip install cynober-db python-docx spylls
# Wynik: dist\run_lore_editor.dist\  oraz  dist\LoreEditor-<ver>-win64.zip
param(
    [switch]$OneFile,
    [switch]$SkipZip,
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dist = Join-Path $RepoRoot "dist"
$Entry = Join-Path $RepoRoot "run_lore_editor.py"
$Pyproject = Join-Path $RepoRoot "pyproject.toml"

# Wersja z pyproject.toml
$Version = "0.0.0"
if (Test-Path $Pyproject) {
    $m = Select-String -Path $Pyproject -Pattern 'version\s*=\s*"([^"]+)"' | Select-Object -First 1
    if ($m) { $Version = $m.Matches[0].Groups[1].Value }
}
$FileVersion = if ($Version -match '^\d+\.\d+\.\d+') { "$Version.0" } else { "0.0.0.0" }

Write-Host "=== Lore Editor $Version — Nuitka standalone ===" -ForegroundColor Cyan

# Zależności runtime + tool
python -m pip install --upgrade "nuitka" "ordered-set" "zstandard" "cynober-db>=8.0.1" "python-docx>=1.1.0" "spylls>=0.1.7" 2>&1 | Out-Null

# Moduły Cynober / Karmazyn (często dynamiczne — jawny include)
$modules = @(
    "cynober_worlds", "cynober_world_shards", "cynober_auto_flush",
    "cynober_replicate", "cynober_client", "cynober_rpc", "cynober_client_config",
    "cynober_query_engine", "cynober_lambda_bridge", "cynober_ops",
    "karmazyn_kernel", "karmazyn_substrate", "karmazyn_store", "karmazyn_kafd",
    "karmazyn_atom", "karmazyn_atomstore", "karmazyn_exec", "karmazyn_proca"
)

$include = @(
    "--include-package=lore",
    "--include-package-data=lore",
    "--include-package=spylls",
    "--include-package=docx",
    "--include-package=lxml",
    "--include-data-dir=$(Join-Path $RepoRoot 'lore\data')=lore/data"
)
$include += $modules | ForEach-Object { "--include-module=$_" }

$Icon = Join-Path $RepoRoot "vendor\Astraedit\astraedit.ico"
$iconArgs = @()
if (Test-Path $Icon) {
    $iconArgs = @("--windows-icon-from-ico=$Icon")
}

$nuitkaArgs = @(
    "-m", "nuitka",
    "--standalone",
    "--assume-yes-for-downloads",
    "--enable-plugin=tk-inter",
    "--output-dir=$Dist",
    "--remove-output",
    "--company-name=EriAmo",
    "--product-name=Lore Editor",
    "--file-description=Lore Editor — edytor lore dla pisarzy",
    "--file-version=$FileVersion",
    "--product-version=$FileVersion",
    "--copyright=MIT",
    "--windows-console-mode=disable"
) + $iconArgs + $include + @($Entry)

if ($OneFile) {
    # Onefile: ten sam zestaw flag, inny tryb
    $nuitkaArgs = @("-m", "nuitka", "--onefile") + $nuitkaArgs[2..($nuitkaArgs.Length - 1)]
}

Write-Host "Nuitka start — może potrwać 5–20 min..."
Push-Location $RepoRoot
try {
    & python @nuitkaArgs
    if ($LASTEXITCODE -ne 0) { throw "Nuitka exit $LASTEXITCODE" }
} finally {
    Pop-Location
}

$DistFolder = Join-Path $Dist "run_lore_editor.dist"
$exe = Get-ChildItem -Path $Dist -Filter "run_lore_editor.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $exe -and (Test-Path $DistFolder)) {
    $exe = Get-ChildItem -Path $DistFolder -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
}

if ($exe) {
    $mb = [math]::Round($exe.Length / 1MB, 1)
    Write-Host "EXE: $($exe.FullName) ($mb MB)" -ForegroundColor Green
} elseif (Test-Path $DistFolder) {
    Write-Host "Folder: $DistFolder" -ForegroundColor Green
} else {
    throw "Brak wyniku w $Dist"
}

# ZIP do dystrybucji (cały folder .dist — wymagany przy --standalone)
if (-not $SkipZip -and -not $OneFile -and (Test-Path $DistFolder)) {
    $ZipName = "LoreEditor-$Version-win64.zip"
    $ZipPath = Join-Path $Dist $ZipName
    if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
    Write-Host "Pakowanie $ZipName ..."
    Compress-Archive -Path (Join-Path $DistFolder "*") -DestinationPath $ZipPath -CompressionLevel Optimal
    $zmb = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
    Write-Host "ZIP: $ZipPath ($zmb MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dla pisarza (bez Pythona):" -ForegroundColor Cyan
    Write-Host "  1. Rozpakuj ZIP albo: .\\scripts\\install_standalone.ps1"
    Write-Host "  2. Skrót pulpitu → exe (powieść w %USERPROFILE%\\dokumenty\\lore)"
}

if ($Install) {
    $installer = Join-Path $RepoRoot "scripts\install_standalone.ps1"
    & $installer
}

Write-Host "Gotowe." -ForegroundColor Green

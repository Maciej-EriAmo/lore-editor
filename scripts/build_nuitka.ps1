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

Write-Host "=== Lore Editor $Version - Nuitka standalone ===" -ForegroundColor Cyan

# pip pisze ostrzezenia na stderr - nie przerywaj buildu
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
python -m pip install --upgrade "nuitka" "ordered-set" "zstandard" "cynober-db>=8.0.1" "python-docx>=1.1.0" "spylls>=0.1.7"
if ($LASTEXITCODE -ne 0) {
    $ErrorActionPreference = $prevEap
    throw "pip install failed: $LASTEXITCODE"
}
$ErrorActionPreference = $prevEap

$modules = @(
    "cynober_worlds", "cynober_world_shards", "cynober_auto_flush",
    "cynober_replicate", "cynober_client", "cynober_rpc", "cynober_client_config",
    "cynober_query_engine", "cynober_lambda_bridge", "cynober_ops",
    "karmazyn_kernel", "karmazyn_substrate", "karmazyn_store", "karmazyn_kafd",
    "karmazyn_atom", "karmazyn_atomstore", "karmazyn_exec", "karmazyn_proca"
)

$dataDir = Join-Path $RepoRoot "lore\data"
$include = @(
    "--include-package=lore",
    "--include-package-data=lore",
    "--include-package=spylls",
    "--include-package=docx",
    "--include-package=lxml",
    "--include-data-dir=${dataDir}=lore/data"
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
    "--file-description=Lore Editor - edytor lore dla pisarzy",
    "--file-version=$FileVersion",
    "--product-version=$FileVersion",
    "--copyright=MIT",
    "--windows-console-mode=disable"
) + $iconArgs + $include + @($Entry)

if ($OneFile) {
    $nuitkaArgs = @("-m", "nuitka", "--onefile") + $nuitkaArgs[2..($nuitkaArgs.Length - 1)]
}

Write-Host "Nuitka start - moze potrwac 5-20 min..."
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
    Write-Host ("EXE: {0} ({1} MB)" -f $exe.FullName, $mb) -ForegroundColor Green
} elseif (Test-Path $DistFolder) {
    Write-Host "Folder: $DistFolder" -ForegroundColor Green
} else {
    throw "Brak wyniku w $Dist"
}

if (-not $SkipZip -and -not $OneFile -and (Test-Path $DistFolder)) {
    $ZipName = "LoreEditor-$Version-win64.zip"
    $ZipPath = Join-Path $Dist $ZipName
    if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
    Write-Host "Pakowanie $ZipName ..."
    Compress-Archive -Path (Join-Path $DistFolder "*") -DestinationPath $ZipPath -CompressionLevel Optimal
    $zmb = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
    Write-Host ("ZIP: {0} ({1} MB)" -f $ZipPath, $zmb) -ForegroundColor Green
    Write-Host ""
    Write-Host "Dla pisarza (bez Pythona):" -ForegroundColor Cyan
    Write-Host "  1. Rozpakuj ZIP albo: .\scripts\install_standalone.ps1"
    Write-Host "  2. Skrot pulpitu -> exe (powiesc w %USERPROFILE%\dokumenty\lore)"
}

if ($Install) {
    $installer = Join-Path $RepoRoot "scripts\install_standalone.ps1"
    & $installer
}

Write-Host "Gotowe." -ForegroundColor Green

# Budowa standalone exe - Lore Editor
# Wymaga: pip install nuitka cynober-db
param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dist = Join-Path $RepoRoot "dist"
$Entry = Join-Path $RepoRoot "run_lore_editor.py"

Write-Host "=== Lore Editor - Nuitka ===" -ForegroundColor Cyan
python -m pip install --upgrade nuitka ordered-set zstandard 2>&1 | Out-Null

$modules = @(
    "lore",
    "cynober_worlds", "cynober_world_shards", "cynober_auto_flush",
    "cynober_replicate", "cynober_client", "cynober_rpc", "cynober_client_config",
    "cynober_query_engine", "cynober_lambda_bridge", "cynober_ops",
    "karmazyn_kernel", "karmazyn_substrate", "karmazyn_store", "karmazyn_kafd",
    "karmazyn_atom", "karmazyn_atomstore", "karmazyn_exec", "karmazyn_proca"
)

$include = @("--include-package=lore")
$include += $modules | Where-Object { $_ -ne "lore" } | ForEach-Object { "--include-module=$_" }

$nuitkaArgs = @(
    "-m", "nuitka",
    "--standalone",
    "--assume-yes-for-downloads",
    "--enable-plugin=tk-inter",
    "--output-dir=$Dist",
    "--remove-output",
    "--company-name=LoreEditor",
    "--product-name=Lore Editor",
    "--file-version=0.4.0.0",
    "--product-version=0.4.0.0",
    "--windows-console-mode=disable"
) + $include + @($Entry)

if ($OneFile) {
    $nuitkaArgs = @("-m", "nuitka", "--onefile") + $nuitkaArgs[2..($nuitkaArgs.Length - 1)]
}

Write-Host 'Nuitka start - moze potrwac 5-15 min...'
Push-Location $RepoRoot
try {
    & python @nuitkaArgs
    if ($LASTEXITCODE -ne 0) { throw "Nuitka exit $LASTEXITCODE" }
} finally {
    Pop-Location
}

$exe = Get-ChildItem -Path $Dist -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($exe) {
    $mb = [math]::Round($exe.Length / 1MB, 1)
    Write-Host "Gotowe: $($exe.FullName) - $mb MB" -ForegroundColor Green
} else {
    $bin = Join-Path $Dist "run_lore_editor.dist"
    if (Test-Path $bin) {
        Write-Host "Gotowe folder: $bin" -ForegroundColor Green
    } else {
        throw "Brak wyniku w $Dist"
    }
}
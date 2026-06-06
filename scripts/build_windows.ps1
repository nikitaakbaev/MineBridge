$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvDir = if ($env:MINEBRIDGE_BUILD_VENV) {
    $env:MINEBRIDGE_BUILD_VENV
} else {
    Join-Path $RootDir ".venv-build"
}
$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }

Set-Location $RootDir

& $PythonBin -m venv $VenvDir
& (Join-Path $VenvDir "Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $VenvDir "Scripts\python.exe") -m pip install -e ".[packaging]"
& (Join-Path $VenvDir "Scripts\python.exe") -m PyInstaller --noconfirm --clean "packaging\minebridge-frp.spec"

Write-Host ""
Write-Host "Windows build is ready: $RootDir\dist\MineBridge FRP\MineBridge FRP.exe"

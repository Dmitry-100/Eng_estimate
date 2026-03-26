$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

python -m pip install -r requirements-windows-build.txt
pyinstaller --clean EngEstimate.spec

Write-Host ""
Write-Host "Build complete."
Write-Host "EXE: dist\EngEstimate.exe"

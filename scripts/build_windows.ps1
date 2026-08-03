$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path .venv)) {
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller==6.10.0

if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist) { Remove-Item dist -Recurse -Force }

pyinstaller --noconfirm --clean --windowed --name ValorantDodgeAdvisor --add-data "web;web" run_desktop.py

Write-Host "Built Windows app at dist\ValorantDodgeAdvisor\ValorantDodgeAdvisor.exe"
Write-Host "To generate installer, run Inno Setup with installer\windows.iss"

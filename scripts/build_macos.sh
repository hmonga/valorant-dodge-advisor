#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller==6.10.0

rm -rf build dist
pyinstaller desktop.spec --noconfirm

mkdir -p dist/release
hdiutil create -volname "Valorant Dodge Advisor" -srcfolder "dist/Valorant Dodge Advisor.app" -ov -format UDZO "dist/release/ValorantDodgeAdvisor.dmg"

echo "Build complete: dist/release/ValorantDodgeAdvisor.dmg"

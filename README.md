# Valorant Dodge Advisor

Desktop-ready live lobby scout + dodge advisor. It reads your current agent-select /
in-game lobby, pulls each player's rank and recent form, flags likely smurfs,
estimates team win probability, and gives a **DODGE / STAY** verdict.

## Download App (No Clone Needed)

Download the latest installer directly from GitHub Releases:

- Windows installer (.exe): [Download ValorantDodgeAdvisor-Setup.exe](https://github.com/hmonga/valorant-dodge-advisor/releases/latest/download/ValorantDodgeAdvisor-Setup.exe)
- macOS installer (.dmg): [Download ValorantDodgeAdvisor.dmg](https://github.com/hmonga/valorant-dodge-advisor/releases/latest/download/ValorantDodgeAdvisor.dmg)

If your browser blocks the direct link, open the [latest release page](https://github.com/hmonga/valorant-dodge-advisor/releases/latest) and download from Assets.

## How it works

Same approach as Tracker.gg-style overlays:

1. `valclient` reads the Valorant **lockfile** and authenticates to the **local client API**.
2. It calls Riot's internal **pregame** (agent select — your team only) and **coregame**
   (load-in — all 10 players) endpoints to get live PUUIDs.
3. Per player it pulls rank (`mmr`) and recent competitive form.
4. Smurf heuristic + win-probability model produce the verdict.

> ⚠️ These internal endpoints are **undocumented and unofficial**. Reading live game
> state is a Riot ToS gray area — tolerated for read-only overlays, but at your own
> risk. This app is strictly read-only.

## Product Features

- Native desktop window (no manual browser tab needed)
- Overlay-style companion mode (`--overlay`) for always-on-top usage
- Built-in settings panel for region, mock/live mode, and refresh interval
- Local read-only Riot client integration via `valclient`
- Mock mode for offline usage and demos

## Quick Start (Desktop)

```bash
./scripts/run_desktop.sh
```

This script creates a venv, installs dependencies, launches the backend, and opens
the native desktop window.

## Manual Run

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_desktop.py
python run_desktop.py --overlay
```

## Run In Browser (Dev Mode)

```bash
uvicorn app.server:app --port 8000
```

Open [http://localhost:8000](http://localhost:8000)

## Live Mode

Launch Valorant, then in app settings:

- disable `Use Mock Data`
- set your region (`na`, `eu`, `ap`, `kr`, etc.)

The verdict fills in with real win % once you load into the map (enemies are hidden
during agent select).

## Build macOS Installer (.dmg)

```bash
./scripts/build_macos.sh
```

Output: `dist/release/ValorantDodgeAdvisor.dmg`

## Windows Installer (.exe)

Local build:

```powershell
./scripts/build_windows.ps1
```

CI release build:

- Workflow: `.github/workflows/release-windows.yml`
- Trigger: publish a GitHub Release (or run manually via Actions)
- Output: `ValorantDodgeAdvisor-Setup.exe` attached to the GitHub Release

End-user install flow:

1. Open your GitHub repository Releases page
2. Click latest release
3. Download `ValorantDodgeAdvisor-Setup.exe`
4. Run installer and launch app from Start Menu

## Architecture

- `app/desktop.py`: Desktop launcher (native window + embedded server)
- `app/server.py`: FastAPI service and UI/settings endpoints
- `app/analyze.py`: Core analysis pipeline and verdict logic
- `web/index.html`: Product UI dashboard
- `desktop.spec`: PyInstaller build spec for app bundling

## Next steps

- Add auto-update flow (Sparkle or custom updater)
- Add Windows installer and optional Overwolf-based overlay integration
- Replace heuristic `winprob` with calibrated model from outcome logs

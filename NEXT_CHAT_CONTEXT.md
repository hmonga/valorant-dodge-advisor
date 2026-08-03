# Copilot Handoff Context (Valorant Dodge Advisor)

Last updated: 2026-08-03  
Repository: [hmonga/valorant-dodge-advisor](https://github.com/hmonga/valorant-dodge-advisor)  
Current branch: main  
Latest commit: 0aa974a

## How to use this file in your next Copilot chat

Paste this at the start of a new chat:

"Read NEXT_CHAT_CONTEXT.md first, then continue development from current state. Do not re-scaffold the project. Preserve existing architecture and release workflow."

## Product intent

This project is a desktop-first Valorant pre-game decision app that helps users decide whether to play or dodge using live lobby data.

Primary UX goals:

- One-click install experience via GitHub Releases
- Open app and use immediately
- Startup order should not matter (app first or Valorant first)
- Clear troubleshooting for non-technical users
- Explainable recommendations, not black-box outputs

## Current app status

Implemented and shipped:

- Native desktop launcher using local FastAPI backend + pywebview
- Overlay-style companion window mode
- Persistent settings (region, mock/live, refresh interval, queue + RR economics)
- Live Riot client connection with auto-reconnect behavior
- Guided troubleshooting panel with fallback to mock mode
- EV-based recommendation engine with confidence + risk breakdown
- Team composition intelligence (role coverage + advice)
- Enemy threat shortlist
- Local learning loop (recommendation snapshots + optional outcome logging)
- Setup check endpoint and update-check endpoint
- GitHub Actions workflow for Windows installer release asset
- Inno Setup script for Windows installer
- Updated black/red RR Saviour logo and simplified brand header

## Key architecture

Backend:

- app/server.py: API surface and HTML serving
- app/analyze.py: Orchestration and payload shaping
- app/riot_client.py: valclient wrapper, status classification, reconnect support
- app/decision.py: EV model, confidence, key risks, recommendations
- app/roles.py: Agent role map and composition scoring
- app/history.py: Local history logging + trend summaries + outcome logging
- app/settings_store.py: Persistent local settings
- app/update_check.py: GitHub latest release checker
- app/winprob.py: Base win probability heuristic
- app/smurf.py: Smurf risk heuristic

Frontend:

- web/index.html: Single-page desktop UI with settings, diagnostics, EV/risk panels, comp intelligence, threat panel, and outcome logging buttons
- web/rr-saviour.svg: Current brand mark (RR + Saviour only)

Desktop/runtime:

- run_desktop.py: main desktop entrypoint
- app/desktop.py: starts server and opens desktop window
- desktop.spec: PyInstaller spec

Release/build:

- scripts/build_macos.sh: local macOS build + DMG output
- scripts/build_windows.ps1: local Windows executable build
- installer/windows.iss: Windows installer definition
- .github/workflows/release-windows.yml: CI build + release asset attach

## Current endpoints

- GET /api/analyze
- GET /api/health
- GET /api/setup-check
- GET /api/stats
- POST /api/outcome
- GET /api/update-check
- GET /api/settings
- POST /api/settings
- GET /
- GET /logo.svg
- GET /rr-saviour.svg

## Runtime settings schema (stored locally)

settings file path: ~/.valorant-dodge-advisor/settings.json

Current keys:

- region
- mock
- refresh_seconds
- queue_type
- rr_gain_on_win
- rr_loss_on_loss
- dodge_rr_penalty
- start_on_login
- notify_strong_dodge
- auto_check_updates

## Current recommendation behavior

Recommendation values:

- PLAY
- LEAN_DODGE
- DODGE
- WAIT

Decision factors currently used:

- win probability
- RR economics (gain/loss/dodge penalty)
- smurf risk differential
- role conflict/composition score
- rank pressure
- fatigue trend from local history
- uncertainty penalties for missing/weak signals

## Installer and release flow (user-facing)

User path:

1. Open Releases page
1. Download installer
1. Install
1. Launch app

Direct links expected in README:

- Windows: releases/latest/download/ValorantDodgeAdvisor-Setup.exe
- macOS: releases/latest/download/ValorantDodgeAdvisor.dmg

## Known limitations and reality checks

- True in-game injected overlay is not implemented; current overlay mode is companion-style always-on-top window.
- winprob and smurf are still heuristic; model calibration requires real outcomes over time.
- Auto-update install flow is not yet full silent updater; currently update check opens release URL.
- Riot internal API usage is unofficial and can break if upstream behavior changes.

## High-priority next improvements

1. Stabilize branding and UI consistency

- Ensure logo renders crisply at all scales and dark/light backgrounds if themes are introduced.

1. Strengthen data quality and calibration

- Build offline calibration script from history + outcome logs.
- Add confidence calibration metrics and drift warnings.

1. Improve supportability

- Add export diagnostics bundle button (health + settings + recent non-sensitive logs).
- Add clearer error categories in UI badges.

1. Improve release quality

- Add version injection at build time and display in UI.
- Add code signing + notarization workflow notes for production release.

## Safety and product constraints

- App is read-only toward game state.
- Avoid writing features that automate gameplay or input.
- Keep local user data minimal and transparent.

## Quick start commands (dev)

- Desktop run: ./scripts/run_desktop.sh
- macOS build: ./scripts/build_macos.sh
- Python compile sanity: python3 -m compileall app run_desktop.py

## If you are the next Copilot instance

Do this first:

1. Read this file fully.
1. Read README.md.
1. Inspect app/analyze.py and web/index.html before proposing architecture changes.
1. Preserve release workflow and existing endpoint contracts unless change is explicitly requested.

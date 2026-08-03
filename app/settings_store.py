"""Persistent settings for desktop-friendly app behavior."""

from __future__ import annotations

import json
from pathlib import Path

from . import config

_APP_DIR = Path.home() / ".valorant-dodge-advisor"
_SETTINGS_FILE = _APP_DIR / "settings.json"


def _defaults():
	return {
		"region": config.REGION,
		"mock": config.MOCK,
		"refresh_seconds": 5,
		"queue_type": "competitive",
		"rr_gain_on_win": 20,
		"rr_loss_on_loss": 20,
		"dodge_rr_penalty": 3,
		"start_on_login": False,
		"notify_strong_dodge": True,
		"auto_check_updates": True,
	}


def load_settings():
    settings = _defaults()
    try:
        if _SETTINGS_FILE.exists():
            disk = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(disk, dict):
                settings.update(disk)
    except Exception:
        # Corrupt or unreadable settings should not break app startup.
        pass

    config.apply_runtime_settings(region=settings.get("region"), mock=settings.get("mock"))
    return settings


def save_settings(settings):
    merged = _defaults()
    merged.update(settings or {})

    _APP_DIR.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(merged, indent=2), encoding="utf-8")

    config.apply_runtime_settings(region=merged.get("region"), mock=merged.get("mock"))
    return merged


def settings_path():
	return str(_SETTINGS_FILE)

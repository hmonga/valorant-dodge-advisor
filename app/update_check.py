"""Simple app update checker against GitHub releases."""

from __future__ import annotations

import requests

LATEST_RELEASE_API = "https://api.github.com/repos/hmonga/valorant-dodge-advisor/releases/latest"


def check_latest_release(current_version="0.1.0"):
    try:
        r = requests.get(LATEST_RELEASE_API, timeout=4)
        r.raise_for_status()
        data = r.json()
        latest_tag = str(data.get("tag_name") or "").lstrip("v")
        html_url = data.get("html_url")
        return {
            "ok": True,
            "current_version": current_version,
            "latest_version": latest_tag or "unknown",
            "update_available": bool(latest_tag and latest_tag != current_version),
            "release_url": html_url,
        }
    except Exception as exc:
        return {
            "ok": False,
            "current_version": current_version,
            "latest_version": None,
            "update_available": False,
            "release_url": "https://github.com/hmonga/valorant-dodge-advisor/releases/latest",
            "error": str(exc),
        }

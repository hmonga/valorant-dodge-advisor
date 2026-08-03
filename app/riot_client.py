"""Thin wrapper around valclient, which reads the Valorant lockfile, authenticates
to the local client API, and calls Riot's internal pregame/coregame/mmr endpoints.

These endpoints are undocumented and unofficial. Reading live game state is a Riot
ToS gray area (tolerated for read-only overlays, but at your own risk). This wrapper
is read-only: it never sends inputs or modifies game state.
"""

from . import config

_client = None
_last_status = {
    "code": "idle",
    "message": "Waiting to connect.",
    "details": "",
}


def _set_status(code, message, details=""):
    global _last_status
    _last_status = {"code": code, "message": message, "details": details}


def _classify_activation_error(exc):
    text = str(exc).lower()
    if "region" in text and ("invalid" in text or "unsupported" in text):
        return (
            "bad_region",
            "Configured region may be invalid. Update region in app settings.",
        )
    if "lockfile" in text or "not found" in text:
        return (
            "no_lockfile",
            "Valorant client lockfile not found. Launch Riot Client and Valorant.",
        )
    if "refused" in text or "timed out" in text or "timeout" in text:
        return (
            "client_unreachable",
            "Could not reach local Valorant client API yet.",
        )
    return (
        "activation_failed",
        "Could not connect to the local Valorant client.",
    )


def get_client(return_status=False):
    """Return an activated valclient Client, or None if the game isn't running."""
    global _client
    if _client is not None:
        _set_status("connected", "Connected to local Valorant client.")
        return (_client, dict(_last_status)) if return_status else _client
    try:
        from valclient.client import Client
    except ImportError:
        _set_status(
            "missing_dependency",
            "Missing runtime dependency 'valclient'. Reinstall the app or dependencies.",
        )
        return (None, dict(_last_status)) if return_status else None
    try:
        client = Client(region=config.REGION)
        client.activate()
        _client = client
        _set_status("connected", "Connected to local Valorant client.")
        return (_client, dict(_last_status)) if return_status else _client
    except Exception as exc:
        code, message = _classify_activation_error(exc)
        _set_status(code, message, str(exc))
        return (None, dict(_last_status)) if return_status else None


def reset_client():
    global _client
    _client = None


def get_client_status():
    return dict(_last_status)

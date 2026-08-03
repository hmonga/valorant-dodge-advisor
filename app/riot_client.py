"""Thin wrapper around valclient, which reads the Valorant lockfile, authenticates
to the local client API, and calls Riot's internal pregame/coregame/mmr endpoints.

These endpoints are undocumented and unofficial. Reading live game state is a Riot
ToS gray area (tolerated for read-only overlays, but at your own risk). This wrapper
is read-only: it never sends inputs or modifies game state.
"""

from . import config

_client = None


def get_client():
    """Return an activated valclient Client, or None if the game isn't running."""
    global _client
    if _client is not None:
        return _client
    try:
        from valclient.client import Client
    except ImportError:
        return None
    try:
        client = Client(region=config.REGION)
        client.activate()
        _client = client
        return client
    except Exception:
        return None


def reset_client():
    global _client
    _client = None

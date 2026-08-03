"""Recent competitive 'form' per player, derived from ranked-rating swings.

We can't get exact W/L cheaply, so we treat a positive RankedRatingEarned as a
win-ish result. It's a proxy, not ground truth — good enough for a form signal.
"""

from . import config


def recent_form(client, puuid):
    """Return {'games': n, 'winrate': float|None, 'rr_trend': int}."""
    try:
        updates = client.fetch_competitive_updates(puuid=puuid)
    except Exception:
        return {"games": 0, "winrate": None, "rr_trend": 0}

    matches = (updates or {}).get("Matches", [])[: config.RECENT_MATCHES]
    if not matches:
        return {"games": 0, "winrate": None, "rr_trend": 0}

    wins = sum(1 for m in matches if m.get("RankedRatingEarned", 0) > 0)
    rr_trend = sum(m.get("RankedRatingEarned", 0) for m in matches)
    return {
        "games": len(matches),
        "winrate": wins / len(matches),
        "rr_trend": rr_trend,
    }

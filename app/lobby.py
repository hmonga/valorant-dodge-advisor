"""Read the current live lobby (agent select -> pregame, or loading/in-game ->
coregame) and normalize every player into a common shape the analyzer can use.

Notes on what Riot exposes:
- pregame (agent select): you can only see YOUR team. Enemies are hidden.
- coregame (load-in / in-game): all 10 players, split by TeamID.
"""

from .agents import agent_name


def _identity(player):
    ident = player.get("PlayerIdentity", {}) or {}
    return {
        "account_level": ident.get("AccountLevel", 0),
        "hidden_level": bool(ident.get("HideAccountLevel")),
        "incognito": bool(ident.get("Incognito")),
    }


def _tier_from_mmr(mmr):
    """Best-effort current competitive tier from a fetch_mmr() payload."""
    if not mmr:
        return 0
    latest = mmr.get("LatestCompetitiveUpdate") or {}
    tier = latest.get("TierAfterUpdate")
    if tier:
        return tier
    # Fall back to the highest tier seen across seasons.
    best = 0
    skills = (mmr.get("QueueSkills") or {}).get("competitive", {})
    for info in (skills.get("SeasonalInfoBySeasonID") or {}).values():
        best = max(best, info.get("CompetitiveTier", 0))
    return best


def _player_tier(client, puuid, fallback):
    if fallback:
        return fallback
    try:
        return _tier_from_mmr(client.fetch_mmr(puuid=puuid))
    except Exception:
        return 0


def fetch_normalized(client):
    """Return {'state', 'players': [...]} or None when not in a lobby.

    Each player: {puuid, team ('ally'|'enemy'), agent, account_level,
                  hidden_level, incognito, tier}.
    """
    state, players = _fetch_raw(client)
    if not players:
        return None

    me = getattr(client, "puuid", None)
    my_team_id = None
    if state == "coregame":
        for p in players:
            if p.get("Subject") == me:
                my_team_id = p.get("TeamID")
                break

    normalized = []
    for p in players:
        ident = _identity(p)
        if state == "coregame":
            team = "ally" if p.get("TeamID") == my_team_id else "enemy"
        else:
            team = "ally"
        normalized.append(
            {
                "puuid": p.get("Subject"),
                "is_me": p.get("Subject") == me,
                "team": team,
                "agent": agent_name(p.get("CharacterID")),
                "account_level": ident["account_level"],
                "hidden_level": ident["hidden_level"],
                "incognito": ident["incognito"],
                "tier": _player_tier(client, p.get("Subject"), p.get("CompetitiveTier", 0)),
            }
        )
    return {"state": state, "players": normalized}


def _fetch_raw(client):
    """Try pregame (agent select) first, then coregame (load-in / in-game)."""
    try:
        match = client.pregame_fetch_match()
        if match:
            team = match.get("AllyTeam") or {}
            return "pregame", team.get("Players", [])
    except Exception:
        pass
    try:
        match = client.coregame_fetch_match()
        if match:
            return "coregame", match.get("Players", [])
    except Exception:
        pass
    return None, []

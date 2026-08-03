"""Team composition and role intelligence."""

ROLE_BY_AGENT = {
    "Jett": "duelist",
    "Reyna": "duelist",
    "Raze": "duelist",
    "Phoenix": "duelist",
    "Yoru": "duelist",
    "Neon": "duelist",
    "Iso": "duelist",
    "Waylay": "duelist",
    "Sova": "initiator",
    "Breach": "initiator",
    "Skye": "initiator",
    "KAY/O": "initiator",
    "Fade": "initiator",
    "Gekko": "initiator",
    "Tejo": "initiator",
    "Sage": "sentinel",
    "Cypher": "sentinel",
    "Killjoy": "sentinel",
    "Chamber": "sentinel",
    "Deadlock": "sentinel",
    "Vyse": "sentinel",
    "Omen": "controller",
    "Brimstone": "controller",
    "Viper": "controller",
    "Astra": "controller",
    "Harbor": "controller",
    "Clove": "controller",
}


def _role(agent_name):
    return ROLE_BY_AGENT.get(agent_name, "unknown")


def analyze_team_comp(players):
    counts = {"duelist": 0, "initiator": 0, "controller": 0, "sentinel": 0, "unknown": 0}
    for p in players:
        counts[_role(p.get("agent"))] += 1

    missing = [r for r in ("controller", "initiator", "sentinel") if counts[r] == 0]
    duelist_overload = max(0, counts["duelist"] - 2)

    score = 100
    score -= len(missing) * 20
    score -= duelist_overload * 12
    score = max(0, min(100, score))

    return {
        "score": score,
        "counts": counts,
        "missing_roles": missing,
        "duelist_overload": duelist_overload,
    }

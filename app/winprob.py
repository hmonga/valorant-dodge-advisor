"""Win-probability estimate for your team vs. the enemy team.

v1 is a transparent heuristic (logistic on rank + form gaps) so it works with zero
training data. Swap this out for a trained scikit-learn model later — collect real
lobby outcomes, then replace `estimate()` with model.predict_proba().
"""

# One full rank = 3 tiers. Larger K => rank gaps matter less.
_K = 6.0


def _avg(players, key, default=0.0):
    vals = [p.get(key) for p in players if p.get(key) is not None]
    return sum(vals) / len(vals) if vals else default


def estimate(allies, enemies):
    """Return {'win_prob': float|None, 'basis': str}.

    win_prob is None in pregame (agent select) because enemies are hidden.
    """
    if not enemies:
        return {"win_prob": None, "basis": "enemies hidden (agent select)"}

    ally_tier = _avg(allies, "tier")
    enemy_tier = _avg(enemies, "tier")

    ally_form = _avg([p.get("form", {}) or {} for p in allies], "winrate", 0.5)
    enemy_form = _avg([p.get("form", {}) or {} for p in enemies], "winrate", 0.5)

    # Rank gap drives the base probability; form nudges it.
    rank_gap = ally_tier - enemy_tier
    form_gap = (ally_form - enemy_form) * 3.0  # scale form into ~tier units
    edge = rank_gap + form_gap

    win_prob = 1.0 / (1.0 + 10 ** (-edge / _K))
    return {
        "win_prob": round(win_prob, 3),
        "basis": f"avg rank gap {round(rank_gap, 1)}, form gap {round(form_gap, 2)}",
    }

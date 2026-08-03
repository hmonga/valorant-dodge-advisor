"""Decision engine: EV scoring, confidence, and explainability."""


def clamp(value, low, high):
    return max(low, min(high, value))


def _rank_gap_risk(allies, enemies):
    ally = [p.get("tier", 0) for p in allies]
    enemy = [p.get("tier", 0) for p in enemies]
    if not ally or not enemy:
        return 50
    gap = (sum(enemy) / len(enemy)) - (sum(ally) / len(ally))
    return int(clamp(50 + gap * 4, 0, 100))


def _smurf_risk(allies, enemies):
    enemy_scores = [((p.get("smurf") or {}).get("score", 0)) for p in enemies]
    ally_scores = [((p.get("smurf") or {}).get("score", 0)) for p in allies]
    if not enemy_scores:
        return 50
    enemy_avg = sum(enemy_scores) / len(enemy_scores)
    ally_avg = (sum(ally_scores) / len(ally_scores)) if ally_scores else 0
    return int(clamp(40 + (enemy_avg - ally_avg) * 0.9, 0, 100))


def _form_value(players):
    forms = [(p.get("form") or {}).get("winrate") for p in players]
    vals = [f for f in forms if f is not None]
    if not vals:
        return 0.5, 0
    return (sum(vals) / len(vals), len(vals))


def build_decision(state, win_prob, allies, enemies, team_comp, settings, recent_summary):
    if win_prob is None or not enemies or state == "pregame":
        return {
            "recommendation": "WAIT",
            "confidence": 30,
            "rr_ev_play": None,
            "rr_ev_dodge": None,
            "dodge_ev_summary": "Need full enemy data at load-in for final EV call.",
            "key_risks": {
                "smurf_risk": _smurf_risk(allies, enemies),
                "role_conflict": int(clamp(100 - team_comp.get("score", 50), 0, 100)),
                "rank_gap": _rank_gap_risk(allies, enemies),
                "mental_tilt_risk": int(clamp(45 + recent_summary.get("fatigue_index", 0), 0, 100)),
            },
            "top_reasons": [
                "Enemy roster is hidden until load-in.",
                "Composition scan is preliminary.",
                "Wait for full data before hard commit.",
            ],
            "what_would_change": ["Load into map so enemy team data becomes visible."],
        }

    rr_gain = int(settings.get("rr_gain_on_win", 20))
    rr_loss = int(settings.get("rr_loss_on_loss", 20))
    dodge_penalty = int(settings.get("dodge_rr_penalty", 3))

    rr_ev_play = (win_prob * rr_gain) - ((1.0 - win_prob) * rr_loss)
    rr_ev_dodge = -float(dodge_penalty)

    rank_risk = _rank_gap_risk(allies, enemies)
    smurf_risk = _smurf_risk(allies, enemies)
    role_risk = int(clamp(100 - team_comp.get("score", 50), 0, 100))

    ally_form, ally_n = _form_value(allies)
    enemy_form, enemy_n = _form_value(enemies)
    form_gap = ally_form - enemy_form

    fatigue_index = recent_summary.get("fatigue_index", 0)
    tilt_risk = int(clamp(40 + (fatigue_index * 1.2) + max(0, -form_gap * 100) * 0.2, 0, 100))

    uncertainty = 0
    if ally_n < 4 or enemy_n < 4:
        uncertainty += 25
    if any(p.get("tier", 0) == 0 for p in allies + enemies):
        uncertainty += 12
    if team_comp.get("counts", {}).get("unknown", 0) > 0:
        uncertainty += 8

    confidence = int(clamp(85 - uncertainty - (tilt_risk * 0.08), 20, 95))

    recommendation = "PLAY"
    if rr_ev_play + 1.0 < rr_ev_dodge:
        recommendation = "DODGE"
    elif rr_ev_play < rr_ev_dodge:
        recommendation = "LEAN_DODGE"

    if confidence < 45 and recommendation == "DODGE":
        recommendation = "LEAN_DODGE"

    top_reasons = []
    top_reasons.append(f"RR EV play {rr_ev_play:.1f} vs dodge {rr_ev_dodge:.1f}.")
    if smurf_risk >= 65:
        top_reasons.append("Enemy smurf risk is high.")
    if role_risk >= 60:
        top_reasons.append("Team composition has role conflicts or missing utility.")
    if rank_risk >= 60:
        top_reasons.append("Enemy average rank pressure is high.")
    if len(top_reasons) < 3:
        top_reasons.append("Recent form and rank signals are within normal range.")
    if len(top_reasons) < 3:
        top_reasons.append("Confidence rises once more match data accumulates.")

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "rr_ev_play": round(rr_ev_play, 2),
        "rr_ev_dodge": round(rr_ev_dodge, 2),
        "dodge_ev_summary": f"Play EV {rr_ev_play:.1f} RR vs dodge EV {rr_ev_dodge:.1f} RR.",
        "key_risks": {
            "smurf_risk": smurf_risk,
            "role_conflict": role_risk,
            "rank_gap": rank_risk,
            "mental_tilt_risk": tilt_risk,
        },
        "top_reasons": top_reasons[:3],
        "what_would_change": [
            "Lower enemy smurf pressure.",
            "Better role balance (controller + initiator + sentinel).",
            "Improved pre-match form trend.",
        ],
    }

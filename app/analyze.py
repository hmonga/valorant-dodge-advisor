"""Orchestrator: live lobby -> enriched players -> smurf flags -> win probability
-> dodge verdict. Returns a JSON-friendly dict for the API/overlay.
"""

import copy

from . import config, stats, winprob
from .decision import build_decision
from .history import append_snapshot, summarize_recent
from .lobby import fetch_normalized
from .ranks import rank_name
from .riot_client import get_client, reset_client
from .roles import analyze_team_comp
from .settings_store import load_settings
from .smurf import smurf_score


def _troubleshooting(code):
    common = [
        "You can launch the app first or launch Valorant first.",
        "Keep the app in Live mode (disable Mock Data) for real matches.",
    ]

    if code == "missing_dependency":
        return [
            "App runtime is missing valclient. Reinstall the app.",
            "If running from source, reinstall dependencies from requirements.txt.",
        ]
    if code == "bad_region":
        return [
            "Open settings and set a valid region (na, eu, ap, kr, latam, br).",
            "Save settings and wait a few seconds for reconnect.",
        ] + common
    if code in {"no_lockfile", "client_unreachable", "activation_failed"}:
        return [
            "Launch Riot Client and open Valorant.",
            "Wait at least 10-20 seconds after game launch.",
            "If it still fails, restart app and game once.",
        ] + common
    return common


def _verdict_from_decision(decision, win_prob):
    rec = decision.get("recommendation")
    call = {
        "DODGE": "DODGE",
        "LEAN_DODGE": "LEAN DODGE",
        "PLAY": "STAY",
        "WAIT": "WAIT",
    }.get(rec, "WAIT")

    if rec == "WAIT":
        reason = "Waiting for enough live data to finalize recommendation."
    elif win_prob is None:
        reason = decision.get("dodge_ev_summary", "Decision built from partial data.")
    else:
        reason = f"{decision.get('dodge_ev_summary', '')} (win {round(win_prob * 100)}%)"

    return {"call": call, "reason": reason}


def _enemy_threats(enemies):
    ranked = []
    for p in enemies:
        form = p.get("form") or {}
        score = (p.get("tier", 0) * 1.5) + ((p.get("smurf") or {}).get("score", 0) * 0.8) + (form.get("winrate", 0.5) * 35)
        ranked.append({
            "agent": p.get("agent"),
            "rank": p.get("rank"),
            "smurf_score": (p.get("smurf") or {}).get("score", 0),
            "recent_winrate": form.get("winrate"),
            "threat_score": round(score, 1),
        })
    return sorted(ranked, key=lambda x: x["threat_score"], reverse=True)[:3]


def _composition_advice(team_comp):
    out = []
    missing = team_comp.get("missing_roles", [])
    if "controller" in missing:
        out.append("Add a controller for smoke coverage.")
    if "initiator" in missing:
        out.append("Add an initiator for info and entry support.")
    if "sentinel" in missing:
        out.append("Add a sentinel for flank control and site anchor.")
    if team_comp.get("duelist_overload", 0) > 0:
        out.append("Too many duelists; swap one into utility role.")
    return out[:3]


def _enrich(players, client):
    out = []
    for p in players:
        p = copy.deepcopy(p)
        if "form" not in p and client is not None and p.get("puuid"):
            p["form"] = stats.recent_form(client, p["puuid"])
        form = p.get("form") or {}
        p["rank"] = rank_name(p.get("tier", 0))
        p["smurf"] = smurf_score(p.get("tier", 0), p.get("account_level", 0), form.get("winrate"))
        out.append(p)
    return out


def analyze():
    settings = load_settings()
    recent_summary = summarize_recent()

    if config.MOCK:
        from .mock import MOCK_LOBBY

        lobby = copy.deepcopy(MOCK_LOBBY)
        client = None
    else:
        client, client_status = get_client(return_status=True)
        if client is None:
            return {
                "state": "no_game",
                "mode": "live",
                "message": client_status.get("message") or "Valorant isn't running (or client not found).",
                "issue_code": client_status.get("code", "client_unavailable"),
                "troubleshooting": _troubleshooting(client_status.get("code")),
            }
        lobby = fetch_normalized(client)
        if lobby is None:
            # Auto-recover if the cached local client became stale after game restarts.
            reset_client()
            client, client_status = get_client(return_status=True)
            if client is None:
                return {
                    "state": "no_game",
                    "mode": "live",
                    "message": client_status.get("message") or "Valorant isn't running (or client not found).",
                    "issue_code": client_status.get("code", "client_unavailable"),
                    "troubleshooting": _troubleshooting(client_status.get("code")),
                }
            lobby = fetch_normalized(client)
            if lobby is None:
                return {
                    "state": "no_match",
                    "mode": "live",
                    "message": "Connected, but you are not in agent select or an active match.",
                    "issue_code": "no_active_match",
                    "troubleshooting": [
                        "Queue for a game and open agent select to see lobby data.",
                        "During menu/party lobby, no match data is available yet.",
                    ],
                }

    players = _enrich(lobby["players"], client)
    allies = [p for p in players if p["team"] == "ally"]
    enemies = [p for p in players if p["team"] == "enemy"]

    prob = winprob.estimate(allies, enemies)
    team_comp = analyze_team_comp(allies)
    decision = build_decision(
        state=lobby["state"],
        win_prob=prob["win_prob"],
        allies=allies,
        enemies=enemies,
        team_comp=team_comp,
        settings=settings,
        recent_summary=recent_summary,
    )

    enemy_smurfs = sum(1 for p in enemies if p["smurf"]["likely_smurf"])
    ally_smurfs = sum(1 for p in allies if p["smurf"]["likely_smurf"])

    payload = {
        "state": lobby["state"],
        "mode": "mock" if config.MOCK else "live",
        "win_prob": prob["win_prob"],
        "win_prob_basis": prob["basis"],
        "verdict": _verdict_from_decision(decision, prob["win_prob"]),
        "decision": decision,
        "team_comp": team_comp,
        "composition_advice": _composition_advice(team_comp),
        "enemy_threats": _enemy_threats(enemies),
        "personal_insights": {
            "fatigue_index": recent_summary.get("fatigue_index", 0),
            "recent_samples": recent_summary.get("samples", 0),
            "avg_confidence": recent_summary.get("avg_confidence", 0),
            "play_rate": recent_summary.get("play_rate", 0.0),
        },
        "settings_used": {
            "queue_type": settings.get("queue_type"),
            "rr_gain_on_win": settings.get("rr_gain_on_win"),
            "rr_loss_on_loss": settings.get("rr_loss_on_loss"),
            "dodge_rr_penalty": settings.get("dodge_rr_penalty"),
        },
        "counts": {"enemy_smurfs": enemy_smurfs, "ally_smurfs": ally_smurfs},
        "allies": allies,
        "enemies": enemies,
    }

    append_snapshot(payload)
    return payload

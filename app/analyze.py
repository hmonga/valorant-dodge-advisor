"""Orchestrator: live lobby -> enriched players -> smurf flags -> win probability
-> dodge verdict. Returns a JSON-friendly dict for the API/overlay.
"""

import copy

from . import config, stats, winprob
from .lobby import fetch_normalized
from .ranks import rank_name
from .riot_client import get_client, reset_client
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


def _verdict(state, win_prob, enemy_smurfs):
    if state == "pregame":
        return {
            "call": "WAIT",
            "reason": "Agent select — enemies are hidden. Verdict updates at load-in.",
        }
    if win_prob is None:
        return {"call": "WAIT", "reason": "Not enough info yet."}

    if win_prob < 0.42:
        reason = f"Low win chance ({round(win_prob * 100)}%)."
        if enemy_smurfs:
            reason += f" {enemy_smurfs} likely smurf(s) on enemy team."
        return {"call": "DODGE", "reason": reason}
    if win_prob < 0.50:
        return {
            "call": "LEAN DODGE",
            "reason": f"Slightly unfavorable ({round(win_prob * 100)}%).",
        }
    return {"call": "STAY", "reason": f"Favorable ({round(win_prob * 100)}%)."}


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
    enemy_smurfs = sum(1 for p in enemies if p["smurf"]["likely_smurf"])
    ally_smurfs = sum(1 for p in allies if p["smurf"]["likely_smurf"])

    return {
        "state": lobby["state"],
        "mode": "mock" if config.MOCK else "live",
        "win_prob": prob["win_prob"],
        "win_prob_basis": prob["basis"],
        "verdict": _verdict(lobby["state"], prob["win_prob"], enemy_smurfs),
        "counts": {"enemy_smurfs": enemy_smurfs, "ally_smurfs": ally_smurfs},
        "allies": allies,
        "enemies": enemies,
    }

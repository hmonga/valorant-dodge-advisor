"""Local learning loop: log recommendations and summarize recent trends."""

from __future__ import annotations

import json
import time
from pathlib import Path

_APP_DIR = Path.home() / ".valorant-dodge-advisor"
_HISTORY_FILE = _APP_DIR / "history.jsonl"

_last_signature = ""
_last_ts = 0.0


def _ensure_dir():
    _APP_DIR.mkdir(parents=True, exist_ok=True)


def _signature(payload):
    state = payload.get("state", "")
    allies = payload.get("allies", [])
    enemies = payload.get("enemies", [])
    rec = ((payload.get("decision") or {}).get("recommendation", ""))
    a_ids = ",".join(sorted([p.get("puuid", "") for p in allies if p.get("puuid")]))
    e_ids = ",".join(sorted([p.get("puuid", "") for p in enemies if p.get("puuid")]))
    return f"{state}|{rec}|{a_ids}|{e_ids}"


def append_snapshot(payload):
    global _last_signature, _last_ts
    sig = _signature(payload)
    now = time.time()

    # Avoid writing duplicate snapshots every polling cycle.
    if sig == _last_signature and (now - _last_ts) < 60:
        return False

    _ensure_dir()
    record = {
        "ts": int(now),
        "state": payload.get("state"),
        "mode": payload.get("mode"),
        "win_prob": payload.get("win_prob"),
        "recommendation": (payload.get("decision") or {}).get("recommendation"),
        "confidence": (payload.get("decision") or {}).get("confidence"),
        "rr_ev_play": (payload.get("decision") or {}).get("rr_ev_play"),
    }
    with _HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    _last_signature = sig
    _last_ts = now
    return True


def append_outcome(outcome):
    _ensure_dir()
    record = {
        "ts": int(time.time()),
        "type": "outcome",
        "result": outcome.get("result"),
        "rr_delta": outcome.get("rr_delta"),
        "notes": outcome.get("notes", ""),
    }
    with _HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return True


def _read_recent(max_items=200):
    if not _HISTORY_FILE.exists():
        return []
    lines = _HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-max_items:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def summarize_recent(max_items=120):
    rows = _read_recent(max_items=max_items)
    if not rows:
        return {
            "samples": 0,
            "play_rate": 0.0,
            "avg_confidence": 0.0,
            "avg_win_prob": None,
            "fatigue_index": 0,
        }

    decision_rows = [r for r in rows if r.get("type") != "outcome"]
    outcome_rows = [r for r in rows if r.get("type") == "outcome"]

    recs = [r.get("recommendation") for r in decision_rows if r.get("recommendation")]
    play_like = sum(1 for r in recs if r in {"PLAY", "STAY"})
    avg_conf = [r.get("confidence") for r in decision_rows if isinstance(r.get("confidence"), (int, float))]
    avg_prob = [r.get("win_prob") for r in decision_rows if isinstance(r.get("win_prob"), (int, float))]

    recent = decision_rows[-20:]
    low_conf_recent = sum(1 for r in recent if isinstance(r.get("confidence"), (int, float)) and r.get("confidence") < 45)
    lean_dodge_recent = sum(1 for r in recent if r.get("recommendation") in {"DODGE", "LEAN_DODGE"})
    fatigue = min(100, (low_conf_recent * 4) + (lean_dodge_recent * 3))

    outcome_rr = [r.get("rr_delta") for r in outcome_rows if isinstance(r.get("rr_delta"), (int, float))]
    outcome_wins = [r for r in outcome_rows if r.get("result") == "win"]

    return {
        "samples": len(rows),
        "play_rate": round(play_like / max(1, len(recs)), 3) if recs else 0.0,
        "avg_confidence": round(sum(avg_conf) / len(avg_conf), 1) if avg_conf else 0.0,
        "avg_win_prob": round(sum(avg_prob) / len(avg_prob), 3) if avg_prob else None,
        "fatigue_index": fatigue,
        "outcome_samples": len(outcome_rows),
        "outcome_win_rate": round(len(outcome_wins) / len(outcome_rows), 3) if outcome_rows else None,
        "avg_rr_delta": round(sum(outcome_rr) / len(outcome_rr), 2) if outcome_rr else None,
    }


def stats_path():
    return str(_HISTORY_FILE)

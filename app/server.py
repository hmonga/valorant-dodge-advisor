from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import config
from .analyze import analyze
from .history import append_outcome, stats_path, summarize_recent
from .riot_client import get_client_status
from .settings_store import load_settings, save_settings, settings_path
from .update_check import check_latest_release

app = FastAPI(title="Valorant Dodge Advisor")

_WEB = Path(__file__).resolve().parent.parent / "web" / "index.html"
_SETTINGS = load_settings()


class SettingsUpdate(BaseModel):
    region: str | None = None
    mock: bool | None = None
    refresh_seconds: int | None = None
    queue_type: str | None = None
    rr_gain_on_win: int | None = None
    rr_loss_on_loss: int | None = None
    dodge_rr_penalty: int | None = None
    start_on_login: bool | None = None
    notify_strong_dodge: bool | None = None
    auto_check_updates: bool | None = None


class OutcomeUpdate(BaseModel):
    result: str
    rr_delta: int | None = None
    notes: str | None = None


@app.get("/api/analyze")
def api_analyze():
    return analyze()


@app.get("/api/health")
def api_health():
    recent = summarize_recent(max_items=60)
    return {
        "ok": True,
        "mock": config.MOCK,
        "region": config.REGION,
        "settings_path": settings_path(),
        "client_status": get_client_status(),
        "recent_summary": recent,
    }


@app.get("/api/setup-check")
def api_setup_check():
    client_status = get_client_status()
    checks = [
        {
            "name": "Desktop backend",
            "ok": True,
            "message": "Backend is running.",
        },
        {
            "name": "Mode",
            "ok": True,
            "message": "Mock mode is enabled." if config.MOCK else "Live mode is enabled.",
        },
        {
            "name": "Region",
            "ok": bool(config.REGION),
            "message": f"Configured region: {config.REGION or 'unset'}",
        },
        {
            "name": "Riot client",
            "ok": config.MOCK or client_status.get("code") == "connected",
            "message": "Connected." if config.MOCK or client_status.get("code") == "connected" else client_status.get("message"),
        },
    ]
    return {
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
    }


@app.get("/api/stats")
def api_stats():
    return {
        "summary": summarize_recent(max_items=300),
        "history_path": stats_path(),
    }


@app.post("/api/outcome")
def api_outcome(update: OutcomeUpdate):
    result = update.result.lower().strip()
    if result not in {"win", "loss"}:
        return {"ok": False, "message": "result must be 'win' or 'loss'"}
    append_outcome({"result": result, "rr_delta": update.rr_delta, "notes": update.notes or ""})
    return {"ok": True}


@app.get("/api/update-check")
def api_update_check():
    return check_latest_release(current_version="0.1.0")


@app.get("/api/settings")
def api_settings():
    _SETTINGS.update(load_settings())
    return _SETTINGS


@app.post("/api/settings")
def api_settings_update(update: SettingsUpdate):
    payload = update.model_dump(exclude_none=True)
    if "refresh_seconds" in payload:
        payload["refresh_seconds"] = max(2, min(30, int(payload["refresh_seconds"])))
    if "rr_gain_on_win" in payload:
        payload["rr_gain_on_win"] = max(5, min(50, int(payload["rr_gain_on_win"])))
    if "rr_loss_on_loss" in payload:
        payload["rr_loss_on_loss"] = max(5, min(50, int(payload["rr_loss_on_loss"])))
    if "dodge_rr_penalty" in payload:
        payload["dodge_rr_penalty"] = max(0, min(10, int(payload["dodge_rr_penalty"])))
    if "queue_type" in payload:
        payload["queue_type"] = str(payload["queue_type"]).strip().lower() or "competitive"
    _SETTINGS.update(save_settings(payload))
    return _SETTINGS


@app.get("/", response_class=HTMLResponse)
def index():
    return _WEB.read_text(encoding="utf-8")

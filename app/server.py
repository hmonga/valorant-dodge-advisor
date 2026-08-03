from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import config
from .analyze import analyze
from .settings_store import load_settings, save_settings, settings_path

app = FastAPI(title="Valorant Dodge Advisor")

_WEB = Path(__file__).resolve().parent.parent / "web" / "index.html"
_SETTINGS = load_settings()


class SettingsUpdate(BaseModel):
    region: str | None = None
    mock: bool | None = None
    refresh_seconds: int | None = None


@app.get("/api/analyze")
def api_analyze():
    return analyze()


@app.get("/api/health")
def api_health():
    return {
        "ok": True,
        "mock": config.MOCK,
        "region": config.REGION,
        "settings_path": settings_path(),
    }


@app.get("/api/settings")
def api_settings():
    _SETTINGS.update(load_settings())
    return _SETTINGS


@app.post("/api/settings")
def api_settings_update(update: SettingsUpdate):
    payload = update.model_dump(exclude_none=True)
    if "refresh_seconds" in payload:
        payload["refresh_seconds"] = max(2, min(30, int(payload["refresh_seconds"])))
    _SETTINGS.update(save_settings(payload))
    return _SETTINGS


@app.get("/", response_class=HTMLResponse)
def index():
    return _WEB.read_text(encoding="utf-8")

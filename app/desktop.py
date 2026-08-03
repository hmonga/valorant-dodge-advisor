"""Desktop launcher for Valorant Dodge Advisor.

Starts the local FastAPI server and opens a native desktop window.
"""

from __future__ import annotations

import argparse
import socket
import threading
import time
import webbrowser

import requests
import uvicorn


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_server(port):
    uvicorn.run("app.server:app", host="127.0.0.1", port=port, log_level="warning")


def _wait_until_ready(port, timeout=12.0):
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/api/health"
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1.5)
            if r.ok:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def launch_desktop_app(overlay=False):
    port = _free_port()
    server_thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    server_thread.start()

    if not _wait_until_ready(port):
        raise RuntimeError("Backend failed to start.")

    url = f"http://127.0.0.1:{port}/"

    try:
        import webview

        window = webview.create_window(
            "Valorant Dodge Advisor",
            url,
            width=460 if overlay else 1200,
            height=760 if overlay else 820,
            min_size=(420, 600) if overlay else (980, 700),
            text_select=False,
            on_top=overlay,
            frameless=overlay,
        )
        webview.start()
        return window
    except Exception:
        # Fallback keeps the app usable even if webview backend is unavailable.
        webbrowser.open(url)
        print(f"Opened browser at {url}")
        print("Press Ctrl+C to exit.")
        while True:
            time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch Valorant Dodge Advisor desktop app")
    parser.add_argument("--overlay", action="store_true", help="Launch compact always-on-top companion window")
    args = parser.parse_args()
    launch_desktop_app(overlay=args.overlay)

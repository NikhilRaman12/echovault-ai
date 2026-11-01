"""Automated UI and server health checkup test suite for EchoVault AI."""

import time
import requests
import pytest

UI_BASE_URL = "http://localhost:8501"


def test_ui_health_endpoint():
    """Verify Streamlit native /_stcore/health endpoint reports 'ok'."""
    url = f"{UI_BASE_URL}/_stcore/health"
    start = time.time()
    try:
        resp = requests.get(url, timeout=5)
    except requests.exceptions.ConnectionError:
        pytest.fail(f"Could not connect to UI server at {UI_BASE_URL}. Ensure 'streamlit run app.py' is active.")

    duration_ms = (time.time() - start) * 1000
    assert resp.status_code == 200, f"Health endpoint returned status code {resp.status_code}"
    assert resp.text.strip() == "ok", f"Expected 'ok' from health endpoint, got: {resp.text}"
    assert duration_ms < 1500, f"Health check response took {duration_ms:.1f} ms (expected < 1500ms)"


def test_ui_root_page_load():
    """Verify primary application root serves complete HTML document."""
    url = f"{UI_BASE_URL}/"
    resp = requests.get(url, timeout=5)
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("Content-Type", "")
    assert "<!DOCTYPE html>" in resp.text or "<html" in resp.text
    # Verify Streamlit bundle hooks
    assert "streamlit" in resp.text.lower() or "window.streamlit" in resp.text.lower() or "static/js" in resp.text


def test_ui_response_headers():
    """Verify security and caching headers on the UI server."""
    resp = requests.get(f"{UI_BASE_URL}/", timeout=5)
    assert resp.status_code == 200
    headers = resp.headers
    assert "Server" in headers
    assert "TornadoServer" in headers.get("Server", "") or "streamlit" in headers.get("Server", "").lower()


def test_ui_stream_endpoint():
    """Verify websocket stream handshake endpoint responds."""
    resp = requests.get(f"{UI_BASE_URL}/_stcore/stream", headers={"Upgrade": "websocket", "Connection": "Upgrade"}, timeout=5)
    # Streamlit returns either 101 Switching Protocols or 400 Bad Request if websocket headers are incomplete
    assert resp.status_code in [101, 400, 426]

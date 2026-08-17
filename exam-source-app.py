import json
import os

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# --- Configuration (all from environment) ---
PORT = int(os.environ.get("PORT", "5000"))
APP_ENV = os.environ.get("APP_ENV", "unset")
APP_VERSION = os.environ.get("APP_VERSION", "unset")
CONFIG_PATH = os.environ.get("CONFIG_PATH", "/app/config/config.json")
API_KEY = os.environ.get("API_KEY", "")

_config = None
_config_error = None


def load_config():
    """Load the config file. The app is NOT ready until this succeeds."""
    global _config, _config_error
    try:
        with open(CONFIG_PATH) as f:
            _config = json.load(f)
        _config_error = None
    except Exception as exc:
        _config = None
        _config_error = str(exc)
    return _config


load_config()


PAGE = """
<!doctype html>
<title>{{ app_name }}</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 60px auto; max-width: 640px; }
  .banner { font-size: 28px; font-weight: 600; }
  .meta { color: #555; margin-top: 24px; line-height: 1.8; }
  code { background: #f2f2f2; padding: 2px 6px; border-radius: 4px; }
</style>
<div class="banner">{{ app_name }}</div>
<p>{{ subtitle }}</p>
<div class="meta">
  Environment: <code>{{ env }}</code><br>
  Version: <code>{{ version }}</code><br>
  Owner: <code>{{ owner }}</code><br>
  API key loaded: <code>{{ key_status }}</code><br>
  Served by pod: <code>{{ hostname }}</code>
</div>
"""


@app.route("/")
def index():
    if _config is None:
        return f"Config not loaded: {_config_error}", 503
    return render_template_string(
        PAGE,
        app_name=_config.get("app_name", "Portal"),
        subtitle=_config.get("subtitle", ""),
        owner=_config.get("owner", "unknown"),
        env=APP_ENV,
        version=APP_VERSION,
        key_status=("yes (%d chars)" % len(API_KEY)) if API_KEY else "NO - missing API_KEY",
        hostname=os.environ.get("HOSTNAME", "unknown"),
    )


@app.route("/healthz")
def healthz():
    """Liveness: the process is alive. Should stay 200 unless the app is wedged."""
    return jsonify(status="alive"), 200


@app.route("/readyz")
def readyz():
    """Readiness: only ready when config file AND API key are present."""
    problems = []
    if _config is None:
        problems.append(f"config: {_config_error}")
    if not API_KEY:
        problems.append("API_KEY environment variable is empty")
    if problems:
        return jsonify(status="not-ready", problems=problems), 503
    return jsonify(status="ready"), 200


@app.route("/api/info")
def info():
    if _config is None:
        return jsonify(error="config not loaded"), 503
    return jsonify(
        app=_config.get("app_name"),
        owner=_config.get("owner"),
        env=APP_ENV,
        version=APP_VERSION,
        pod=os.environ.get("HOSTNAME", "unknown"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

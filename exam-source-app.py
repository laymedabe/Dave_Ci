# Import required standard libraries
import json
import os

# Import Flask for the web framework functionality
from flask import Flask, jsonify, render_template_string

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration (all from environment) ---
# Read the target port from the environment, defaulting to 5000
PORT = int(os.environ.get("PORT", "5000"))
# Identify if we are in 'staging' or 'production'
APP_ENV = os.environ.get("APP_ENV", "unset")
# Identify the current build/tag version
APP_VERSION = os.environ.get("APP_VERSION", "unset")
# Path where the ConfigMap will be mounted as a file
CONFIG_PATH = os.environ.get("CONFIG_PATH", "/app/config/config.json")
# Secret API key injected by Kubernetes Secrets
API_KEY = os.environ.get("API_KEY", "")

# Global variables to store the loaded config and any load errors
_config = None
_config_error = None


def load_config():
    """Load the config file. The app is NOT ready until this succeeds."""
    global _config, _config_error
    try:
        # Attempt to open and parse the JSON file injected by the ConfigMap
        with open(CONFIG_PATH) as f:
            _config = json.load(f)
        _config_error = None
    except Exception as exc:
        # If the ConfigMap is not mounted properly, catch the error
        _config = None
        _config_error = str(exc)
    return _config


# Attempt to load the config immediately on startup
load_config()


# HTML Template for the main webpage
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
  Served by podssssssssssss: <code>{{ hostname }}</code>
</div>
"""


@app.route("/")
def index():
    # If the config failed to load, return a 503 error page
    if _config is None:
        return f"Config not loaded: {_config_error}", 503
        
    # Render the HTML page using variables from our ConfigMap and Environment
    return render_template_string(
        PAGE,
        app_name=_config.get("app_name", "Portal"),
        subtitle=_config.get("subtitle", ""),
        owner=_config.get("owner", "unknown"),
        env=APP_ENV,
        version=APP_VERSION,
        # Check if the Secret was loaded properly
        key_status=("yes (%d chars)" % len(API_KEY)) if API_KEY else "NO - missing API_KEY",
        # Print the Pod's hostname so we know which replica answered the request
        hostname=os.environ.get("HOSTNAME", "unknown"),
    )


@app.route("/healthz")
def healthz():
    """Liveness probe: tells Kubernetes the process hasn't crashed."""
    # Kubernetes will hit this endpoint every 10 seconds.
    return jsonify(status="alive"), 200


@app.route("/readyz")
def readyz():
    """Readiness probe: tells Kubernetes if the app is ready to receive user traffic."""
    problems = []
    # Verify the ConfigMap was loaded
    if _config is None:
        problems.append(f"config: {_config_error}")
    # Verify the Secret was loaded
    if not API_KEY:
        problems.append("API_KEY environment variable is empty")
        
    # If anything is missing, return 503 so Kubernetes stops sending traffic to this pod
    if problems:
        return jsonify(status="not-ready", problems=problems), 503
        
    # Everything is good! Send me traffic!
    return jsonify(status="ready"), 200


@app.route("/api/info")
def info():
    # JSON API endpoint for getting app metadata
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
    # Start the web server and listen on all network interfaces (0.0.0.0)
    app.run(host="0.0.0.0", port=PORT)

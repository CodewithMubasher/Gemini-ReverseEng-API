"""Configuration management."""
import json
import os
import secrets
import stat

API_KEY_PREFIX = "sk-local-"

DEFAULT_CONFIG = {
    "port": 8081,
    "host": "0.0.0.0",
    "retry_attempts": 3,
    "retry_delay_sec": 2,
    "request_timeout_sec": 180,
    "gemini_bl": "boq_assistant-bard-web-server_20260716.08_p0",
    "auth_user": None,
    "xsrf_token": None,
    "default_model": "gemini-3.6-flash",
    "log_requests": True,
    "cookie_file": None,
    "proxy": None,
    "api_keys": [],
    "api_key_file": None,
    "temporary_chats": False,
}

CONFIG = dict(DEFAULT_CONFIG)


def load_config(path: str = None):
    """Load config from JSON file."""
    if path and os.path.exists(path):
        with open(path) as f:
            CONFIG.update(json.load(f))
    return CONFIG


def find_config():
    """Search for config file in standard locations."""
    for p in ["./config.json", os.path.expanduser("~/.config/gemini-web2api/config.json")]:
        if os.path.exists(p):
            return p
    return None


def api_key_path() -> str:
    """Where the auto-generated local API key is persisted."""
    return os.path.join(os.path.expanduser("~"), ".config", "gemini-web2api", "api_key")


def generate_api_key() -> str:
    """Create a new OpenAI-style local API key."""
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


def ensure_api_key() -> str:
    """Return the active API key, generating and saving one when needed.

    Resolution order:
      1. An explicit key from config.json (``api_keys``) or the CLI.
      2. ``GEMINI_WEB2API_API_KEY`` from the environment.
      3. A previously generated key in ~/.config/gemini-web2api/api_key.
      4. A freshly generated key, persisted for the next run.
    """
    keys = [k for k in (CONFIG.get("api_keys") or []) if k]
    if keys:
        CONFIG["api_keys"] = keys
        CONFIG["api_key_file"] = None
        return keys[0]

    env_key = (os.environ.get("GEMINI_WEB2API_API_KEY") or "").strip()
    if env_key:
        CONFIG["api_keys"] = [env_key]
        CONFIG["api_key_file"] = None
        return env_key

    path = api_key_path()
    key = None
    try:
        with open(path, encoding="utf-8") as f:
            key = f.read().strip()
    except OSError:
        key = None

    if not key or not key.startswith(API_KEY_PREFIX):
        key = generate_api_key()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(key + "\n")
            try:
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
        except OSError:
            # If the key cannot be persisted it still works for this run.
            pass

    CONFIG["api_keys"] = [key]
    CONFIG["api_key_file"] = path
    return key

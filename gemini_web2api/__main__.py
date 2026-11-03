"""Entry point: python -m gemini_web2api"""
import argparse
import os

from .config import CONFIG, load_config, find_config, ensure_api_key
from .models import MODELS
from .gemini import HAS_HTTPX
from .server import GeminiHandler, ThreadedServer
from . import __version__

APP_NAME = "Gemini ReverseEng API"


def _print_banner(port: int):
    keys = CONFIG.get("api_keys") or []
    api_key = keys[0] if keys else "disabled (--no-auth)"
    models = ", ".join(MODELS.keys())
    cookie = "yes ({})".format(CONFIG["cookie_file"]) if CONFIG.get("cookie_file") else "none (anonymous)"
    proxy = CONFIG.get("proxy") or "system env (HTTP_PROXY/HTTPS_PROXY)"
    streaming = "httpx (true streaming)" if HAS_HTTPX else "urllib (buffered)"
    temporary = "yes" if CONFIG.get("temporary_chats", False) else "no"
    auth_line = (
        "API Key        : {}".format(api_key)
        if keys
        else "API Key        : disabled (authentication is off)"
    )

    line = "=" * 66
    print(line)
    print("  {}  v{}".format(APP_NAME, __version__))
    print("  OpenAI-compatible gateway for Google Gemini Web")
    print(line)
    print()
    print("  Base URL       : http://localhost:{}/v1".format(port))
    print("  {}".format(auth_line))
    print("  Default Model  : {}".format(CONFIG["default_model"]))
    print("  Listening      : http://{}:{}".format(CONFIG["host"], port))
    print("  Health Check   : http://localhost:{}/health".format(port))
    print("  Models         : {}".format(models))
    print("  Cookie         : {}".format(cookie))
    print("  Proxy          : {}".format(proxy))
    print("  Streaming      : {}".format(streaming))
    print("  Temporary      : {}".format(temporary))
    print()
    print("  Endpoints")
    print("    POST /v1/chat/completions")
    print("    POST /v1/responses")
    print("    GET  /v1/models")
    print("    GET  /v1beta/models")
    print("    POST /v1beta/models/{model}:generateContent")
    print("    POST /v1beta/models/{model}:streamGenerateContent")
    print("    GET  /health")
    print()
    if keys:
        print("  Use this key as:  Authorization: Bearer <API Key>")
        if CONFIG.get("api_key_file"):
            print("  Key file        : {}".format(CONFIG["api_key_file"]))
    else:
        print("  Authentication is disabled. Any API key (or none) is accepted.")
    print(line)
    print()


def main():
    parser = argparse.ArgumentParser(description="Gemini Web to OpenAI API")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--cookie-file", type=str, default=None)
    parser.add_argument("--proxy", type=str, default=None, help="HTTP proxy, e.g. http://127.0.0.1:7890")
    parser.add_argument("--api-key", type=str, default=None,
                        help="API key(s) clients must send, comma-separated. Default: auto-generated sk-local-... key")
    parser.add_argument("--no-auth", action="store_true",
                        help="Disable API key authentication entirely")
    parser.add_argument("--version", action="version", version=f"gemini-web2api {__version__}")
    args = parser.parse_args()

    config_path = args.config or os.environ.get("GEMINI_WEB2API_CONFIG") or find_config()
    if config_path:
        load_config(config_path)

    if args.port:
        CONFIG["port"] = args.port
    if args.cookie_file:
        CONFIG["cookie_file"] = args.cookie_file
    if args.proxy:
        CONFIG["proxy"] = args.proxy
    if args.no_auth:
        CONFIG["api_keys"] = []
    elif args.api_key:
        keys = [k.strip() for k in args.api_key.split(",") if k.strip()]
        CONFIG["api_keys"] = keys
    else:
        ensure_api_key()

    port = CONFIG["port"]
    server = ThreadedServer((CONFIG["host"], port), GeminiHandler)
    _print_banner(port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()


if __name__ == "__main__":
    main()

"""
╔══════════════════════════════════════════════════════════════╗
║  RIDOS OS v1.1 — AI Daemon                                  ║
║  Copyright (C) 2026 RIDOS OS Project                        ║
║  Licensed under GNU General Public License v3 (GPL-3.0)     ║
║  https://github.com/ridos-os/ridos-os                       ║
╚══════════════════════════════════════════════════════════════╝

Core AI engine. Runs as a background systemd service.
Listens on Unix socket, routes requests to Claude API (online)
or local model (offline fallback).
"""

import asyncio
import json
import os
import signal
import sys
from collections import OrderedDict
from datetime import datetime

SOCKET_PATH   = "/run/ridos.sock"
API_KEY_FILE  = "/etc/ridos/api.key"
CONFIG_FILE   = "/etc/ridos/config.json"
LOG_FILE      = "/var/log/ridos/daemon.log"
VERSION       = "1.1.0"

ONLINE_MODEL  = "claude-haiku-4-5-20251001"
MAX_TOKENS    = 512
CACHE_SIZE    = 30
RATE_LIMIT    = 15  # requests per minute

SYSTEM_PROMPT = """You are RIDOS, an AI assistant built into RIDOS OS v1.1 "Basra" — 
a professional Linux distribution for IT specialists, network engineers, and developers.

You have deep knowledge of:
- Linux system administration and troubleshooting
- Network protocols (TCP/IP, DNS, HTTP, SSH, etc.)
- Security tools (nmap, wireshark, tcpdump, etc.)
- Python, Bash, and general programming
- IT infrastructure and server management

When a user asks about IT tasks, suggest specific Linux commands they can run.
When showing commands, wrap them in backticks.
Be concise, practical, and professional.
The system runs on both old and modern hardware."""

# ── Logging ───────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{level}] {ts} — {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ── Config & Key ──────────────────────────────────────────────
def load_config() -> dict:
    defaults = {
        "online_model": ONLINE_MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.7,
        "enable_offline_fallback": False,
        "enable_web_search": True,
        "enable_it_tools": True,
    }
    try:
        with open(CONFIG_FILE) as f:
            return {**defaults, **json.load(f)}
    except Exception:
        return defaults

def read_api_key() -> str:
    if not os.path.exists(API_KEY_FILE):
        raise FileNotFoundError(f"API key not found at {API_KEY_FILE}")
    key = open(API_KEY_FILE).read().strip()
    if not key or key in ("CONFIGURE_ON_FIRST_BOOT", "YOUR_API_KEY"):
        raise ValueError("API key not configured. Run: ridos-setup")
    return key

# ── Claude API ────────────────────────────────────────────────
async def call_claude(prompt: str, history: list, cfg: dict) -> str:
    import httpx
    key = read_api_key()
    messages = history[-10:] + [{"role": "user", "content": prompt}]

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": cfg.get("online_model", ONLINE_MODEL),
                "max_tokens": cfg.get("max_tokens", MAX_TOKENS),
                "system": SYSTEM_PROMPT,
                "messages": messages
            }
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]

# ── Internet check ────────────────────────────────────────────
async def check_internet() -> bool:
    import socket
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: socket.create_connection(("8.8.8.8", 53), timeout=3)
        )
        return True
    except Exception:
        return False

# ── Request cache ─────────────────────────────────────────────
_cache: OrderedDict = OrderedDict()
_request_times: list = []

def cache_get(key: str):
    return _cache.get(key)

def cache_set(key: str, value):
    if len(_cache) >= CACHE_SIZE:
        _cache.popitem(last=False)
    _cache[key] = value

def is_rate_limited() -> bool:
    now = asyncio.get_event_loop().time()
    _request_times[:] = [t for t in _request_times if now - t < 60]
    if len(_request_times) >= RATE_LIMIT:
        return True
    _request_times.append(now)
    return False

# ── Client handler ────────────────────────────────────────────
async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        data = await asyncio.wait_for(reader.read(16384), timeout=10)
        if not data:
            return

        payload = json.loads(data.decode("utf-8"))
        prompt  = payload.get("prompt", "").strip()
        history = payload.get("context", [])

        if not prompt:
            writer.write(json.dumps({"response": "Empty prompt.", "model": "error"}).encode())
            await writer.drain()
            return

        # Cache lookup
        cache_key = prompt.lower()[:120]
        cached = cache_get(cache_key)
        if cached:
            response, model = cached
            log(f"Cache hit: {prompt[:50]}")
        else:
            cfg = load_config()
            online = await check_internet()

            try:
                # ── IT tools intent check ──
                response, model = None, None
                if cfg.get("enable_it_tools"):
                    try:
                        from intent_parser import IntentParser
                        handled, result = IntentParser().handle(prompt)
                        if handled:
                            response, model = result, "system"
                    except ImportError:
                        pass

                # ── Web search augmentation ──
                if response is None and online and cfg.get("enable_web_search"):
                    try:
                        from web_search import is_search_query, web_search, format_result
                        if is_search_query(prompt):
                            sr = await web_search(prompt)
                            context = format_result(sr)
                            augmented = f"[Web Search Results]\n{context}\n\nUser question: {prompt}"
                            response = await call_claude(augmented, history, cfg)
                            model = "online+search"
                    except ImportError:
                        pass

                # ── Claude API ──
                if response is None:
                    if online:
                        response = await call_claude(prompt, history, cfg)
                        model = "online"
                    elif cfg.get("enable_offline_fallback"):
                        response = "⚠ No internet connection. Offline model not configured."
                        model = "offline"
                    else:
                        response = "⚠ No internet connection. Connect to use RIDOS AI."
                        model = "error"

            except Exception as e:
                response = f"⚠ Error: {str(e)}"
                model = "error"
                log(f"Handler error: {e}", "ERROR")

            if model not in ("error",):
                cache_set(cache_key, (response, model))

        result = json.dumps({
            "response": response,
            "model": model,
            "version": VERSION
        }, ensure_ascii=False)

        writer.write(result.encode("utf-8"))
        await writer.drain()

    except json.JSONDecodeError:
        err = json.dumps({"response": "Invalid JSON payload.", "model": "error"})
        writer.write(err.encode())
        await writer.drain()
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
    finally:
        writer.close()

# ── Main ──────────────────────────────────────────────────────
async def main():
    log(f"RIDOS OS v{VERSION} AI Daemon starting...", "OK")
    log(f"Copyright (C) 2026 RIDOS OS Project — GPL v3", "INFO")
    log(f"Socket: {SOCKET_PATH}", "INFO")

    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = await asyncio.start_unix_server(handle_client, SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: (server.close(), log("Daemon stopped.", "INFO")))

    online = await check_internet()
    log(f"Network: {'ONLINE' if online else 'OFFLINE'}", "INFO")
    log("Ready. Listening for requests...", "OK")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())

"""Thin HTTP wrapper around the vanilla baseline.

Serves POST /chat with {messages, session_metadata, session_context} and
returns {"reply": ...}. This is the structurally-different serving path that
lets the harness prove it works against an arbitrary HTTP endpoint (rubric A2),
not just an in-process Anthropic call. The prompt is ONE neutral generic
sentence (subject/vanilla_prompt.txt) — nothing of ours, no guardrail layer.
"""

from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from jahoda.config import MODELS
from jahoda.llm import chat
from jahoda.subject import vanilla_prompt

log = logging.getLogger("jahoda.vanilla")


def _make_handler(model: str):
    system = vanilla_prompt()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence default stderr logging
            return

        def do_POST(self):
            if self.path != "/chat":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or "{}")
            messages = body.get("messages", [])
            ctx = body.get("session_context") or ""
            sys = f"{system}\n\n{ctx}" if ctx else system
            try:
                reply = chat(
                    model=model,
                    system=sys,
                    messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                    max_tokens=600,
                    temperature=0.0,
                    cache_system=True,
                )
                payload = {"reply": reply}
                code = 200
            except Exception as e:  # surfaced to the adapter as a non-200
                log.warning("vanilla server error: %s", e)
                payload = {"error": str(e)}
                code = 502
            data = json.dumps(payload).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve_in_thread(port: int = 8900, model: str | None = None) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(model or MODELS.subject))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    log.info("vanilla baseline serving on http://127.0.0.1:%d/chat", port)
    return server


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    srv = serve_in_thread()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()

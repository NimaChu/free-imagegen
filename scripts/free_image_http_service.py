#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from free_image_gen import generate_image, generate_openclaw_assets


class Handler(BaseHTTPRequestHandler):
    server_version = "FreeImageGenHTTP/1.0"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json(200, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "free-imagegen-local-svg"})
            return
        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
        except Exception as exc:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {exc}"})
            return

        try:
            if self.path == "/generate":
                prompt = str(payload.get("prompt", "")).strip()
                if not prompt:
                    raise ValueError("Field 'prompt' is required")

                output = payload.get("output")
                if output:
                    output_path = Path(str(output)).expanduser().resolve()
                else:
                    output_path = Path.cwd() / "output" / "imagegen" / "generated-local.png"

                svg_output = payload.get("svg_output")
                svg_path = Path(str(svg_output)).expanduser().resolve() if svg_output else None

                result = generate_image(
                    prompt=prompt,
                    output=output_path,
                    width=int(payload.get("width", 1024)),
                    height=int(payload.get("height", 1024)),
                    svg_output=svg_path,
                )
                self._send_json(200, {"ok": True, "result": result})
                return

            if self.path == "/openclaw-assets":
                prompt = str(payload.get("prompt", "")).strip()
                project = str(payload.get("project", "")).strip()
                if not prompt:
                    raise ValueError("Field 'prompt' is required")
                if not project:
                    raise ValueError("Field 'project' is required")

                result = generate_openclaw_assets(
                    project_dir=project,
                    prompt=prompt,
                )
                self._send_json(200, {"ok": True, "result": result})
                return

            self._send_json(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HTTP wrapper for local free-imagegen (SVG -> PNG)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving Free ImageGen on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

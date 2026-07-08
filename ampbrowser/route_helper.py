from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any

from .config import AppConfig, load_config
from .routing import route_url
from .transport_manager import ManagedTransportResult, ensure_transport_ready, transport_status


SUPPORTED_HELPER_TRANSPORTS = {"tor", "i2p"}


def handle_helper_message(
    message: dict[str, Any],
    *,
    root: Path,
    config: AppConfig,
) -> dict[str, Any]:
    action = _string(message.get("action"))
    transport = _message_transport(message)
    if not transport:
        return _error_response("unsupported-route", "URL does not route to a managed browser transport")
    if transport not in SUPPORTED_HELPER_TRANSPORTS:
        return _error_response("unsupported-transport", f"{transport} is not supported by the route helper yet")

    if action == "status":
        return _result_response(transport_status(transport, config=config, root=root))
    if action == "ensure":
        return _result_response(ensure_transport_ready(transport, config=config, root=root))
    return _error_response("unsupported-action", f"unsupported helper action: {action or '-'}")


def serve_route_helper(
    *,
    host: str,
    port: int,
    token: str,
    root: Path,
    config_path: Path | None = None,
) -> None:
    config = load_config(root, config_path)
    server = _RouteHelperServer((host, port), _RouteHelperHandler)
    server.token = token
    server.root_path = root
    server.config = config
    server.serve_forever()


class _RouteHelperServer(ThreadingHTTPServer):
    token: str
    root_path: Path
    config: AppConfig


class _RouteHelperHandler(BaseHTTPRequestHandler):
    server: _RouteHelperServer

    def do_OPTIONS(self) -> None:
        self._write_json(200, {"ok": True})

    def do_POST(self) -> None:
        if self.headers.get("X-AMPB-Token") != self.server.token:
            self._write_json(403, _error_response("forbidden", "invalid helper token"))
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._write_json(400, _error_response("bad-json", "request body is not valid JSON"))
            return
        if not isinstance(payload, dict):
            self._write_json(400, _error_response("bad-request", "request body must be a JSON object"))
            return
        response = handle_helper_message(payload, root=self.server.root_path, config=self.server.config)
        self._write_json(200 if response.get("ok") else 400, response)

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AMPB-Token")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _message_transport(message: dict[str, Any]) -> str:
    raw_transport = _string(message.get("transport"))
    if raw_transport:
        return raw_transport
    raw_url = _string(message.get("url"))
    if not raw_url:
        return ""
    return route_url(raw_url).transport


def _result_response(result: ManagedTransportResult) -> dict[str, Any]:
    return {
        "ok": True,
        "transport": result.transport,
        "provider": result.provider,
        "provider_source": result.provider_source,
        "status": result.status,
        "ready": result.ready,
        "owned": result.owned,
        "pid": result.pid,
        "endpoint": result.endpoint,
        "state_dir": result.state_dir,
        "message": result.message,
        "command": list(result.command),
    }


def _error_response(status: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "ready": False,
        "message": message,
    }


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""

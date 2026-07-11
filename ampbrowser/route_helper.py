from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from typing import Any

from .broker import BrokerRouteError, open_brokered_url
from .config import AppConfig, load_config
from .launch import OpenPlan
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
    if action == "open":
        raw_url = _string(message.get("url"))
        if not raw_url:
            return _error_response("missing-url", "broker open requires a URL")
        try:
            open_plan = open_brokered_url(
                raw_url,
                expected_transport=transport,
                consent=message.get("consent") is True,
                config=config,
                root=root,
            )
        except BrokerRouteError as exc:
            return _error_response("route-mismatch", str(exc))
        transport_result = None
        if open_plan.status not in {"launched", "opened-existing"}:
            transport_result = transport_status(transport, config=config, root=root)
        return _open_response(open_plan, transport_result)
    return _error_response("unsupported-action", f"unsupported helper action: {action or '-'}")


def serve_route_helper(
    *,
    host: str,
    port: int,
    token: str,
    root: Path,
    config_path: Path | None = None,
    watch_pid: int = 0,
) -> None:
    config = load_config(root, config_path)
    server = _RouteHelperServer((host, port), _RouteHelperHandler)
    server.token = token
    server.root_path = root
    server.config = config
    if watch_pid > 0:
        watcher = threading.Thread(target=_shutdown_when_pid_exits, args=(server, watch_pid), daemon=True)
        watcher.start()
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
        "setup_hint": result.setup_hint,
        "install_command": list(result.install_command),
    }


def _open_response(
    open_plan: OpenPlan,
    transport_result: ManagedTransportResult | None,
) -> dict[str, Any]:
    route = open_plan.browse_plan.route
    opened = open_plan.status in {"launched", "opened-existing"}
    return {
        "ok": True,
        "transport": route.transport,
        "profile": route.profile,
        "status": open_plan.status,
        "ready": opened,
        "launched": opened,
        "requires_consent": open_plan.status == "consent-required",
        "consent_granted": open_plan.consent_granted,
        "browser_pid": open_plan.browser_pid,
        "profile_path": open_plan.profile_path,
        "message": open_plan.message,
        "setup_prompt_title": open_plan.setup_prompt_title,
        "setup_prompt_body": open_plan.setup_prompt_body,
        "setup_prompt_approve_label": open_plan.setup_prompt_approve_label,
        "setup_hint": transport_result.setup_hint if transport_result else "-",
        "install_command": list(transport_result.install_command) if transport_result else [],
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


def _shutdown_when_pid_exits(server: _RouteHelperServer, pid: int, *, interval_seconds: float = 1.0) -> None:
    while _pid_exists(pid):
        time.sleep(interval_seconds)
    server.shutdown()


def _pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True

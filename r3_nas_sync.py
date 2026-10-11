"""R3∞ Synology NAS backend adapter.

Uses WebDAV over HTTPS and environment variables only.
No credentials are stored in source code.

Required env:
  R3_NAS_BASE_URL   e.g. https://nas.example.com:5006
  R3_NAS_USERNAME
  R3_NAS_PASSWORD
Optional:
  R3_NAS_ROOT       default: /R3_INFINITY

The adapter is intentionally conservative: it never deletes remote history.
It writes versioned objects and can read/list the R3 namespace.
"""
from __future__ import annotations

import base64
import json
import os
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


class NASConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class NASConfig:
    base_url: str
    username: str
    password: str
    root: str = "/R3_INFINITY"

    @classmethod
    def from_env(cls) -> "NASConfig":
        base = os.getenv("R3_NAS_BASE_URL", "").strip().rstrip("/")
        user = os.getenv("R3_NAS_USERNAME", "").strip()
        password = os.getenv("R3_NAS_PASSWORD", "")
        root = os.getenv("R3_NAS_ROOT", "/R3_INFINITY").strip() or "/R3_INFINITY"
        if not base or not user or not password:
            raise NASConfigError("R3 NAS non configurato: servono BASE_URL, USERNAME e PASSWORD via environment.")
        if not base.startswith("https://"):
            raise NASConfigError("R3_NAS_BASE_URL deve usare HTTPS.")
        return cls(base, user, password, "/" + root.strip("/"))


class SynologyWebDAV:
    def __init__(self, config: NASConfig | None = None, timeout: int = 20):
        self.cfg = config or NASConfig.from_env()
        self.timeout = timeout
        token = base64.b64encode(f"{self.cfg.username}:{self.cfg.password}".encode()).decode()
        self.auth = f"Basic {token}"
        self.ssl_context = ssl.create_default_context()

    def _url(self, path: str = "") -> str:
        safe = "/".join(urllib.parse.quote(p) for p in path.strip("/").split("/") if p)
        root = self.cfg.root.strip("/")
        suffix = "/".join(x for x in (root, safe) if x)
        return f"{self.cfg.base_url}/{suffix}"

    def _request(self, method: str, path: str = "", data: bytes | None = None, headers: dict | None = None):
        h = {"Authorization": self.auth, "User-Agent": "R3-Infinity/1.0"}
        if headers:
            h.update(headers)
        req = urllib.request.Request(self._url(path), data=data, headers=h, method=method)
        return urllib.request.urlopen(req, timeout=self.timeout, context=self.ssl_context)

    def ensure_collection(self, path: str = "") -> None:
        parts = [p for p in path.strip("/").split("/") if p]
        current = ""
        for part in parts:
            current = f"{current}/{part}".strip("/")
            try:
                with self._request("MKCOL", current):
                    pass
            except urllib.error.HTTPError as e:
                if e.code not in (405, 409):
                    raise

    def put_bytes(self, path: str, payload: bytes, content_type: str = "application/octet-stream") -> None:
        parent = "/".join(path.strip("/").split("/")[:-1])
        if parent:
            self.ensure_collection(parent)
        with self._request("PUT", path, payload, {"Content-Type": content_type}) as r:
            if r.status not in (200, 201, 204):
                raise RuntimeError(f"NAS PUT fallito: HTTP {r.status}")

    def put_json_versioned(self, logical_name: str, obj: dict) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe = logical_name.replace("/", "_")
        path = f"ledger/{safe}/{stamp}.json"
        body = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        self.put_bytes(path, body, "application/json; charset=utf-8")
        return path

    def get_bytes(self, path: str) -> bytes:
        with self._request("GET", path) as r:
            return r.read()

    def list(self, path: str = "") -> list[str]:
        headers = {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"}
        body = b'<?xml version="1.0"?><propfind xmlns="DAV:"><prop><displayname/></prop></propfind>'
        with self._request("PROPFIND", path, body, headers) as r:
            xml = r.read()
        root = ET.fromstring(xml)
        out: list[str] = []
        for href in root.findall(".//{DAV:}href"):
            if href.text:
                out.append(urllib.parse.unquote(href.text))
        return out

    def health(self) -> dict:
        try:
            items = self.list("")
            return {"ok": True, "root": self.cfg.root, "items_seen": len(items)}
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:300]}


def snapshot_to_nas(name: str, payload: dict) -> dict:
    """Write an immutable, timestamped R3 snapshot. Never deletes older snapshots."""
    nas = SynologyWebDAV()
    path = nas.put_json_versioned(name, payload)
    return {"ok": True, "path": path, "health": nas.health()}

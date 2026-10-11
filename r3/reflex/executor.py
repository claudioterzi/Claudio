"""Closed-catalog desktop executor for the R3 reflex candidate."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import shutil
import subprocess
from typing import Any, Mapping
from urllib.parse import quote_plus
import webbrowser

from .decider import Decision


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    action: str
    detail: str


def _run(args: list[str], timeout: int = 15) -> str:
    try:
        proc = subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout)
        return (proc.stdout or proc.stderr or "").strip()[:500]
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def _known(mapping: Mapping[str, str], target: str) -> str | None:
    if target in mapping:
        return str(mapping[target])
    low = str(target).lower()
    for key, value in mapping.items():
        if str(key).lower() == low:
            return str(value)
    return None


def open_app(executable: str) -> str:
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(["cmd", "/c", "start", "", executable])
        return f"opened {executable}"
    if system == "Darwin":
        return _run(["open", "-a", executable]) or f"opened {executable}"
    binary = shutil.which(executable)
    if not binary:
        return f"app not found: {executable}"
    subprocess.Popen([binary], start_new_session=True)
    return f"opened {binary}"


def close_app(executable: str) -> str:
    name = Path(executable).name
    if platform.system() == "Windows":
        return _run(["taskkill", "/IM", name, "/F"]) or f"closed {name}"
    return _run(["pkill", "-f", name]) or f"closed {name}"


def open_folder(path: str) -> str:
    expanded = os.path.expandvars(os.path.expanduser(path))
    if not Path(expanded).exists():
        return f"folder not found: {expanded}"
    if platform.system() == "Windows":
        subprocess.Popen(["explorer", expanded])
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", expanded])
    else:
        subprocess.Popen(["xdg-open", expanded])
    return f"folder {expanded}"


def set_clipboard(text: str) -> str:
    if not text:
        return "no text"
    system = platform.system()
    if system == "Windows":
        proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True)
        proc.communicate(text)
    elif system == "Darwin":
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
        proc.communicate(text)
    elif shutil.which("wl-copy"):
        proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
        proc.communicate(text)
    elif shutil.which("xclip"):
        proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
        proc.communicate(text)
    else:
        return "clipboard backend unavailable"
    return f"clipboard {len(text)} chars"


def set_volume(percent: float) -> str:
    percent = max(0, min(100, int(percent)))
    if platform.system() == "Darwin":
        _run(["osascript", "-e", f"set volume output volume {percent}"])
        return f"volume {percent}%"
    if shutil.which("pactl"):
        _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percent}%"])
        return f"volume {percent}%"
    if shutil.which("nircmd"):
        _run(["nircmd", "setsysvolume", str(int(percent * 65535 / 100))])
        return f"volume {percent}%"
    return "volume backend unavailable"


def mute(on: bool) -> str:
    if platform.system() == "Darwin":
        _run(["osascript", "-e", f"set volume output muted {'true' if on else 'false'}"])
        return "muted" if on else "audio on"
    if shutil.which("pactl"):
        _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if on else "0"])
        return "muted" if on else "audio on"
    return "mute backend unavailable"


def screenshot() -> str:
    desktop = Path.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = desktop / f"r3-reflex-{stamp}.png"
    try:
        from PIL import ImageGrab
        image = ImageGrab.grab()
        image.save(destination)
        return str(destination)
    except Exception as exc:
        return f"screenshot unavailable: {type(exc).__name__}"


def open_youtube(query: str) -> str:
    cleaned = (query or "").strip()
    if cleaned.lower() in {"", "youtube", "metti un video"}:
        url = "https://www.youtube.com"
    else:
        url = "https://www.youtube.com/results?search_query=" + quote_plus(cleaned)
    webbrowser.open(url)
    return url


def execute(decision: Decision, config: Mapping[str, Any]) -> ExecutionResult:
    apps = dict(config.get("apps") or {})
    folders = dict(config.get("folders") or {})
    action = decision.action
    target = decision.target

    if action == "open_app":
        executable = _known(apps, target)
        return ExecutionResult(False, action, "target outside catalog") if not executable else ExecutionResult(True, action, open_app(executable))
    if action == "close_app":
        executable = _known(apps, target)
        return ExecutionResult(False, action, "target outside catalog") if not executable else ExecutionResult(True, action, close_app(executable))
    if action == "open_folder":
        path = _known(folders, target)
        return ExecutionResult(False, action, "target outside catalog") if not path else ExecutionResult(True, action, open_folder(path))
    if action == "dictate":
        return ExecutionResult(True, action, set_clipboard(decision.text_payload))
    if action == "set_volume":
        if decision.volume is None:
            return ExecutionResult(False, action, "missing volume")
        return ExecutionResult(True, action, set_volume(decision.volume))
    if action == "mute":
        return ExecutionResult(True, action, mute(True))
    if action == "unmute":
        return ExecutionResult(True, action, mute(False))
    if action == "screenshot":
        return ExecutionResult(True, action, screenshot())
    if action == "youtube":
        return ExecutionResult(True, action, open_youtube(decision.text_payload))
    return ExecutionResult(False, action, "no action")

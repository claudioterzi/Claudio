"""Private probe wrapper extending OFFLINE_GUARD_WRAPPER_20261008.py.

This is a test guard for the unchanged loader, not an OS sandbox or runtime.
"""
import contextlib
import fcntl
import io
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import sysconfig


fixture = Path(sys.argv[1]).resolve(strict=True)
original_source = Path(sys.argv[2])
script = fixture / "scripts/r3_ai_bootstrap.py"
loader_args = sys.argv[3:]
stdlib = Path(sysconfig.get_path("stdlib")).resolve(strict=True)
startup_environment_names = sorted(os.environ)
if not set(startup_environment_names).issubset({"LC_CTYPE"}):
    raise RuntimeError("unexpected child startup environment")
os.environ.clear()
attempts = []
allowed_reads = []


def inside(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def safe_path(raw):
    if isinstance(raw, int):
        # fdopen emits open(fd:int): check the actual readonly descriptor target.
        flags = fcntl.fcntl(raw, fcntl.F_GETFL)
        if flags & os.O_ACCMODE != os.O_RDONLY:
            raise RuntimeError("guard denied writable descriptor")
        target = os.readlink("/proc/self/fd/" + str(raw))
        if target.endswith(" (deleted)"):
            raise RuntimeError("guard denied deleted descriptor target")
        raw = target
    return Path(os.fsdecode(raw)).resolve()


def read_allowed(path):
    if inside(path, fixture):
        return "fixture"
    if inside(path, stdlib) and "site-packages" not in path.parts and "dist-packages" not in path.parts:
        return "stdlib"
    return None


def deny(event, operation, reason):
    attempts.append({"event": event, "operation": operation, "reason": reason})
    raise RuntimeError("recovery guard rejected " + reason)


def guard(event, args):
    if event.startswith("socket."):
        deny(event, "network", "network or DNS")
    if event == "subprocess.Popen" or event in {"os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"} or event.startswith("os.spawn"):
        deny(event, "subprocess", "subprocess or process creation")
    if event == "open":
        raw, mode, flags = args
        if isinstance(mode, str) and any(character in mode for character in "wax+"):
            deny(event, "write", "file write")
        if isinstance(flags, int) and (flags & os.O_ACCMODE != os.O_RDONLY or flags & (os.O_APPEND | os.O_CREAT | os.O_TRUNC)):
            deny(event, "write", "file write flags")
        try:
            path = safe_path(raw)
        except (OSError, ValueError, TypeError, RuntimeError):
            deny(event, "read", "unresolvable or non-readonly descriptor")
        location = read_allowed(path)
        if location is None:
            deny(event, "read", "read outside fixture and stdlib")
        allowed_reads.append({"scope": location, "path": str(path), "descriptor": isinstance(raw, int)})
    if event in {"os.listdir", "os.scandir"}:
        try:
            path = safe_path(args[0])
        except (OSError, ValueError, TypeError, RuntimeError):
            deny(event, "read", "directory target invalid")
        if read_allowed(path) is None:
            deny(event, "read", "directory read outside fixture and stdlib")
    if event in {
        "os.mkdir", "os.rmdir", "os.remove", "os.rename", "os.link", "os.symlink",
        "os.truncate", "os.chmod", "os.chown", "os.utime", "os.chdir", "os.fchdir",
        "os.mknod", "os.mkfifo", "shutil.copyfile", "shutil.copymode", "shutil.copystat",
    }:
        deny(event, "mutation", "filesystem mutation")


sys.addaudithook(guard)
controls = {}
control_actions = [
    ("read_outside", lambda: open(__file__, "rb").read()),
    ("read_original_source", lambda: open(original_source, "rb").read()),
    ("write_outside", lambda: open(__file__ + ".blocked-write", "wb")),
    ("write_inside", lambda: open(fixture / "public/r3-ai-bootstrap.json", "wb")),
    ("mkdir_inside", lambda: os.mkdir(fixture / "guard-blocked-directory")),
    ("socket", lambda: socket.socket()),
    ("dns", lambda: socket.getaddrinfo("example.invalid", 443)),
    ("subprocess", lambda: subprocess.Popen([sys.executable, "-c", "pass"])),
]
for name, action in control_actions:
    before = len(attempts)
    try:
        action()
    except RuntimeError as exc:
        controls[name] = {"blocked": True, "error": str(exc), "events": attempts[before:]}
    except Exception as exc:
        controls[name] = {"blocked": False, "error": type(exc).__name__, "events": attempts[before:]}
    else:
        controls[name] = {"blocked": False, "error": "operation unexpectedly accepted", "events": attempts[before:]}

before_attempts = len(attempts)
before_reads = len(allowed_reads)
stdout = io.StringIO()
stderr = io.StringIO()
sys.argv = [str(script)] + loader_args
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    try:
        runpy.run_path(str(script), run_name="__main__")
        code = 0
    except SystemExit as exc:
        code = exc.code
    except Exception as exc:
        code = 1
        stderr.write(type(exc).__name__ + ": " + str(exc))
records = []
for line in stdout.getvalue().splitlines():
    try:
        records.append(json.loads(line))
    except json.JSONDecodeError:
        records.append({"non_json_output": True})
print(json.dumps({
    "schema": "R3_PROVIDER_LOSS_GUARDED_LOADER/1.0",
    "loader_exit_code": code,
    "stdout_records": records,
    "stderr": stderr.getvalue(),
    "guard_controls": controls,
    "loader_denied_operations": attempts[before_attempts:],
    "loader_allowed_reads": allowed_reads[before_reads:],
    "startup_environment_names": startup_environment_names,
    "environment_entry_count": len(os.environ),
    "python_isolated": sys.flags.isolated,
    "python_no_site": sys.flags.no_site,
    "python_no_bytecode": sys.flags.dont_write_bytecode,
    "third_party_module_origins": [name for name, module in sys.modules.copy().items() if "site-packages" in str(getattr(module, "__file__", ""))],
    "guard_scope": "Python auditable opens, mutations, socket/DNS and process creation; unchanged trusted loader only; not an OS sandbox or airgap",
}, ensure_ascii=False))
raise SystemExit(code if isinstance(code, int) else 1)

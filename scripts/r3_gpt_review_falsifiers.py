"""Falsifiers for the external (GPT) review of PR #113 supervisor and PR #115 gate.

Each claim from the review is turned into an executable check. Output: CONFIRMED /
REFUTED / NOT_TESTED per claim. Stdlib only; httpx is stubbed (network disabled).
Usage: python3 scripts/r3_gpt_review_falsifiers.py <judge_worktree> <supervisor_worktree>
"""
import itertools, json, math, os, signal, subprocess, sys, tempfile, textwrap, time, types
from pathlib import Path
from unittest import mock

JUDGE, SUP = sys.argv[1], sys.argv[2]
sys.modules.setdefault("httpx", types.ModuleType("httpx"))
sys.path.insert(0, JUDGE)
from r3_judge.benchmark import summarize  # noqa: E402
sys.path.insert(0, SUP)
from r3.supervise_node import supervise  # noqa: E402

R = {}

def fixture():
    return [{"expected": "stub" if i < 5 else "real", "correct": True,
             "model": "M", "backend_fingerprint": "F",
             "id": f"case-{i}", "path": f"fixtures/case-{i}.txt"} for i in range(10)]

def verdict(cond):
    return "DEFECT_PRESENT" if cond else "DEFECT_ABSENT"

def adopts(rows, **kw):
    """True if the gate adopts invalid rows; False if it refuses or rejects them."""
    try:
        return summarize(rows, **kw)["adopt"] is True
    except ValueError:
        return False

# ---- Gate claims -------------------------------------------------------
rows = fixture(); [r.update(correct="false") for r in rows]
R["G1_correct_string_false_counted"] = verdict(adopts(rows))

rows = fixture(); [r.update(model=123, backend_fingerprint=456) for r in rows]
R["G2_non_string_identity_accepted"] = verdict(adopts(rows))

rows = fixture(); rows[0]["backend_fingerprint"] = " F "
R["G3_padded_fingerprint_equated"] = verdict(adopts(rows))

rows = fixture(); [r.update(model="wrong-model") for r in rows]
try:
    R["G4_unrequested_model_adopted"] = verdict(adopts(rows, expected_model="M"))
except TypeError:  # pre-fix summarize has no expected_model parameter
    R["G4_unrequested_model_adopted"] = verdict(adopts(rows))

rows = fixture(); [r.update(id="dup", path="same") for r in rows]
R["G5_duplicate_cases_accepted"] = verdict(adopts(rows))

passing = 0
for bits in itertools.product([0, 1], repeat=10):
    s, r_ = sum(bits[:5]), sum(bits[5:])
    if s + r_ >= 8 and s >= 4 and r_ >= 4:
        passing += 1
p8 = sum(math.comb(10, k) for k in (8, 9, 10)) / 1024
R["G6_chance_pass_36_of_1024"] = "CONFIRMED" if passing == 36 else "REFUTED"
R["G6_detail"] = {"gate_pass_combinations": passing, "p_gate_random": round(passing / 1024, 4),
                  "p_at_least_8_random": round(p8, 4)}

# ---- Supervisor claims -------------------------------------------------
# S1: SIGTERM during first Popen still starts the second child
real_popen = subprocess.Popen
starts = []
def fake_popen(cmd, **kw):
    starts.append(cmd)
    p = real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kw)
    if len(starts) == 1:
        signal.raise_signal(signal.SIGTERM)
    return p
with mock.patch("r3.supervise_node.subprocess.Popen", side_effect=fake_popen):
    rc = supervise([["a"], ["b"]], grace_seconds=1)
R["S1_child_started_after_sigterm"] = verdict(len(starts) == 2)
R["S1_detail"] = {"starts": len(starts), "rc": rc}

# S2: second Popen fails -> first child cleaned, non-zero outcome
work = Path(tempfile.mkdtemp(prefix="r3gpt_"))
TAG = "4%d" % 7319  # built at runtime so no command line contains the literal
code = ("import sys; sys.path.insert(0, %r)\nfrom r3.supervise_node import supervise\n"
        "supervise([['sleep', %r], ['/nonexistent/binary']], grace_seconds=1)" % (SUP, TAG))
p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
time.sleep(0.5)
alive = 0
for pid in filter(str.isdigit, os.listdir("/proc")):
    try:
        argv = open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
    except OSError:
        continue
    alive += argv[:2] == [b"sleep", TAG.encode()]
R["S2_popen_failure_leaves_orphan"] = verdict(not (p.returncode != 0 and alive == 0))
R["S2_detail"] = {"rc": p.returncode, "first_child_alive_after": alive,
                  "method": "exact argv match in /proc (pgrep -f gave a self-match false positive)"}

# S3: leader exits on SIGTERM at once; grandchild needs 2 s -> killed before grace?
marker = work / "grandchild_done"
grandchild = textwrap.dedent(f"""
import signal, time, sys
def h(*_):
    time.sleep(2); open({str(marker)!r}, 'w').write('ok'); sys.exit(0)
signal.signal(signal.SIGTERM, h)
while True: time.sleep(0.1)
""")
leader = textwrap.dedent(f"""
import subprocess, sys, signal, time
subprocess.Popen([sys.executable, '-c', {grandchild!r}])   # same process group
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
while True: time.sleep(0.1)
""")
runner = textwrap.dedent(f"""
import sys; sys.path.insert(0, {SUP!r})
from r3.supervise_node import supervise
sys.exit(supervise([[sys.executable, '-c', {leader!r}]], grace_seconds=5))
""")
p = subprocess.Popen([sys.executable, "-c", runner])
time.sleep(1.0)
t0 = time.monotonic(); p.send_signal(signal.SIGTERM); p.wait(timeout=30)
elapsed = round(time.monotonic() - t0, 2)
time.sleep(2.5)
R["S3_grandchild_killed_before_grace"] = verdict(not marker.exists())
R["S3_detail"] = {"supervisor_exit_seconds": elapsed, "grandchild_marker_written": marker.exists()}

# S4: zombie reaping as PID 1 -> requires container/PID namespace
R["S4_pid1_zombie_reaping"] = "NOT_TESTED (no PID namespace here; mechanism plausible)"
R["S5_drain_zero"] = "CONFIRMED_BY_CONFIG (production node-a has no RAILWAY_DEPLOYMENT_DRAINING_SECONDS; Railway default 0 s)"
R["S6_heartbeat_gap"] = "CONFIRMED_EARLIER (hung and failing sync not detected, harness 08:18)"

print(json.dumps(R, indent=2))

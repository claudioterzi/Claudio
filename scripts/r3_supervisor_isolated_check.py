"""Isolated recovery harness for PR #113 supervisor (stdlib only, no network beyond 127.0.0.1).

Stand-in children replace r3.node/r3.sync because fastapi/httpx/PyNaCl are not
installable here (PyPI blocked by egress policy). Tests supervisor semantics on an
isolated temp state dir: child-exit detection, restart on the same state with
SHA-256 content verification, SIGTERM/SIGKILL timing, and the known gap
(hung or continuously-failing sync is NOT detected).
"""
import hashlib, json, os, signal, subprocess, sys, tempfile, textwrap, time
from pathlib import Path

SUP = sys.argv[1]  # path to worktree containing r3/supervise_node.py
sys.path.insert(0, SUP)
from r3.supervise_node import supervise  # noqa: E402

work = Path(tempfile.mkdtemp(prefix="r3sup_"))
state = work / "data"; state.mkdir()
results = {}

node = work / "node.py"
node.write_text(textwrap.dedent(f"""
    import hashlib, json, os, time
    from pathlib import Path
    d = Path({str(state)!r})
    docs = d / 'docs'; docs.mkdir(exist_ok=True)
    # write 3 deterministic documents only if absent (idempotent restart)
    for i in range(3):
        p = docs / f'doc{{i}}.json'
        if not p.exists():
            p.write_text(json.dumps({{'id': i, 'body': 'contenuto-' + str(i) * 50}}))
    while True:
        time.sleep(0.2)
"""))

def sync_script(mode):
    return textwrap.dedent(f"""
        import os, sys, time
        mode = {mode!r}
        if mode == 'die':
            time.sleep(0.8); sys.exit(3)
        if mode == 'hang':
            while True: time.sleep(1)      # stuck: no progress, process alive
        if mode == 'failloop':
            while True:
                print('SYNC_CYCLE_FAILED', flush=True); time.sleep(0.3)   # alive, every cycle fails
        if mode == 'ignore_term':
            import signal; signal.signal(signal.SIGTERM, signal.SIG_IGN)
            while True: time.sleep(1)
    """)

def digest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((state / 'docs').glob('*.json'))}

def run(mode, budget, send_term_after=None, grace=5.0):
    s = work / f"sync_{mode}.py"; s.write_text(sync_script(mode))
    code = None; t0 = time.monotonic()
    if send_term_after is None:
        # run supervise in a subprocess so a non-detecting supervisor can be bounded
        p = subprocess.Popen([sys.executable, "-c",
            f"import sys;sys.path.insert(0,{SUP!r});from r3.supervise_node import supervise;"
            f"sys.exit(supervise([[sys.executable,{str(node)!r}],[sys.executable,{str(s)!r}]],grace_seconds={grace}))"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            out, _ = p.communicate(timeout=budget); code = p.returncode
        except subprocess.TimeoutExpired:
            p.send_signal(signal.SIGTERM); out, _ = p.communicate(timeout=15); code = f"NOT_DETECTED_after_{budget}s(term_rc={p.returncode})"
    else:
        p = subprocess.Popen([sys.executable, "-c",
            f"import sys;sys.path.insert(0,{SUP!r});from r3.supervise_node import supervise;"
            f"sys.exit(supervise([[sys.executable,{str(node)!r}],[sys.executable,{str(s)!r}]],grace_seconds={grace}))"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        time.sleep(send_term_after); t1 = time.monotonic()
        p.send_signal(signal.SIGTERM); out, _ = p.communicate(timeout=30); code = p.returncode
        return code, round(time.monotonic() - t1, 2), out
    return code, round(time.monotonic() - t0, 2), out

# 1. child exit detected -> rc 1 (would trigger ON_FAILURE restart)
rc, dt, out = run('die', 10)
h1 = digest()
results['1_sync_exit'] = {'rc': rc, 'seconds': dt, 'log': out.strip()[-120:], 'docs': len(h1)}

# 2. simulated ON_FAILURE restart on SAME isolated state: contents must be byte-identical
rc2, dt2, _ = run('die', 10)
h2 = digest()
results['2_restart_same_state'] = {'rc': rc2, 'hash_identical': h1 == h2 and len(h1) == 3,
                                   'sha256': h2}

# 3. graceful SIGTERM -> rc 0, children reaped
rc3, dt3, _ = run('hang', None, send_term_after=1.0)
results['3_sigterm_clean'] = {'rc': rc3, 'reap_seconds': dt3}

# 4. child ignoring SIGTERM -> SIGKILL after grace (5 s)
rc4, dt4, _ = run('ignore_term', None, send_term_after=1.0)
results['4_sigterm_ignored_child'] = {'rc': rc4, 'reap_seconds': dt4, 'grace_seconds': 5.0}

# 5. KNOWN GAP: hung sync not detected
rc5, dt5, _ = run('hang', 4)
results['5_hung_sync'] = {'rc': rc5}

# 6. KNOWN GAP: continuously failing cycles not detected
rc6, dt6, out6 = run('failloop', 4)
results['6_failloop_sync'] = {'rc': rc6, 'failed_cycles_seen': out6.count('SYNC_CYCLE_FAILED')}

# no leftover processes from harness
left = subprocess.run(['pgrep', '-f', str(work)], capture_output=True, text=True).stdout.split()
results['orphans_after'] = len(left)
results['state_dir'] = 'tempdir (isolated, deleted after run)'
print(json.dumps(results, indent=2))
import shutil; shutil.rmtree(work)

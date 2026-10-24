import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from r3.supervise_node import supervise
from r3.sync_progress import ProgressWatchdog, ProgressWriter


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux subreaper')
def test_adopted_zombie_reaped_without_stealing_leader_status(tmp_path, capsys):
    pidfile = tmp_path / 'orphan'
    code = f'''import os,time
p=os.fork()
if p==0:
 q=os.fork()
 if q==0:
  open({str(pidfile)!r},'w').write(str(os.getpid()))
  time.sleep(.15)
  os._exit(0)
 os._exit(0)
os.waitpid(p,0)
time.sleep(.6)
os._exit(7)
'''
    assert supervise([[sys.executable, '-c', code]], grace_seconds=.5) == 1
    assert 'returncode=7' in capsys.readouterr().out
    with pytest.raises(ProcessLookupError):
        os.kill(int(pidfile.read_text()), 0)


def test_resume_grants_budget_but_keeps_failure_limit(tmp_path):
    now = [0.0]
    path = tmp_path / 'progress'
    writer = ProgressWriter(path, 'run')
    watcher = ProgressWatchdog(path, 'run', timeout=2, clock=lambda: now[0])
    writer.mark()
    assert watcher.check() is None
    now[0] = 100
    watcher.resume()
    assert watcher.check() is None
    now[0] = 103
    assert watcher.check() == 'sync_progress_timeout'
    for _ in range(3):
        writer.mark(success=False)
    watcher.resume()
    assert watcher.check() == 'sync_repeated_failure'


@pytest.mark.skipif(sys.platform != 'linux', reason='SIGSTOP/SIGCONT')
def test_whole_monitor_pause_receives_resume_budget(tmp_path):
    ready = tmp_path / 'ready'
    code = f'''import os,time,sys
from r3.supervise_node import supervise
from r3.sync_progress import ProgressWatchdog
w=ProgressWatchdog({str(tmp_path / 'missing')!r},'r',startup=2,timeout=.3)
open({str(ready)!r},'w').write('ready')
raise SystemExit(supervise([[sys.executable,'-c','import time; time.sleep(30)']],grace_seconds=.1,progress_check=w.check))
'''
    p = subprocess.Popen([sys.executable, '-c', code], start_new_session=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 4
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists()
        time.sleep(.2)
        os.kill(p.pid, signal.SIGSTOP)
        time.sleep(2.2)
        os.kill(p.pid, signal.SIGCONT)
        time.sleep(.2)
        assert p.poll() is None
        # Missing progress is still eventually a fault, not permanently masked.
        assert p.wait(timeout=4) == 1
    finally:
        if p.poll() is None:
            p.send_signal(signal.SIGTERM)
            p.wait(timeout=3)

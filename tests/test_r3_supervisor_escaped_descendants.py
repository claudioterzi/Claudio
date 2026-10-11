import os
import signal
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from r3.supervise_node import supervise


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux subreaper and setsid')
@pytest.mark.parametrize('ignore_term', [False, True])
def test_escaped_double_fork_is_terminated_and_reaped(tmp_path, ignore_term):
    pidfile = tmp_path / 'pid'
    marker = tmp_path / 'closed'
    child = f'''import os,time,signal
p=os.fork()
if p==0:
 q=os.fork()
 if q:
  os._exit(0)
 os.setsid()
 def close(s,f):
  time.sleep(.15)
  open({str(marker)!r},'w').write('closed')
  os._exit(0)
 signal.signal(signal.SIGTERM, signal.SIG_IGN if {ignore_term!r} else close)
 open({str(pidfile)!r},'w').write(str(os.getpid()))
 while True: time.sleep(.05)
os.waitpid(p,0)
time.sleep(30)
'''
    def check():
        return 'done' if pidfile.exists() else None
    started = time.monotonic()
    try:
        assert supervise([[sys.executable, '-c', child]], grace_seconds=.5,
                         progress_check=check, failure_delay_seconds=.1) == 1
        assert time.monotonic() - started < 3
        assert marker.exists() is (not ignore_term)
        with pytest.raises(ProcessLookupError):
            os.kill(int(pidfile.read_text()), 0)
    finally:
        if pidfile.exists():
            try: os.kill(int(pidfile.read_text()), signal.SIGKILL)
            except ProcessLookupError: pass


def test_cleanup_exception_restores_signals_and_subreaper():
    from r3.supervise_node import _enable_subreaper
    old = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
    setting = _enable_subreaper()
    if setting:
        libc, before = setting
        libc.prctl(36, before, 0, 0, 0)
    with patch('r3.supervise_node._cleanup_children', side_effect=OSError('cleanup')), \
         patch('r3.supervise_node.subprocess.Popen', side_effect=OSError('start')):
        with pytest.raises(OSError, match='cleanup'):
            supervise([['unused']])
    assert all(signal.getsignal(s) == h for s, h in old.items())
    if setting:
        setting2 = _enable_subreaper()
        assert setting2[1] == before
        libc.prctl(36, before, 0, 0, 0)


def test_incomplete_cleanup_returns_failure():
    with patch('r3.supervise_node._cleanup_children', return_value=False), \
         patch('r3.supervise_node.subprocess.Popen', side_effect=OSError('start')):
        assert supervise([['unused']]) == 1

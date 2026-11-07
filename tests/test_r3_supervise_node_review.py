"""Regressions from the external review of 2026-10-05 (stdlib unittest, no network).

Each case failed on c5300c4 before the fix and passes after it.
"""
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from r3.supervise_node import supervise


class SupervisorReviewRegressions(unittest.TestCase):
    def test_no_child_started_after_sigterm_during_startup(self):
        real_popen = subprocess.Popen
        starts = []

        def fake_popen(cmd, **kwargs):
            starts.append(cmd)
            child = real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
            if len(starts) == 1:
                signal.raise_signal(signal.SIGTERM)
            return child

        with mock.patch("r3.supervise_node.subprocess.Popen", side_effect=fake_popen):
            rc = supervise([["first"], ["second"]], grace_seconds=1)
        self.assertEqual(len(starts), 1)
        self.assertEqual(rc, 0)

    def test_grace_covers_descendants_not_only_leaders(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "grandchild_done"
            grandchild = textwrap.dedent(f"""
                import signal, sys, time
                def done(*_):
                    time.sleep(1.5)
                    open({str(marker)!r}, 'w').write('ok')
                    sys.exit(0)
                signal.signal(signal.SIGTERM, done)
                while True:
                    time.sleep(0.1)
            """)
            leader = textwrap.dedent(f"""
                import signal, subprocess, sys, time
                subprocess.Popen([sys.executable, '-c', {grandchild!r}])
                signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
                while True:
                    time.sleep(0.1)
            """)
            runner = ("import sys\nfrom r3.supervise_node import supervise\n"
                      f"sys.exit(supervise([[sys.executable, '-c', {leader!r}]], grace_seconds=5))")
            proc = subprocess.Popen([sys.executable, "-c", runner])
            time.sleep(1.0)
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=30)
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(marker.exists(), "descendant was killed before the grace period")

    def test_children_still_receive_sigterm(self):
        # Guards against blocking signals during start-up: children would inherit
        # the blocked mask and only die by SIGKILL after the full grace period.
        script = ("import sys\nfrom r3.supervise_node import supervise\n"
                  "sys.exit(supervise([[sys.executable, '-c', 'import time\\nwhile 1: time.sleep(1)']],"
                  " grace_seconds=5))")
        proc = subprocess.Popen([sys.executable, "-c", script])
        time.sleep(0.8)
        started = time.monotonic()
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=30)
        self.assertLess(time.monotonic() - started, 2.0)


if __name__ == "__main__":
    unittest.main()

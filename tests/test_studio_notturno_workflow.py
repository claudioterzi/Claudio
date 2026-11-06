"""Offline regression tests for the actual Studio Notturno workflow shell steps."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/studio_notturno.yml'


class StudioWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
        cls.steps = cls.workflow['jobs']['studia']['steps']

    def test_schedule_uses_the_brussels_calendar(self):
        schedule = self.workflow['on']['schedule']
        self.assertEqual(schedule, [{'cron': '0 2 * * *', 'timezone': 'Europe/Brussels'}])
        self.assertEqual(self.workflow['jobs']['studia']['env']['TZ'], 'Europe/Brussels')

    def step(self, name):
        return next(step for step in self.steps if step.get('name') == name)

    def run_step(self, name, *, env=None, prelude=''):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = root / 'summary.md'
            calls = root / 'calls.txt'
            variables = {
                'PATH': os.environ['PATH'],
                'HOME': tmp,
                'GITHUB_STEP_SUMMARY': str(summary),
                'GITHUB_OUTPUT': str(calls),
                'CALLS': str(calls),
                'TARGET_BRANCH': 'test-studio',
                'ANTHROPIC_API_KEY': '',
                **(env or {}),
            }
            result = subprocess.run(
                ['bash', '-eo', 'pipefail', '-c', prelude + '\n' + self.step(name)['run']],
                cwd=tmp, env=variables, capture_output=True, text=True,
            )
            return result, summary.read_text() if summary.exists() else '', calls.read_text() if calls.exists() else ''

    def test_missing_key_selects_public_apis(self):
        result, summary, output = self.run_step('Seleziona motore Studio')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.strip(), 'provider=public_api')
        self.assertIn('API documentali pubbliche', summary)
        self.assertNotIn('Morning Brief salvato', summary)

    def test_present_key_is_not_exposed(self):
        fake = 'test-only-not-a-real-credential'
        result, summary, output = self.run_step('Seleziona motore Studio', env={'ANTHROPIC_API_KEY': fake})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.strip(), 'provider=claude')
        self.assertNotIn(fake, result.stdout + result.stderr + summary + output)

    def test_installation_only_runs_for_claude(self):
        self.assertEqual(self.steps[0]['id'], 'motore')
        self.assertEqual(self.step('Installa dipendenze')['if'], "steps.motore.outputs.provider == 'claude'")

    def test_push_trigger_only_for_studio_sources_on_main(self):
        self.assertEqual(self.workflow['on']['push']['branches'], ['main'])
        self.assertEqual(set(self.workflow['on']['push']['paths']), {
            '.github/workflows/studio_notturno.yml',
            'scripts/studio_notturno.py',
            'scripts/studio_fonti.py',
            'scripts/studio_priorita.py',
            'studio/temi_lavorati.json',
        })

    def test_no_cache_for_no_cache_installation(self):
        setup = self.step('Setup Python')
        self.assertNotIn('cache', setup['with'])
        self.assertIn('--no-cache-dir', self.step('Installa dipendenze')['run'])

    def test_generation_error_propagates(self):
        result, _, _ = self.run_step('Studio Notturno', prelude='python3() { return 7; }')
        self.assertEqual(result.returncode, 7)

    def test_missing_output_is_rejected(self):
        result, _, _ = self.run_step('Studio Notturno', prelude='python3() { return 0; }')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('assente o vuoto', result.stdout)

    def test_empty_output_is_rejected(self):
        result, _, _ = self.run_step('Studio Notturno', prelude='python3() { mkdir -p output/morning_brief; touch "output/morning_brief/$(date +%Y-%m-%d).md"; }')
        self.assertNotEqual(result.returncode, 0)

    def test_nonempty_output_is_accepted(self):
        result, _, _ = self.run_step('Studio Notturno', prelude='python3() { mkdir -p output/morning_brief; echo "Offline test fixture" > "output/morning_brief/$(date +%Y-%m-%d).md"; }')
        self.assertEqual(result.returncode, 0, result.stderr)

    def git_stub(self, *, changed=True, commit_status=0, push_status=0):
        return '''
git() {
  printf '%s\\n' "$*" >> "$CALLS"
  case "$1" in
    diff) return DIFF_STATUS ;;
    commit) return COMMIT_STATUS ;;
    push) return PUSH_STATUS ;;
    rev-parse) printf '%s\\n' 'fixture-commit-sha' ;;
    *) return 0 ;;
  esac
}
'''.replace('DIFF_STATUS', str(int(changed))).replace('COMMIT_STATUS', str(commit_status)).replace('PUSH_STATUS', str(push_status))

    def test_unchanged_output_does_not_claim_a_new_commit(self):
        result, summary, calls = self.run_step('Salva Morning Brief nel repo', prelude=self.git_stub(changed=False))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Nessun nuovo commit', summary)
        self.assertNotIn('push ', calls)
        self.assertNotIn('Morning Brief salvato', summary)

    def test_commit_failure_stops_before_push(self):
        result, summary, calls = self.run_step('Salva Morning Brief nel repo', prelude=self.git_stub(commit_status=9))
        self.assertEqual(result.returncode, 9)
        self.assertNotIn('push ', calls)
        self.assertNotIn('Morning Brief salvato', summary)

    def test_push_failure_is_not_hidden(self):
        result, summary, _ = self.run_step('Salva Morning Brief nel repo', prelude=self.git_stub(push_status=11))
        self.assertEqual(result.returncode, 11)
        self.assertNotIn('Morning Brief salvato', summary)

    def test_success_records_commit_only_after_push(self):
        result, summary, calls = self.run_step('Salva Morning Brief nel repo', prelude=self.git_stub())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('push origin HEAD:refs/heads/test-studio', calls)
        self.assertIn('Morning Brief salvato', summary)
        self.assertIn('fixture-commit-sha', summary)

    def test_all_shell_steps_have_valid_syntax(self):
        for step in self.steps:
            if 'run' in step:
                with self.subTest(step=step['name']):
                    result = subprocess.run(['bash', '-n'], input=step['run'], text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_checks_never_use_provider_credentials(self):
        checks = yaml.load((ROOT / '.github/workflows/studio_notturno_checks.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(checks['permissions'], {'contents': 'read'})
        self.assertNotIn('secrets.', str(checks))
        for step in checks['jobs']['workflow-regressions']['steps']:
            self.assertNotIn('python3 scripts/studio_notturno.py', step.get('run', ''))


if __name__ == '__main__':
    unittest.main()

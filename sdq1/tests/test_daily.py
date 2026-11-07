"""Regressioni Daily offline: nessun invio Telegram o richiesta a provider reali."""

from __future__ import annotations

import contextlib
import io
import os
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import yaml

from sdq1 import notifiche
from sdq1.llm import providers
from sdq1.llm.providers import openai_provider

ROOT = Path(__file__).resolve().parents[2]


class MistralProviderTests(unittest.TestCase):
    def test_public_export(self):
        self.assertIn("MistralProvider", providers.__all__)
        self.assertIs(providers.MistralProvider, openai_provider.MistralProvider)

    def test_missing_sdk_does_not_initialize(self):
        with (
            patch.object(openai_provider, "_OK", False),
            patch.dict(os.environ, {}, clear=True),
        ):
            provider = providers.MistralProvider("mistral-small-latest", api_key=None)
        self.assertFalse(provider.disponibile)
        self.assertFalse(provider.completa("system", "question").via_api)

    def test_missing_key_does_not_initialize(self):
        with (
            patch.object(openai_provider, "_OK", True),
            patch.dict(os.environ, {}, clear=True),
        ):
            provider = providers.MistralProvider("mistral-small-latest", api_key=None)
        self.assertFalse(provider.disponibile)

    def test_compatible_client_and_response(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="risposta"), finish_reason="stop"
                )
            ],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3),
        )
        with (
            patch.object(openai_provider, "_OK", True),
            patch.object(
                openai_provider, "OpenAI", return_value=client, create=True
            ) as factory,
            patch.dict(os.environ, {"MISTRAL_API_KEY": "test-only-key"}, clear=True),
        ):
            provider = providers.MistralProvider(
                "mistral-small-latest", api_key=None, timeout_secondi=25
            )
            result = provider.completa("system", "question")
        factory.assert_called_once_with(
            api_key="test-only-key", timeout=25, base_url="https://api.mistral.ai/v1"
        )
        self.assertEqual(result.provider, "mistral")
        self.assertEqual(result.testo, "risposta")
        self.assertTrue(result.via_api)
        self.assertEqual(result.metadata["output_tokens"], 3)
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["model"],
            "mistral-small-latest",
        )


class BriefingTests(unittest.TestCase):
    def test_missing_config_has_no_provider_or_telegram_calls(self):
        for env in (
            {},
            {"TELEGRAM_BOT_TOKEN": "test-only"},
            {"TELEGRAM_CHAT_ID": "test-chat"},
            {"TELEGRAM_BOT_TOKEN": " \t", "TELEGRAM_CHAT_ID": "test-chat"},
        ):
            with (
                self.subTest(env=list(env)),
                patch.dict(os.environ, env, clear=True),
                patch.object(notifiche, "_consulta_ai") as consult,
                patch.object(notifiche, "invia") as send,
                contextlib.redirect_stdout(io.StringIO()) as out,
            ):
                self.assertFalse(notifiche.briefing_operativo())
                consult.assert_not_called()
                send.assert_not_called()
                self.assertIn("Telegram non configurato", out.getvalue())

    def run_briefing(self, ai_result="", send_result=True):
        with (
            patch.dict(
                os.environ,
                {"TELEGRAM_BOT_TOKEN": "test-only", "TELEGRAM_CHAT_ID": "test-chat"},
                clear=True,
            ),
            patch("sdq1.agenda.carica", return_value={}),
            patch("sdq1.agenda.prossimi_viaggi", return_value=[]),
            patch.object(notifiche, "_consulta_ai", return_value=ai_result) as consult,
            patch.object(notifiche, "invia", return_value=send_result) as send,
        ):
            result = notifiche.briefing_operativo()
        return result, consult, send

    def test_all_four_providers_are_reachable_without_real_calls(self):
        result, consult, send = self.run_briefing(ai_result="risposta simulata")
        self.assertTrue(result)
        self.assertEqual(consult.call_count, 4)
        classes = {call.args[0] for call in consult.call_args_list}
        self.assertIn(providers.MistralProvider, classes)
        self.assertIn("[Mistral] risposta simulata", send.call_args.args[0])
        send.assert_called_once()

    def test_missing_ai_keys_use_existing_fallback(self):
        with (
            patch.dict(
                os.environ,
                {"TELEGRAM_BOT_TOKEN": "test-only", "TELEGRAM_CHAT_ID": "test-chat"},
                clear=True,
            ),
            patch("sdq1.agenda.carica", return_value={}),
            patch("sdq1.agenda.prossimi_viaggi", return_value=[]),
            patch.object(
                socket.socket,
                "connect",
                side_effect=AssertionError("Network forbidden"),
            ) as connect,
            patch.object(notifiche, "invia", return_value=True) as send,
        ):
            result = notifiche.briefing_operativo()
            connect.assert_not_called()
        self.assertTrue(result)
        self.assertIn(
            "Nessun modello ha restituito l'analisi sistemica.",
            send.call_args.args[0],
        )

    def test_provider_exception_uses_empty_helper_fallback(self):
        client = Mock()
        client.chat.completions.create.side_effect = RuntimeError(
            "simulated service failure"
        )
        with (
            patch.object(openai_provider, "_OK", True),
            patch.object(openai_provider, "OpenAI", return_value=client, create=True),
            patch.dict(os.environ, {"MISTRAL_API_KEY": "test-only-key"}, clear=True),
        ):
            result = notifiche._consulta_ai(
                providers.MistralProvider, "mistral-small-latest", "system", "question"
            )
        self.assertEqual(result, "")
        client.chat.completions.create.assert_called_once()

    def test_website_capture_still_works_without_telegram_credentials(self):
        import agora_runtime

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("sdq1.agenda.carica", return_value={}),
            patch("sdq1.agenda.prossimi_viaggi", return_value=[]),
            patch.object(
                notifiche, "_consulta_ai", return_value="risposta simulata"
            ) as consult,
            patch("urllib.request.urlopen") as network,
        ):
            result = agora_runtime.esegui("/briefing")
        self.assertEqual(result["stato"], "completato")
        self.assertIn("Briefing Operativo", result["testo"])
        self.assertEqual(consult.call_count, 4)
        network.assert_not_called()

    def test_failed_send_is_not_success(self):
        result, _, send = self.run_briefing(send_result=False)
        self.assertFalse(result)
        send.assert_called_once()

    def test_cli_propagates_briefing_outcome(self):
        from sdq1.__main__ import main

        for outcome, code in ((True, 0), (False, 1)):
            with (
                self.subTest(outcome=outcome),
                patch.object(notifiche, "briefing_operativo", return_value=outcome),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(main(["sdq1", "--briefing-operativo"]), code)


class DailyWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.safe_load(
            (ROOT / ".github/workflows/sdq1_daily.yml").read_text()
        )
        cls.steps = cls.workflow["jobs"]["run"]["steps"]
        cls.by_name = {step["name"]: step for step in cls.steps}

    def run_shell(self, step, env=None):
        with tempfile.TemporaryDirectory() as directory:
            output, summary = (Path(directory) / name for name in ("output", "summary"))
            variables = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "GITHUB_OUTPUT": str(output),
                "GITHUB_STEP_SUMMARY": str(summary),
                "TELEGRAM_BOT_TOKEN": "",
                "TELEGRAM_CHAT_ID": "",
            }
            variables.update(env or {})
            proc = subprocess.run(
                [
                    "bash",
                    "--noprofile",
                    "--norc",
                    "-e",
                    "-o",
                    "pipefail",
                    "-c",
                    step["run"],
                ],
                env=variables,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return (
                proc,
                output.read_text() if output.exists() else "",
                summary.read_text() if summary.exists() else "",
            )

    def test_no_cache_save_after_no_cache_install(self):
        self.assertNotIn("cache", self.by_name["Setup Python"]["with"])
        self.assertIn("--no-cache-dir", self.by_name["Installa dipendenze"]["run"])

    def test_missing_telegram_is_explicitly_skipped(self):
        for env in (
            {},
            {"TELEGRAM_BOT_TOKEN": "test-only"},
            {"TELEGRAM_CHAT_ID": "test-chat"},
            {"TELEGRAM_BOT_TOKEN": " \t", "TELEGRAM_CHAT_ID": "test-chat"},
        ):
            with self.subTest(env=list(env)):
                proc, output, summary = self.run_shell(
                    self.by_name["Verifica configurazione Telegram"], env
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(output, "available=false\n")
                self.assertIn("::warning::", proc.stdout)
                self.assertIn("SKIPPED_MISSING_CONFIG", summary)

    def test_configured_telegram_admitted_without_leaking_values(self):
        proc, output, summary = self.run_shell(
            self.by_name["Verifica configurazione Telegram"],
            {
                "TELEGRAM_BOT_TOKEN": "test-only-private",
                "TELEGRAM_CHAT_ID": "test-chat",
            },
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(output, "available=true\n")
        self.assertNotIn(
            "test-only-private", proc.stdout + proc.stderr + output + summary
        )

    def test_telegram_steps_require_config(self):
        for name in ("Comandi Telegram", "Briefing Telegram"):
            self.assertEqual(
                self.by_name[name]["if"],
                "steps.telegram_config.outputs.available == 'true'",
            )

    def test_mistral_secret_is_wired(self):
        self.assertEqual(
            self.by_name["Briefing Telegram"]["env"]["MISTRAL_API_KEY"],
            "${{ secrets.MISTRAL_API_KEY }}",
        )

    def test_briefing_failure_is_not_masked_and_outputs_are_preserved(self):
        briefing = self.by_name["Briefing Telegram"]
        self.assertEqual(briefing["id"], "briefing")
        self.assertNotIn("continue-on-error", briefing)
        for name in ("Registra battito e stato pubblico", "Commit output e stato"):
            step = self.by_name[name]
            self.assertEqual(step["if"], "${{ always() }}")
            self.assertGreater(self.steps.index(step), self.steps.index(briefing))
        heartbeat = self.by_name["Registra battito e stato pubblico"]["run"]
        self.assertIn("briefing_outcome=${{ steps.briefing.outcome }}", heartbeat)
        self.assertIn(
            "telegram_available=${{ steps.telegram_config.outputs.available }}",
            heartbeat,
        )

    def test_regressions_run_before_daily_effects_and_in_ci(self):
        test = self.by_name["Test regressioni Daily offline"]
        self.assertIn("unittest discover -s sdq1/tests -p 'test_daily.py'", test["run"])
        self.assertNotIn("continue-on-error", test)
        self.assertLess(
            self.steps.index(test), self.steps.index(self.by_name["Sync Airbnb"])
        )
        runner = yaml.safe_load(
            (ROOT / ".github/workflows/test_runner.yml").read_text()
        )
        ci_test = next(
            s for s in runner["jobs"]["test"]["steps"] if s["name"] == test["name"]
        )
        self.assertIn("test_daily.py", ci_test["run"])
        self.assertNotIn("continue-on-error", ci_test)


if __name__ == "__main__":
    unittest.main()

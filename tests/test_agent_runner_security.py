import os
import socket
import unittest
from unittest.mock import patch

import agent_runner


def addrinfo(address):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    sockaddr = (address, 443, 0, 0) if family == socket.AF_INET6 else (address, 443)
    return (family, socket.SOCK_STREAM, 6, "", sockaddr)


class RunnerSecurityTests(unittest.TestCase):
    def test_child_environment_does_not_inherit_parent_secrets(self):
        parent = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/home/runner",
            "GITHUB_TOKEN": "ghs-secret",
            "GEMINI_API_KEY": "gemini-secret",
            "GROQ_API_KEY": "groq-secret",
            "OPENROUTER_API_KEY": "openrouter-secret",
            "AWS_SECRET_ACCESS_KEY": "aws-secret",
            "SUPABASE_SERVICE_ROLE_KEY": "supabase-secret",
            "PLAYWRIGHT_BROWSERS_PATH": "/secret/browser/path",
        }
        with patch.dict(os.environ, parent, clear=True):
            child = agent_runner.sandbox_environment()

        for name in (
            "GITHUB_TOKEN", "GEMINI_API_KEY", "GROQ_API_KEY",
            "OPENROUTER_API_KEY", "AWS_SECRET_ACCESS_KEY",
            "SUPABASE_SERVICE_ROLE_KEY", "PLAYWRIGHT_BROWSERS_PATH",
        ):
            self.assertNotIn(name, child)
        self.assertEqual(set(child), {"PATH", "HOME", "TMPDIR", "TEMP", "TMP", "LANG", "LC_ALL", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE"})
        self.assertNotEqual(child["HOME"], "/home/runner")

    def test_container_command_is_restricted_and_receives_no_secrets(self):
        command = agent_runner.build_sandbox_command(
            "/tmp/workspace",
            container_name="qa-sandbox-test",
        )
        joined = " ".join(command)
        for required in (
            "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
            "--pids-limit=128", "--memory=2g", "--cpus=2",
            "--network", "uba-agent-sandbox", "/tmp/workspace:/work",
        ):
            self.assertIn(required, joined)
        for forbidden in ("--env-file", "GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY"):
            self.assertNotIn(forbidden, joined)

    def test_rejects_loopback_private_link_local_and_ipv6_private_targets(self):
        for url in (
            "http://127.0.0.1",
            "http://10.0.0.1",
            "http://192.168.1.1",
            "http://169.254.169.254/latest/meta-data",
            "http://[::1]",
            "http://[fc00::1]",
            "http://[fe80::1]",
            "http://[::ffff:127.0.0.1]",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    agent_runner.validate_public_target(url)

    @patch("agent_runner.socket.getaddrinfo")
    def test_rejects_hostname_with_any_non_global_dns_answer(self, getaddrinfo):
        getaddrinfo.return_value = [
            addrinfo("93.184.216.34"),
            addrinfo("10.20.30.40"),
        ]
        with self.assertRaises(ValueError):
            agent_runner.validate_public_target("https://example.test")

    @patch("agent_runner.socket.getaddrinfo")
    def test_accepts_hostname_only_when_all_dns_answers_are_global(self, getaddrinfo):
        getaddrinfo.return_value = [
            addrinfo("93.184.216.34"),
            addrinfo("2606:2800:220:1:248:1893:25c8:1946"),
        ]
        self.assertEqual(
            agent_runner.validate_public_target("https://example.test"),
            "https://example.test",
        )

    def test_rejects_url_credentials_and_invalid_ports(self):
        for url in ("https://user:pass@example.com", "https://example.com:invalid"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    agent_runner.validate_public_target(url)


if __name__ == "__main__":
    unittest.main()


    def test_provider_generation_pipeline_is_defined(self):
        for name in ("extract_code", "provider_config", "ask_model", "build_prompt"):
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(agent_runner, name, None)))

    def test_prompt_requires_truthful_success_evidence(self):
        prompt = agent_runner.build_prompt("Inspect the page", "https://example.com")
        self.assertIn("success", prompt.lower())
        self.assertIn("verified", prompt.lower())
        self.assertIn("Never fabricate", prompt)

    def test_execute_script_rejects_output_that_reports_failure(self):
        import json
        import subprocess
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / ".agent-sandbox-test"
            workspace.mkdir()

            def fake_run(command, **kwargs):
                if "-m" in command and "py_compile" in command:
                    return subprocess.CompletedProcess(command, 0, "", "")
                (workspace / "output.json").write_text(
                    json.dumps({"success": False, "error": "task did not complete"}),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(agent_runner, "ROOT", root), \\
                 patch.object(agent_runner, "OUTPUT", root / "output.json"), \\
                 patch.object(agent_runner, "ARTIFACTS", root / "artifacts"), \\
                 patch("agent_runner.tempfile.mkdtemp", return_value=str(workspace)), \\
                 patch("agent_runner.subprocess.run", side_effect=fake_run):
                success, logs = agent_runner.execute_script("print('test')", timeout=5)

        self.assertFalse(success)
        self.assertIn("success", logs.lower())

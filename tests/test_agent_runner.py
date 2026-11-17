import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent_runner


class AgentRunnerTests(unittest.TestCase):
    def test_extract_code_strips_python_fence(self):
        fence = chr(96) * 3
        self.assertEqual(
            agent_runner.extract_code(f"  {fence}python\nprint('ok')\n{fence}  "),
            "print('ok')",
        )

    def test_extract_code_strips_json_wrapped_fence(self):
        fence = chr(96) * 3
        payload = json.dumps({"code": f"{fence}py\nprint(1 + 1)\n{fence}"})
        self.assertEqual(agent_runner.extract_code(payload), "print(1 + 1)")

    def test_extract_code_preserves_unfenced_source(self):
        self.assertEqual(agent_runner.extract_code("print('plain')"), "print('plain')")

    def test_repair_prompt_uses_real_newlines(self):
        prompt = agent_runner.build_prompt(
            "search for a result", "https://example.com", "print('old')", "timeout"
        )
        self.assertIn("\nPREVIOUS SCRIPT:\n", prompt)
        self.assertNotIn("\\nPREVIOUS SCRIPT:\\n", prompt)

    def test_sandbox_command_does_not_forward_provider_secrets(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "gemini-secret-test",
            "GROQ_API_KEY": "groq-secret-test",
            "OPENROUTER_API_KEY": "openrouter-secret-test",
        }):
            command = agent_runner.build_sandbox_command("/tmp/agent-work")
        self.assertEqual(command[:2], ["docker", "run"])
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--security-opt=no-new-privileges", command)
        self.assertIn("--read-only", command)
        self.assertIn("--network=bridge", command)
        self.assertNotIn("gemini-secret-test", command)
        self.assertNotIn("groq-secret-test", command)
        self.assertNotIn("openrouter-secret-test", command)

    def test_execute_script_runs_in_container_and_copies_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                patch.object(agent_runner, "ROOT", root),
                patch.object(agent_runner, "OUTPUT", root / "output.json"),
                patch.object(agent_runner, "ARTIFACTS", root / "artifacts"),
                patch.dict(os.environ, {"GEMINI_API_KEY": "never-forward-this"}),
            ):
                def fake_run(command, **kwargs):
                    mount = next(item for item in command if item.startswith("type=bind,src="))
                    sandbox_path = Path(mount.split("src=", 1)[1].split(",dst=", 1)[0])
                    (sandbox_path / "output.json").write_text('{"success": true}', encoding="utf-8")
                    return subprocess.CompletedProcess(command, 0, "sandbox ok", "")

                with patch.object(agent_runner.subprocess, "run", side_effect=fake_run) as run:
                    success, logs = agent_runner.execute_script("print('safe')", 30)

                self.assertTrue(success)
                self.assertIn("sandbox ok", logs)
                self.assertTrue((root / "generated_task.py").exists())
                self.assertEqual(json.loads((root / "output.json").read_text()), {"success": True})
                command = run.call_args.args[0]
                self.assertIn("--read-only", command)
                self.assertNotIn("never-forward-this", command)


if __name__ == "__main__":
    unittest.main()

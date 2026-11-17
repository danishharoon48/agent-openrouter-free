import os
import unittest

from agent_runner import build_prompt, build_sandbox_command, extract_code


class AgentRunnerTests(unittest.TestCase):
    def test_extract_code_strips_python_fence(self):
        self.assertEqual(
            extract_code("  ```python\nprint('ok')\n```  "),
            "print('ok')",
        )

    def test_extract_code_strips_json_wrapped_fence(self):
        self.assertEqual(
            extract_code('{"code": "```py\\nprint(1 + 1)\\n```"}'),
            "print(1 + 1)",
        )

    def test_extract_code_preserves_unfenced_source(self):
        self.assertEqual(extract_code("print('plain')"), "print('plain')")

    def test_repair_prompt_uses_real_newlines(self):
        prompt = build_prompt("search for a result", "https://example.com", "print('old')", "timeout")
        self.assertIn("\nPREVIOUS SCRIPT:\n", prompt)
        self.assertNotIn("\\nPREVIOUS SCRIPT:\\n", prompt)

    def test_sandbox_command_does_not_forward_provider_secrets(self):
        command = build_sandbox_command("/tmp/agent-work")
        self.assertEqual(command[:2], ["docker", "run"])
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--security-opt=no-new-privileges", command)
        self.assertIn("--read-only", command)
        self.assertIn("--network=bridge", command)
        self.assertIn("--env", command)
        self.assertNotIn(os.getenv("GEMINI_API_KEY", "not-a-key"), command)
        self.assertNotIn(os.getenv("GROQ_API_KEY", "not-a-key"), command)
        self.assertNotIn(os.getenv("OPENROUTER_API_KEY", "not-a-key"), command)


if __name__ == "__main__":
    unittest.main()

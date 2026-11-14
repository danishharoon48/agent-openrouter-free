import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import agent_runner


@unittest.skipUnless(
    os.getenv("BROWSER_SANDBOX_INTEGRATION") == "1",
    "Docker integration is enabled only on trusted same-repository PRs and manual runs.",
)
class SandboxContainerIntegrationTests(unittest.TestCase):
    def test_generated_code_runs_without_parent_secrets(self):
        code = """
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

for name in (
    "GITHUB_TOKEN", "GEMINI_API_KEY", "GROQ_API_KEY",
    "OPENROUTER_API_KEY", "AWS_SECRET_ACCESS_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
):
    if name in os.environ:
        raise RuntimeError("Secret environment variable leaked: " + name)

if Path("/var/run/docker.sock").exists():
    raise RuntimeError("Docker socket is exposed inside the generated-code container")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_content("<html><body><main id='probe'>isolated-chromium-ok</main></body></html>")
    extracted = page.locator("#probe").inner_text()
    browser.close()

if extracted != "isolated-chromium-ok":
    raise RuntimeError("Chromium did not execute the browser smoke test")

Path("output.json").write_text(
    json.dumps({"success": True, "sandbox": "container-executed", "browser": "chromium", "extracted_text": extracted}),
    encoding="utf-8",
)
"""
        parent_secrets = {
            "GITHUB_TOKEN": "test-github-secret",
            "GEMINI_API_KEY": "test-gemini-secret",
            "GROQ_API_KEY": "test-groq-secret",
            "OPENROUTER_API_KEY": "test-openrouter-secret",
            "AWS_SECRET_ACCESS_KEY": "test-aws-secret",
            "SUPABASE_SERVICE_ROLE_KEY": "test-supabase-secret",
        }
        with patch.dict(os.environ, parent_secrets, clear=False):
            success, logs = agent_runner.execute_script(code, timeout=60)

        self.assertTrue(success, logs)
        output = json.loads(Path("output.json").read_text(encoding="utf-8"))
        self.assertTrue(output["success"])
        self.assertEqual(output["sandbox"], "container-executed")
        self.assertEqual(output["browser"], "chromium")
        self.assertEqual(output["extracted_text"], "isolated-chromium-ok")


if __name__ == "__main__":
    unittest.main()

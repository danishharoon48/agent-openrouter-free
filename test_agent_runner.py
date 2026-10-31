import unittest
from agent_runner import extract_code
class RunnerTests(unittest.TestCase):
    def test_markdown_fence(self):
        self.assertEqual(extract_code('```python\\nprint(42)\\n```'), 'print(42)')
    def test_json_code_wrapper(self):
        self.assertEqual(extract_code('{\"code\": \"print(42)\"}'), 'print(42)')
    def test_unicode_preserved(self):
        value = \"term = 'اردو تلاش'\"
        self.assertEqual(extract_code(value), value)
if __name__ == '__main__': unittest.main()

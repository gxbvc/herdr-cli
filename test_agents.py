#!/usr/bin/env python3
import unittest

import importlib.machinery
import importlib.util
from pathlib import Path

LOADER = importlib.machinery.SourceFileLoader("agentscli", str(Path(__file__).with_name("agents-cli")))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MOD = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MOD)


class PromptArgvTest(unittest.TestCase):
    def test_heading_and_double_dash_stay_one_text_argv(self):
        argv = MOD.prompt_argv("w1:p1", "# Title\n--wait is content")
        self.assertEqual(argv[:3], ["agent", "prompt", "w1:p1"])
        self.assertEqual(argv[3], "# Title\n--wait is content")
        self.assertNotIn("--", argv)

    def test_wait_flags_come_after_text(self):
        argv = MOD.prompt_argv("bot", "hello", wait=True, timeout="5000", until=["idle", "done"])
        self.assertEqual(argv[3], "hello")
        self.assertEqual(argv[4:], ["--wait", "--until", "idle", "--until", "done", "--timeout", "5000"])


if __name__ == "__main__":
    unittest.main()

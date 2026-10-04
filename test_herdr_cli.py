#!/usr/bin/env python3
import unittest

import importlib.machinery
import importlib.util
from pathlib import Path

LOADER = importlib.machinery.SourceFileLoader("agentscli", str(Path(__file__).with_name("herdr-cli")))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MOD = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MOD)


class PromptArgvTest(unittest.TestCase):
    def test_heading_and_double_dash_stay_one_text_argv(self):
        argv = MOD.prompt_argv("w7:t1", "# Title\n--wait is content")
        self.assertEqual(argv[:3], ["agent", "prompt", "w7:t1"])
        self.assertEqual(argv[3], "# Title\n--wait is content")
        self.assertNotIn("--", argv)

    def test_wait_flags_come_after_text(self):
        argv = MOD.prompt_argv("bot", "hello", wait=True, timeout="5000", until=["idle", "done"])
        self.assertEqual(argv[3], "hello")
        self.assertEqual(argv[4:], ["--wait", "--until", "idle", "--until", "done", "--timeout", "5000"])


class TabSurfaceTest(unittest.TestCase):
    def test_tab_create_has_no_focus_and_no_pane_flag(self):
        argv = MOD.tab_create_argv("w7", cwd="/tmp/proj", label="research")
        self.assertEqual(
            argv,
            ["tab", "create", "--workspace", "w7", "--no-focus", "--cwd", "/tmp/proj", "--label", "research"],
        )
        self.assertNotIn("--pane", argv)
        self.assertNotIn("--focus", argv)

    def test_pane_from_list_is_internal(self):
        pane = MOD.pane_from_list(
            [{"tab_id": "w7:t1", "pane_id": "w7:p1", "cwd": "/tmp"}],
            "w7:t1",
        )
        self.assertEqual(pane["pane_id"], "w7:p1")

    def test_public_tab_hides_pane_id(self):
        row = MOD.public_tab(
            {"workspace_id": "w7", "tab_id": "w7:t1", "label": "research", "agent_status": "idle"},
            {"pane_id": "w7:p1", "cwd": "/tmp/proj", "agent": "pi"},
            {"name": "research", "agent": "pi", "cwd": "/tmp/proj"},
        )
        self.assertNotIn("pane_id", row)
        self.assertEqual(row["tab_id"], "w7:t1")
        self.assertEqual(row["name"], "research")
        self.assertEqual(row["kind"], "pi")


if __name__ == "__main__":
    unittest.main()

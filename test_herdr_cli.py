#!/usr/bin/env python3
import unittest
from unittest.mock import patch
import tempfile

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


class JournalSendTest(unittest.TestCase):
    def test_journal_failure_does_not_fail_successful_file_send(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "private-prompt.md"
            path.write_text("private prompt from a file")
            with patch.object(MOD, "resolve_target", return_value="w7:pC1"), \
                 patch.object(MOD, "herdr", return_value={"sent": True}) as herdr, \
                 patch.object(MOD, "journal_send", side_effect=OSError(28, "disk full")), \
                 patch.object(MOD, "emit_ok", return_value=0):
                self.assertEqual(MOD.cmd_send(["w7:tC1", "--no-prefix", "--file", str(path)]), 0)
                self.assertEqual(herdr.call_args.args[0][3], "private prompt from a file")


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


class SenderPrefixTest(unittest.TestCase):
    def test_prefix_names_workspace_tab_and_label(self):
        env = {"HERDR_TAB_ID": "wH:tE", "HERDR_WORKSPACE_ID": "wH"}
        with patch.dict(MOD.os.environ, env, clear=False), \
             patch.object(MOD, "workspaces", return_value=[{"workspace_id": "wH", "label": "gov"}]), \
             patch.object(MOD, "tab_info", return_value={"label": "\u2b50 Manager"}):
            self.assertEqual(MOD.sender_prefix("hello"), "[gov wH:tE Manager] ")
            self.assertEqual(MOD.sender_prefix("[gov wH:tE Manager] hello"), "")

    def test_no_prefix_outside_herdr(self):
        with patch.dict(MOD.os.environ, {}, clear=True):
            self.assertEqual(MOD.sender_prefix("hello"), "")

    def test_lookup_failure_still_gives_ids(self):
        env = {"HERDR_TAB_ID": "w7:tC1", "HERDR_WORKSPACE_ID": "w7"}
        with patch.dict(MOD.os.environ, env, clear=False), \
             patch.object(MOD, "workspaces", side_effect=Exception("down")), \
             patch.object(MOD, "tab_info", side_effect=Exception("down")):
            self.assertEqual(MOD.sender_prefix("hi"), "[w7 w7:tC1] ")


if __name__ == "__main__":
    unittest.main()

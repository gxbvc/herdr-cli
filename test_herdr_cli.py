#!/usr/bin/env python3
import unittest
import os
import json
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
        argv = MOD.prompt_argv("w0:t1", "# Title\n--wait is content")
        self.assertEqual(argv[:3], ["agent", "prompt", "w0:t1"])
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
            with patch.object(MOD, "resolve_target", return_value="w0:pC1"), \
                 patch.object(MOD, "herdr", return_value={"sent": True}) as herdr, \
                 patch.object(MOD, "journal_send", side_effect=OSError(28, "disk full")), \
                 patch.object(MOD, "emit_ok", return_value=0):
                self.assertEqual(MOD.cmd_send(["w0:tC1", "--no-prefix", "--file", str(path)]), 0)
                self.assertEqual(herdr.call_args.args[0][3], "private prompt from a file")

    def test_journal_path_comes_from_the_env_or_the_setting_file_else_none(self):
        with tempfile.TemporaryDirectory() as home:
            with patch.dict(MOD.os.environ, {"HOME": home}, clear=True):  # Path.home() reads HOME
                self.assertIsNone(MOD.journal_module_path())
                cfg = Path(home) / ".config/herdr-cli"
                cfg.mkdir(parents=True)
                (cfg / "journal").write_text("~/bin/journal.py\n")
                self.assertEqual(MOD.journal_module_path(), Path(home) / "bin/journal.py")
            with patch.dict(MOD.os.environ, {"HOME": home, "HERDR_CLI_JOURNAL": "/opt/j.py"}, clear=True):
                self.assertEqual(MOD.journal_module_path(), Path("/opt/j.py"))

    def test_no_journal_setting_means_no_journal_call(self):
        with patch.object(MOD, "journal_module_path", return_value=None), \
             patch("importlib.util.spec_from_file_location") as spec:
            MOD.journal_send("w0:t1")
            spec.assert_not_called()


class TabSurfaceTest(unittest.TestCase):
    def test_tab_create_has_no_focus_and_no_pane_flag(self):
        argv = MOD.tab_create_argv("w0", cwd="/tmp/proj", label="research")
        self.assertEqual(
            argv,
            ["tab", "create", "--workspace", "w0", "--no-focus", "--cwd", "/tmp/proj", "--label", "research"],
        )
        self.assertNotIn("--pane", argv)
        self.assertNotIn("--focus", argv)

    def test_pane_from_list_is_internal(self):
        pane = MOD.pane_from_list(
            [{"tab_id": "w0:t1", "pane_id": "w0:p1", "cwd": "/tmp"}],
            "w0:t1",
        )
        self.assertEqual(pane["pane_id"], "w0:p1")

    def test_public_tab_hides_pane_id(self):
        row = MOD.public_tab(
            {"workspace_id": "w0", "tab_id": "w0:t1", "label": "research", "agent_status": "idle"},
            {"pane_id": "w0:p1", "cwd": "/tmp/proj", "agent": "pi"},
            {"name": "research", "agent": "pi", "cwd": "/tmp/proj"},
        )
        self.assertNotIn("pane_id", row)
        self.assertEqual(row["tab_id"], "w0:t1")
        self.assertEqual(row["name"], "research")
        self.assertEqual(row["kind"], "pi")


class SenderPrefixTest(unittest.TestCase):
    def test_prefix_names_workspace_tab_and_label(self):
        env = {"HERDR_TAB_ID": "w0:tE", "HERDR_WORKSPACE_ID": "wH"}
        with patch.dict(MOD.os.environ, env, clear=False), \
             patch.object(MOD, "workspaces", return_value=[{"workspace_id": "wH", "label": "gov"}]), \
             patch.object(MOD, "tab_info", return_value={"label": "\u2b50 Manager"}):
            self.assertEqual(MOD.sender_prefix("hello"), "[gov w0:tE Manager] ")
            self.assertEqual(MOD.sender_prefix("[gov w0:tE Manager] hello"), "")

    def test_no_prefix_outside_herdr(self):
        with patch.dict(MOD.os.environ, {}, clear=True):
            self.assertEqual(MOD.sender_prefix("hello"), "")

    def test_tmux_ignores_inherited_herdr_tab(self):
        # Security, Nov 16: a tmux watcher inherited the tmux server's HERDR_TAB_ID (another tab).
        env = {"TMUX": "/tmp/tmux-501/default,1724,0", "TMUX_PANE": "%3",
               "HERDR_TAB_ID": "w0:t5H", "HERDR_WORKSPACE_ID": "w0"}
        with patch.dict(MOD.os.environ, env, clear=True), \
             patch.object(MOD, "tmux_session_name", return_value="cui-first-watch"), \
             patch.object(MOD, "workspaces", return_value=[{"workspace_id": "w0", "label": "acme"}]), \
             patch.object(MOD, "tab_info", return_value={"label": "Acme manager"}):
            self.assertEqual(MOD.sender_prefix("WAKE"), "[tmux cui-first-watch] ")
            self.assertEqual(MOD.sender_prefix("[tmux cui-first-watch] WAKE"), "")
            self.assertEqual(MOD.sender_prefix("/new"), "")

    def test_journal_sender_id_matches_header(self):
        with patch.dict(MOD.os.environ, {"TMUX": "x", "HERDR_TAB_ID": "w0:t5H"}, clear=True), \
             patch.object(MOD, "tmux_session_name", return_value="l120-psi"):
            self.assertEqual(MOD.sender_id(), "tmux:l120-psi")
        with patch.dict(MOD.os.environ, {"HERDR_TAB_ID": "w0:tC1"}, clear=True):
            self.assertEqual(MOD.sender_id(), "w0:tC1")
        with patch.dict(MOD.os.environ, {}, clear=True):
            self.assertEqual(MOD.sender_id(), "external")

    def test_tmux_session_lookup_failure(self):
        with patch.dict(MOD.os.environ, {"TMUX": "x"}, clear=True), \
             patch.object(MOD.subprocess, "run", side_effect=Exception("no tmux")):
            self.assertEqual(MOD.sender_prefix("hi"), "[tmux unknown] ")

    def test_lookup_failure_still_gives_ids(self):
        env = {"HERDR_TAB_ID": "w0:tC1", "HERDR_WORKSPACE_ID": "w0"}
        with patch.dict(MOD.os.environ, env, clear=False), \
             patch.object(MOD, "workspaces", side_effect=Exception("down")), \
             patch.object(MOD, "tab_info", side_effect=Exception("down")):
            self.assertEqual(MOD.sender_prefix("hi"), "[w0 w0:tC1] ")


class RpiSendTest(unittest.TestCase):
    """herdr 0.9.1 cannot `agent prompt` an rpi tab; send types into the pane and presses Enter."""

    RPI = {"name": "rpi-test", "tab_id": "w0:t2", "pane_id": "w0:p2", "agent": "rpi"}
    PI = {"name": "misc", "tab_id": "w0:tC1", "pane_id": "w0:pC1", "agent": "pi"}

    def run_send(self, argv, rows):
        calls = []

        def fake(args, timeout=None):
            calls.append((list(args), timeout))
            if args[:2] == ["agent", "list"]:
                return {"agents": rows}
            return {}

        with patch.object(MOD, "herdr", side_effect=fake), \
             patch.object(MOD, "journal_send", return_value=None), \
             patch.object(MOD, "emit_ok", side_effect=lambda data: data):
            out = MOD.cmd_send(argv)
        return out, [c for c in calls if c[0][:2] != ["agent", "list"]]

    def test_rpi_by_name_uses_send_text_then_enter_with_3s_timeouts(self):
        out, calls = self.run_send(["rpi-test", "--no-prefix", "line one\nline two"], [self.RPI])
        self.assertEqual(calls, [(["pane", "send-text", "w0:p2", "line one\nline two"], 3),
                                 (["pane", "send-keys", "w0:p2", "enter"], 3)])
        self.assertEqual(out["kind"], "rpi")

    def test_rpi_by_tab_id(self):
        _, calls = self.run_send(["w0:t2", "--no-prefix", "hi"], [self.RPI])
        self.assertEqual(calls[0][0][:3], ["pane", "send-text", "w0:p2"])

    def test_pi_still_uses_agent_prompt(self):
        _, calls = self.run_send(["misc", "--no-prefix", "hi"], [self.PI])
        self.assertEqual(calls, [(["agent", "prompt", "misc", "hi"], None)])

    def test_rpi_wait_is_refused(self):
        with self.assertRaises(MOD.HerdrError):
            self.run_send(["rpi-test", "--no-prefix", "--wait", "hi"], [self.RPI])

    def test_send_text_failure_never_presses_enter(self):
        calls = []

        def fake(args, timeout=None):
            calls.append(list(args))
            if args[:2] == ["agent", "list"]:
                return {"agents": [self.RPI]}
            if args[:2] == ["pane", "send-text"]:
                raise MOD.HerdrError("herdr timed out", "TIMEOUT")
            return {}

        with patch.object(MOD, "herdr", side_effect=fake), patch.object(MOD, "journal_send", return_value=None):
            with self.assertRaises(MOD.HerdrError):
                MOD.cmd_send(["rpi-test", "--no-prefix", "hi"])
        self.assertNotIn(["pane", "send-keys", "w0:p2", "enter"], calls)


class RpiStartTest(unittest.TestCase):
    """herdr 0.9.1 cannot `agent start --kind rpi`: start runs rpi in the pane, waits for it to report, names it."""

    def fake_herdr(self, calls, report_after=1):
        state = {"lists": 0}

        def fake(args, timeout=None):
            calls.append(list(args))
            if args[:2] == ["agent", "list"]:
                state["lists"] += 1
                kind = "rpi" if state["lists"] > report_after else None
                return {"agents": [{"pane_id": "w0:pY4", "tab_id": "w0:tY4", "agent": kind, "name": None}]}
            if args[:2] == ["pane", "list"]:
                return {"panes": [{"pane_id": "w0:pY4", "tab_id": "w0:tY4"}]}
            return {"agent": {"name": "x"}}

        return fake

    def test_start_rpi_runs_binary_with_model_then_renames(self):
        calls = []
        with patch.object(MOD, "herdr", side_effect=self.fake_herdr(calls)), \
             patch.object(MOD, "pane_for_tab", return_value={"pane_id": "w0:pY4"}), \
             patch.object(MOD.time, "sleep", return_value=None), \
             patch.object(MOD, "emit_ok", side_effect=lambda data: data), \
             patch.object(MOD, "RPI_SESSIONS", tempfile.mkdtemp()):
            out = MOD.cmd_start(["lane1", "--tab", "w0:tY4", "--kind", "rpi", "--model", "cliproxy-fireworks/glm-5p3-flash"])
        run = [c for c in calls if c[:2] == ["pane", "run"]][0]
        self.assertEqual(run[2], "w0:pY4")
        self.assertIn("rpi-guard/rpi-guarded --model cliproxy-fireworks/glm-5p3-flash --session-dir ", run[3])
        self.assertNotIn(".local/bin/rpi", run[3])  # never the stock, self-updating rpi (Nov 13)
        self.assertIn(["agent", "rename", "w0:pY4", "lane1"], calls)
        self.assertNotIn("start", [c[1] for c in calls if c[0] == "agent"])
        self.assertEqual(out["kind"], "rpi")

    def test_start_rpi_times_out_without_report(self):
        calls = []
        with patch.object(MOD, "herdr", side_effect=self.fake_herdr(calls, report_after=10**6)), \
             patch.object(MOD, "pane_for_tab", return_value={"pane_id": "w0:pY4"}), \
             patch.object(MOD.time, "sleep", return_value=None), \
             patch.object(MOD.time, "monotonic", side_effect=[0, 0, 5, 30, 30]), \
             patch.object(MOD, "RPI_SESSIONS", tempfile.mkdtemp()):
            with self.assertRaises(MOD.HerdrError):
                MOD.cmd_start(["lane1", "--tab", "w0:tY4", "--kind", "rpi"])
        self.assertFalse(any(c[:2] == ["agent", "rename"] for c in calls))

    def test_pi_start_unchanged_and_model_flag_goes_after_dashdash(self):
        calls = []
        with patch.object(MOD, "herdr", side_effect=lambda a, timeout=None: calls.append(list(a)) or {}), \
             patch.object(MOD, "pane_for_tab", return_value={"pane_id": "w0:p9"}), \
             patch.object(MOD, "emit_ok", side_effect=lambda data: data):
            MOD.cmd_start(["lane2", "--tab", "w0:t9", "--model", "fireworks/x"])
        self.assertEqual(calls, [["agent", "start", "lane2", "--kind", "pi", "--pane", "w0:p9", "--", "--model", "fireworks/x"]])

    def test_old_dashdash_model_form_still_works(self):
        head, extra = MOD.split_extra(["lane3", "--", "--model", "a/b"])
        self.assertEqual((head, extra), (["lane3"], ["--model", "a/b"]))


class RpiSessionTest(unittest.TestCase):
    """rpi keeps sessions in <cwd>/.rpi unless told; start passes a per-name --session-dir and status reads it."""

    def test_start_adds_session_dir_per_name(self):
        calls = []
        tmp = tempfile.mkdtemp()

        def fake(args, timeout=None):
            calls.append(list(args))
            if args[:2] == ["agent", "list"]:
                return {"agents": [{"pane_id": "w0:p1", "agent": "rpi"}]}
            return {}

        with patch.object(MOD, "herdr", side_effect=fake), patch.object(MOD, "RPI_SESSIONS", tmp):
            MOD.start_rpi_on_pane("mgr-x", "w0:p1", extra=["--model", "cliproxy/claude-opus-5-5"])
        run = [c for c in calls if c[:2] == ["pane", "run"]][0][3]
        self.assertIn("--session-dir " + os.path.join(tmp, "mgr-x"), run)
        self.assertTrue(os.path.isdir(os.path.join(tmp, "mgr-x")))
        self.assertEqual(os.stat(os.path.join(tmp, "mgr-x")).st_mode & 0o777, 0o700)

    def test_status_session_for_rpi_reads_newest_file_and_epoch_ms(self):
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "mgr-x", "--private-tmp--"))
        old = os.path.join(tmp, "mgr-x", "a.jsonl")
        new = os.path.join(tmp, "mgr-x", "--private-tmp--", "b.jsonl")
        open(old, "w").write("")
        line = json.dumps({"kind": "entry", "type": "message", "timestamp": 1794194871548,
                           "message": {"role": "assistant", "content": [{"type": "text", "text": "Ready?"}],
                                       "usage": {"totalTokens": 3142}}}, separators=(",", ":"))
        open(new, "w").write(line + "\n")
        os.utime(old, (1, 1))
        with patch.object(MOD, "RPI_SESSIONS", tmp):
            path = MOD.agent_session_path({"agent": "rpi", "name": "mgr-x"})
            self.assertEqual(path, new)
            self.assertIsNone(MOD.agent_session_path({"agent": "rpi", "name": "other"}))
            self.assertEqual(MOD.agent_session_path({"agent": "pi", "name": "mgr-x", "agent_session": {"value": "/p"}}), "/p")
        facts = MOD.session_facts(path)
        self.assertEqual(facts["context_tokens"], 3142)
        self.assertTrue(facts["ends_with_question"])
        self.assertTrue(facts["last_assistant_at"].startswith("2026-11-09T03:27:51"))


if __name__ == "__main__":
    unittest.main()

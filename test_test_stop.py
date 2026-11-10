#!/usr/bin/env python3
"""Test stop (GXB_TEST_NO_REAL_IO, Nov 10): only read commands run; every other command exits 3 before herdr is
called. Run: python3 -m unittest test_test_stop (from ~/tools/herdr-cli). The process run uses HERDR=/bin/false and
an empty socket path, so even a failed stop could not reach a herdr pane."""
import importlib.machinery
import importlib.util
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

EXE = Path(__file__).with_name("herdr-cli")
LOADER = importlib.machinery.SourceFileLoader("herdrcli_stop", str(EXE))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MOD = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MOD)

READS = {"workspaces", "tabs", "list", "status"}
ON = {"GXB_TEST_NO_REAL_IO": "1"}


class TestStop(unittest.TestCase):
    def test_every_command_is_a_read_or_refused(self):
        self.assertGreaterEqual(len(MOD.COMMANDS), 15)
        for name in MOD.COMMANDS:
            self.assertEqual(MOD.test_stop_refuses([name], ON), name not in READS, name)
        for name in ("send", "ask", "spawn", "start", "star", "unstar", "rename", "move", "move-workspace"):
            self.assertTrue(MOD.test_stop_refuses([name, "x"], ON), name)

    def test_a_command_added_later_is_refused(self):
        self.assertTrue(MOD.test_stop_refuses(["frobnicate"], ON))

    def test_any_non_empty_value_turns_it_on(self):
        for v in ("1", "yes", "true", "0", "no", "false", "x"):
            self.assertTrue(MOD.test_stop_refuses(["send"], {"GXB_TEST_NO_REAL_IO": v}), v)
        self.assertFalse(MOD.test_stop_refuses(["send"], {"GXB_TEST_NO_REAL_IO": ""}))
        self.assertFalse(MOD.test_stop_refuses(["send"], {}))

    def test_main_refuses_before_any_herdr_call(self):
        def no_call(*a, **k):
            raise AssertionError("herdr was called")
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, ON), patch.object(MOD, "herdr", no_call), patch.object(MOD.subprocess, "run", no_call), \
                redirect_stdout(out), redirect_stderr(err):
            code = MOD.main(["send", "gxbot-mgr", "hello"])
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(out.getvalue())["code"], "TEST_NO_REAL_IO")
        self.assertIn("TEST STOP", err.getvalue())

    def test_executable_refuses_send_with_exit_3(self):
        env = dict(os.environ, **ON, HERDR="/bin/false", HERDR_SOCKET_PATH="/nonexistent/herdr.sock")
        r = subprocess.run([sys.executable, str(EXE), "send", "gxbot-mgr", "hello"], env=env, capture_output=True,
                           text=True, timeout=30)
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertEqual(json.loads(r.stdout)["code"], "TEST_NO_REAL_IO")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations
import copy
import json
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ashfall_harness.common import HarnessError
from ashfall_harness.unity_config import editmode_gate, integration_command

class UnityCommandTests(unittest.TestCase):
    def test_nonexistent_editor_refused(self):
        with self.assertRaises(HarnessError):editmode_gate(Path("NoEditor"),["X.Y"])
    def test_test_process_does_not_use_quit(self):
        with tempfile.TemporaryDirectory() as d:
            editor=Path(d)/"Unity.exe";editor.write_bytes(b"placeholder only not executable")
            g=editmode_gate(editor,["Tests.A"])
            self.assertNotIn("-quit",g["argv"])
            self.assertIn("-runTests",g["argv"])
            self.assertEqual(g["required_test_names"],["Tests.A"])
    def test_method_not_shell(self):
        with tempfile.TemporaryDirectory() as d:
            editor=Path(d)/"Unity.exe";editor.write_bytes(b"placeholder only")
            with self.assertRaises(HarnessError):integration_command(editor,"A.Run; do_more")

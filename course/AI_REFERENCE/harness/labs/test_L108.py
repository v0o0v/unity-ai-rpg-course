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
from ashfall_harness.common import HarnessError, FileLock, event, read_json

class LockTests(unittest.TestCase):
    def test_second_owner_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"lock"
            with FileLock(p,"demo"):
                with self.assertRaises(HarnessError):
                    with FileLock(p,"demo"): pass
            self.assertFalse(p.exists())
    def test_event_is_append_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); event(p,"START"); event(p,"END")
            lines=(p/"events.jsonl").read_text().splitlines()
            self.assertEqual([json.loads(x)["kind"] for x in lines],["START","END"])
    def test_role_permissions_are_distinct(self):
        c=read_json(Path(__file__).resolve().parents[1]/"config/demo.json")
        self.assertEqual(c["roles"]["critic"]["write_prefixes"],[])
        self.assertNotEqual(c["roles"]["qa_engineer"]["write_prefixes"],c["roles"]["gameplay_engineer"]["write_prefixes"])

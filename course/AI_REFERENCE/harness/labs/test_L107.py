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
from ashfall_harness.common import HarnessError, safe_relative, is_inside, scan, copy_manifest

class SnapshotTests(unittest.TestCase):
    def test_escape_refused(self):
        for p in ["../x", "C:/x", "a\\b", "a/NUL.txt"]:
            with self.subTest(path=p), self.assertRaises(HarnessError): safe_relative(p)
    def test_prefix_is_path_aware(self):
        self.assertTrue(is_inside("Game/a.py","Game"))
        self.assertFalse(is_inside("Gameplay/a.py","Game"))
    def test_copy_preserves_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"source"; (root/"Game").mkdir(parents=True)
            (root/"Game/a.py").write_text("value=1",encoding="utf-8")
            m=scan(root,["Game"]); copy_manifest(root,Path(d)/"candidate",m)
            self.assertEqual(m,scan(Path(d)/"candidate",["Game"]))
    def test_secret_named_file_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/".env").write_text("DEMO_ONLY=1")
            with self.assertRaises(HarnessError): scan(root,[".env"])

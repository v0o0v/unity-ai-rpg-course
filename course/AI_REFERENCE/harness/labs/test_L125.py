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


class UnityLabSourcePackagingTests(unittest.TestCase):
    def test_assemblies_have_distinct_names(self):
        root=Path(__file__).resolve().parents[1]/"unity_lab/Assets/HarnessLab"
        names=[json.loads(p.read_text())["name"] for p in root.rglob("*.asmdef")]
        self.assertEqual(len(names),3);self.assertEqual(len(set(names)),3)
    def test_lab_is_not_a_fabricated_project(self):
        root=Path(__file__).resolve().parents[1]/"unity_lab"
        self.assertFalse((root/"ProjectSettings/ProjectVersion.txt").exists())
        self.assertTrue((root/"Assets/HarnessLab/Tests/Editor/LootFilterTests.cs").exists())

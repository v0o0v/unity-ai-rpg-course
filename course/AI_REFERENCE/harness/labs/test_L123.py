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
import importlib.util
from ashfall_harness.common import HarnessError
_SPEC=importlib.util.spec_from_file_location("workbook_lesson",Path(__file__).resolve().parents[1]/"expansion2d/tools/workbook.py")
workbook=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(workbook)


class BindingToolTests(unittest.TestCase):
    def test_module_loads_without_unity(self):
        self.assertTrue(callable(workbook.bind))
    def test_output_inside_project_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(HarnessError):workbook._outside(root,root/"out")
    def test_new_output_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json";workbook.write_new(p,{"a":1})
            with self.assertRaises(FileExistsError):workbook.write_new(p,{"a":2})

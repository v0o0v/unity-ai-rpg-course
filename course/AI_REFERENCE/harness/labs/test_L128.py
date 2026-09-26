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
_SPEC=importlib.util.spec_from_file_location("smoke",Path(__file__).resolve().parents[1]/"examples/smoke.py")
_module=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(_module);smoke=_module.smoke


class GraduationSmokeTests(unittest.TestCase):
    def test_actual_smoke_uses_created_runner(self):
        with tempfile.TemporaryDirectory() as d:
            result=smoke(Path(d)/"new-smoke")
            self.assertEqual(result["gate_report"]["counts"]["passed"],5)
            self.assertEqual(result["release_status"],"DEMO_ONLY")
    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaises(HarnessError):smoke(Path(d))

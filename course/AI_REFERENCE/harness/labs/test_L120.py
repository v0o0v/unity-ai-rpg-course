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
from ashfall_harness.common import HarnessError, read_json
from ashfall_harness.planner import draft, validate_draft


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class PlannerTests(unittest.TestCase):
    def test_mock_plan_is_not_executed(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"plan"
            result=draft(ROOT/"examples/demo_project",c,"damage fix",["Docs/GAME_SPEC.md"],out,"mock",ROOT/"examples/planner.fixture.json")
            self.assertEqual(result["status"],"DRAFT_REVIEW_REQUIRED")
            self.assertFalse(result["executed"])
            self.assertFalse((out/"run.json").exists())
    def test_command_injection_into_plan_refused(self):
        p,c=fixture();p=read_json(ROOT/"examples/planner.fixture.json");p["commands"]=["do anything"]
        with self.assertRaises(HarnessError):validate_draft(p,c,{})
    def test_invented_read_file_refused(self):
        p,c=fixture();p=read_json(ROOT/"examples/planner.fixture.json");p["tasks"][0]["read_files"]=["Game/Imaginary.cs"]
        with self.assertRaises(HarnessError):validate_draft(p,c,{})
    def test_live_is_opt_in(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d,self.assertRaises(HarnessError):
            draft(ROOT/"examples/demo_project",c,"x",["Docs/GAME_SPEC.md"],Path(d)/"out","claude")

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
from ashfall_harness.engine import init_run, run_tasks, stage, seal
from ashfall_harness.evidence import run_gate


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class GateTests(unittest.TestCase):
    def test_full_mock_and_real_five_tests(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run"; dest=Path(d)/"candidate"
            init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            r=run_tasks(run);stage(run,dest,r["candidate_sha256"]);seal(run,"test fixture approval")
            result=run_gate(run,"demo_rules",True)
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["counts"]["passed"],5)
    def test_unapproved_execution_refused(self):
        with self.assertRaises(HarnessError): run_gate(Path("not-used"),"x",False)
    def test_changes_after_seal_refused(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";dest=Path(d)/"candidate"
            init_run(ROOT/"examples/demo_project",run,p,c,"mock");r=run_tasks(run)
            stage(run,dest,r["candidate_sha256"]);seal(run,"test")
            (dest/"Game/rules.py").write_text("changed=1")
            with self.assertRaises(HarnessError): run_gate(run,"demo_rules",True)

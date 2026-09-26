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
from ashfall_harness.engine import init_run, run_tasks, stage, seal, status, dashboard
from ashfall_harness.evidence import run_gate, attest


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class ReportTests(unittest.TestCase):
    def test_mock_never_becomes_release(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            r=run_tasks(run);stage(run,Path(d)/"candidate",r["candidate_sha256"]);seal(run,"test")
            run_gate(run,"demo_rules",True)
            self.assertEqual(status(run)["release_status"],"DEMO_ONLY")
            self.assertIn("DEMO_ONLY",dashboard(run).read_text())
    def test_auto_gate_cannot_be_replaced_by_human(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            r=run_tasks(run);stage(run,Path(d)/"candidate",r["candidate_sha256"]);seal(run,"test")
            e=Path(d)/"e.txt";e.write_text("I tried it")
            with self.assertRaises(HarnessError): attest(run,"demo_rules",e,"note","learner",True,True)

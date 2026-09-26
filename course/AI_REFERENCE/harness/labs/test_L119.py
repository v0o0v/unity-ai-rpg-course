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
from ashfall_harness.common import HarnessError, read_json, atomic_json
from ashfall_harness.engine import init_run, run_tasks
from ashfall_harness.diagnostics import diagnose


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class RecoveryTests(unittest.TestCase):
    def test_running_is_not_automatically_retried(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            s=read_json(run/"state.json");s["design"]["status"]="RUNNING";atomic_json(run/"state.json",s)
            with self.assertRaises(HarnessError):run_tasks(run)
            self.assertFalse(diagnose(run)["automatic_retry"])
    def test_budget_unknown_blocks_even_explicit_retry(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            m=read_json(run/"run.json");m["budget_unknown"]=True;atomic_json(run/"run.json",m)
            with self.assertRaises(HarnessError):run_tasks(run)
            self.assertIn("STOP_BUDGET_UNKNOWN",diagnose(run)["actions"][0])

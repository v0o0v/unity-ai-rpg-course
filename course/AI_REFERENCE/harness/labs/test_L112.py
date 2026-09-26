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
from ashfall_harness.engine import init_run, run_tasks


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class RunnerTests(unittest.TestCase):
    def test_mock_completes_and_does_not_edit_source(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            source=ROOT/"examples/demo_project";before=(source/"Game/rules.py").read_bytes()
            run=Path(d)/"run";init_run(source,run,p,c,"mock")
            result=run_tasks(run)
            self.assertEqual(result["status"],"PROPOSALS_REVIEWED")
            self.assertEqual((source/"Game/rules.py").read_bytes(),before)
    def test_second_run_reuses_done_without_extra_attempt(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            run_tasks(run);run_tasks(run)
            self.assertTrue(all(x["attempts"]==1 for x in read_json(run/"state.json").values()))
    def test_paid_path_requires_explicit_choice(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"claude")
            with self.assertRaises(HarnessError): run_tasks(run)

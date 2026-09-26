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
from ashfall_harness.engine import init_run, prepare_task_view


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class InitTests(unittest.TestCase):
    def test_init_records_waiting_and_snapshot(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run"; init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            self.assertEqual(read_json(run/"state.json")["design"]["status"],"WAITING")
            self.assertTrue((run/"snapshot/Game/rules.py").is_file())
    def test_init_does_not_overwrite(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run"; init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            with self.assertRaises(HarnessError): init_run(ROOT/"examples/demo_project",run,p,c,"mock")
    def test_view_contains_only_selected_inputs(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run"; init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            view=Path(d)/"view"; prepare_task_view(run,view,p["tasks"][0],[],read_json(run/"state.json"))
            self.assertTrue((view/"Docs/GAME_SPEC.md").exists())
            self.assertFalse((view/"Game/rules.py").exists())

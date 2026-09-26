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
from ashfall_harness.engine import init_run, run_tasks, stage


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class StageTests(unittest.TestCase):
    def test_approval_hash_required(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock");run_tasks(run)
            with self.assertRaises(HarnessError): stage(run,Path(d)/"candidate","made-up")
    def test_candidate_contains_qa_test(self):
        p,c=fixture()
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock");r=run_tasks(run)
            stage(run,Path(d)/"candidate",r["candidate_sha256"])
            self.assertTrue((Path(d)/"candidate/Tests/test_rules.py").exists())
    def test_failed_review_prevents_stage(self):
        p,c=fixture(); p["tasks"][-1]["mock_response"]["outcome"]="review_fail"
        p["tasks"][-1]["mock_response"]["findings"]=["수정 필요"]
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock");run_tasks(run)
            with self.assertRaises(HarnessError): stage(run,Path(d)/"candidate","unused")

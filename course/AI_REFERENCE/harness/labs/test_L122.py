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
from ashfall_harness.common import HarnessError, atomic_json
from ashfall_harness.json_gate import parse_json_checks
from ashfall_harness.engine import validate_config


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class JsonGateTests(unittest.TestCase):
    def test_summary_cannot_override_case(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.json";atomic_json(p,{"schema_version":1,"summary":"PASS","checks":[{"id":"a","passed":False,"detail":"bad"}]})
            with self.assertRaises(HarnessError):parse_json_checks(p)
    def test_zero_and_duplicate_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.json"
            for checks in [[],[{"id":"a","passed":True,"detail":"ok"}]*2]:
                atomic_json(p,{"schema_version":1,"checks":checks})
                with self.assertRaises(HarnessError):parse_json_checks(p)
    def test_new_parser_accepts_named_checks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.json";atomic_json(p,{"schema_version":1,"checks":[{"id":"a","passed":True,"detail":"ok"}]})
            self.assertEqual(parse_json_checks(p,1,["a"])["passed"],1)
    def test_unknown_parser_remains_refused(self):
        p,c=fixture();c["gates"]["demo_rules"]["kind"]="trust_me"
        with self.assertRaises(HarnessError):validate_config(c)
    def test_json_kind_is_registered(self):
        p,c=fixture();c["gates"]["demo_rules"]["kind"]="json_checks";validate_config(c)
    def test_actual_catalog_gate_uses_sealed_candidate_data(self):
        from ashfall_harness.engine import init_run, run_tasks, stage, seal
        from ashfall_harness.evidence import run_gate
        p,c=fixture()
        c["gates"]={"catalog":{"kind":"json_checks","enabled":True,"required":True,
            "argv":["{python}","{project}/Game/catalog_audit.py","{project}/Game/catalog.json"],
            "minimum_tests":3,"required_test_names":["items_present","ids_unique","references_valid"],"timeout_seconds":10}}
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source";shutil.copytree(ROOT/"examples/demo_project",source)
            shutil.copy2(ROOT/"tools/catalog_audit.py",source/"Game/catalog_audit.py")
            shutil.copy2(ROOT/"examples/catalog.json",source/"Game/catalog.json")
            run=Path(d)/"run";init_run(source,run,p,c,"mock");r=run_tasks(run)
            stage(run,Path(d)/"candidate",r["candidate_sha256"]);seal(run,"fixture only")
            result=run_gate(run,"catalog",True)
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["counts"]["passed"],3)

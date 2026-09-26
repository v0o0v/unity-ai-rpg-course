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
from ashfall_harness.engine import validate_plan, validate_config


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class PlanTests(unittest.TestCase):
    def test_order(self):
        p,c=fixture(); self.assertEqual([t["id"] for t in validate_plan(p,c)],["design","implement","test","review"])
    def test_cycle(self):
        p,c=fixture(); p["tasks"][0]["depends_on"]=["review"]
        with self.assertRaises(HarnessError): validate_plan(p,c)
    def test_role_cannot_expand_permissions(self):
        p,c=fixture(); p["tasks"][1]["write_prefixes"]=["Tests"]
        with self.assertRaises(HarnessError): validate_plan(p,c)
    def test_required_gate(self):
        p,c=fixture(); c["gates"]={}
        with self.assertRaises(HarnessError): validate_config(c)

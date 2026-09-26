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
from ashfall_harness.customize import add_role


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class CustomRoleTests(unittest.TestCase):
    def test_new_role_does_not_change_source_config(self):
        p,c=fixture();new=add_role(c,"catalog_auditor","ID검수","중복 확인",["Docs/Audit"])
        self.assertIn("catalog_auditor",new["roles"])
        self.assertNotIn("catalog_auditor",c["roles"])
    def test_duplicate_role_refused(self):
        p,c=fixture()
        with self.assertRaises(HarnessError):add_role(c,"critic","x","y",[])
    def test_escape_refused(self):
        p,c=fixture()
        with self.assertRaises(HarnessError):add_role(c,"new_role","x","y",["../Outside"])

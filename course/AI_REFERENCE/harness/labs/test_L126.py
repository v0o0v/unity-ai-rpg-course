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
import importlib.util
from ashfall_harness.common import HarnessError
_SPEC=importlib.util.spec_from_file_location("prepare_lab",Path(__file__).resolve().parents[1]/"examples/prepare_unity_lab.py")
_module=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(_module);prepare=_module.prepare


class LabPlanTests(unittest.TestCase):
    def test_missing_unity_project_is_blocked(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaises(HarnessError):
            prepare(Path(d)/"not-unity",Path(d)/"plan",True)
    def test_mock_plan_has_no_enabled_unity_command(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"project"
            for name,txt in [("Packages/manifest.json","{}"),("ProjectSettings/ProjectVersion.txt","fixture, not actual editor"),("Docs/GAME_SPEC.md","fixture"),("Docs/HARNESS_LAB_SPEC.md","fixture")]:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt)
            (root/"Assets").mkdir()
            out=Path(d)/"out";result=prepare(root,out,True)
            self.assertEqual(result["status"],"PLAN_ONLY_COMMANDS_NOT_BOUND")
            config=json.loads((out/"config.json").read_text())
            self.assertTrue(any(g.get("required") and not g.get("enabled") for g in config["gates"].values()))

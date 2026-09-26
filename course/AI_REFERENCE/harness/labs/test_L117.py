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
from ashfall_harness.engine import init_run, run_tasks, stage, seal
from ashfall_harness.evidence import integrate


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class IntegrationTests(unittest.TestCase):
    def test_registered_command_is_executed_but_not_verified(self):
        p,c=fixture(); c["integration_commands"]={"probe":{"enabled":True,"argv":["{python}","-c","print('integration-probe')"],"timeout_seconds":10}}
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/"run";init_run(ROOT/"examples/demo_project",run,p,c,"mock")
            r=run_tasks(run);stage(run,Path(d)/"candidate",r["candidate_sha256"]);seal(run,"old")
            result=integrate(run,"probe",True)
            self.assertEqual(result["status"],"EXECUTED_NOT_VERIFIED")
            self.assertNotIn("seal_id",read_json(run/"run.json"))
    def test_missing_approval_refused(self):
        with self.assertRaises(HarnessError): integrate(Path("unused"),"probe",False)

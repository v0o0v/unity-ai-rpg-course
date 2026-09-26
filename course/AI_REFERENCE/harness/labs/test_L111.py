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
from ashfall_harness.engine import validate_response


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class ResponseTests(unittest.TestCase):
    def test_response_is_bound_to_input(self):
        p,c=fixture(); task=p["tasks"][0]
        value={"task_id":"design","input_sha256":"old","outcome":"proposal","summary":"note","files":[],"findings":[]}
        with self.assertRaises(HarnessError): validate_response(value,task,"current",{},c)
    def test_reviewer_cannot_patch(self):
        p,c=fixture(); task=p["tasks"][-1]
        value={"task_id":"review","input_sha256":"h","outcome":"review_pass","summary":"note","files":[{"path":"Game/x.py","expected_sha256":None,"content":"x=1"}],"findings":[]}
        with self.assertRaises(HarnessError): validate_response(value,task,"h",{},c)
    def test_valid_proposal(self):
        p,c=fixture();task=p["tasks"][1]
        value={"task_id":"implement","input_sha256":"h","outcome":"proposal","summary":"proposal only","files":[{"path":"Game/new.py","expected_sha256":None,"content":"x=1"}],"findings":[]}
        validate_response(value,task,"h",{},c)

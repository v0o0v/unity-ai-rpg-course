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
from ashfall_harness.provider import command


ROOT = Path(__file__).resolve().parents[1]

def fixture():
    from ashfall_harness.common import read_json
    return read_json(ROOT / "examples/demo.plan.json"), read_json(ROOT / "config/demo.json")
class ProviderTests(unittest.TestCase):
    def test_command_uses_structured_output_and_readonly_tools(self):
        p,c=fixture();c["claude"]["executable"]="/fake/claude"
        argv=command(c)
        self.assertIn("--json-schema",argv)
        self.assertEqual(argv[argv.index("--tools")+1],"Read,Glob,Grep")
        self.assertNotIn("--dangerously-skip-permissions",argv)
    def test_api_key_missing_refused(self):
        p,c=fixture();c["claude"]["executable"]="/fake/claude";c["claude"]["auth_mode"]="api"
        with patch.dict(os.environ,{},clear=True),self.assertRaises(HarnessError):command(c)
    def test_missing_cli_is_not_fake_success(self):
        p,c=fixture();c["claude"]["executable"]=None
        with patch("ashfall_harness.provider.shutil.which",return_value=None),self.assertRaises(HarnessError):command(c)

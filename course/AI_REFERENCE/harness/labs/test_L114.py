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
from ashfall_harness.provider import run_process
from ashfall_harness.evidence import parse_nunit, parse_unittest

class ProcessTests(unittest.TestCase):
    def test_real_python_process(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            r=run_process([sys.executable,"-c","print('hello')"],root,"",10,root/"o",root/"e")
            self.assertEqual(r["exit_code"],0)
            self.assertEqual((root/"o").read_text().strip(),"hello")
    def test_zero_nunit_is_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.xml";p.write_text('<test-run result="Passed" total="0"/>')
            with self.assertRaises(HarnessError): parse_nunit(p)
    def test_count_and_name_must_match(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.xml";p.write_text('<test-run result="Passed" total="1" passed="1"><test-case fullname="Game.TestA" result="Passed"/></test-run>')
            self.assertEqual(parse_nunit(p,1,["Game.TestA"])["passed"],1)
            with self.assertRaises(HarnessError): parse_nunit(p,1,["Game.NotRun"])
    def test_all_skipped_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/"o").write_text("");(root/"e").write_text("Ran 2 tests in 0.1s\nOK (skipped=2)\n")
            with self.assertRaises(HarnessError): parse_unittest(root/"o",root/"e")

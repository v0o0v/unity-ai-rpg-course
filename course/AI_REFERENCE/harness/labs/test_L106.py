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
from ashfall_harness.common import digest, atomic_json, read_json

class JsonTests(unittest.TestCase):
    def test_key_order_is_not_identity(self):
        self.assertEqual(digest({"a":1,"b":2}), digest({"b":2,"a":1}))
    def test_change_changes_hash(self):
        self.assertNotEqual(digest({"hp":10}), digest({"hp":11}))
    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.json"
            atomic_json(p,{"status":"WAITING","name":"검사"})
            self.assertEqual(read_json(p)["name"],"검사")
    def test_nonfinite_refused(self):
        with self.assertRaises(ValueError): digest({"budget":float("nan")})

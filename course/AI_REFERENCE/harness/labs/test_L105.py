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


class StartTests(unittest.TestCase):
    def test_package_can_be_imported(self):
        import ashfall_harness
        self.assertIsNotNone(ashfall_harness)
    def test_first_cli(self):
        from ashfall_harness.__main__ import main
        with patch("builtins.print") as output:
            self.assertEqual(main(["hello"]), 0)
        self.assertIn("NOT CONNECTED", output.call_args.args[0])

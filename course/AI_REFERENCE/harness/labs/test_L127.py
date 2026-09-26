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
_SPEC=importlib.util.spec_from_file_location("quest_audit",Path(__file__).resolve().parents[1]/"tools/quest_audit.py")
_module=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(_module);audit=_module.audit


class NewDomainTests(unittest.TestCase):
    def test_quest_data_is_actually_checked(self):
        result=audit({"quests":[{"id":"a","reward_key":"r"}]})
        self.assertTrue(all(x["passed"] for x in result["checks"]))
    def test_same_reward_key_fails(self):
        result=audit({"quests":[{"id":"a","reward_key":"r"},{"id":"b","reward_key":"r"}]})
        self.assertFalse(result["checks"][2]["passed"])
    def test_broken_next_fails(self):
        result=audit({"quests":[{"id":"a","next":"missing","reward_key":"r"}]})
        self.assertFalse(result["checks"][1]["passed"])

"""Regressions found by adversarial course review. Not Unity/device evidence."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from ashfall_harness.common import HarnessError,read_json
from ashfall_harness.engine import validate_config,validate_plan,init_run,run_tasks,stage,seal
from ashfall_harness.evidence import parse_nunit,parse_unittest,attest
ROOT=Path(__file__).resolve().parents[1]
class AuditTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.p=Path(self.temp.name)
  self.config=read_json(ROOT/'config/demo.json');self.plan=read_json(ROOT/'examples/demo.plan.json')
 def tearDown(self):self.temp.cleanup()
 def xml(self,text):
  p=self.p/'result.xml';p.write_text(text);return p
 def test_nunit_duplicate_fullname_rejected(self):
  p=self.xml('<test-run result="Passed"><test-case fullname="A" result="Passed"/><test-case fullname="A" result="Passed"/></test-run>')
  with self.assertRaises(HarnessError):parse_nunit(p,2)
 def test_nunit_duplicate_id_rejected(self):
  p=self.xml('<test-run result="Passed"><test-case fullname="A" id="1" result="Passed"/><test-case fullname="B" id="1" result="Passed"/></test-run>')
  with self.assertRaises(HarnessError):parse_nunit(p,2)
 def test_parameter_cases_remain_distinct(self):
  p=self.xml('<test-run result="Passed"><test-case fullname="A(1)" id="1" result="Passed"/><test-case fullname="A(2)" id="2" result="Passed"/></test-run>')
  self.assertEqual(parse_nunit(p,2)['passed'],2)
 def test_minimum_parser_validation(self):
  p=self.xml('<test-run result="Passed"/>')
  for n in (0,-1,True,1.5,'2'):
   with self.subTest(n=n),self.assertRaises(HarnessError):parse_nunit(p,n)
 def test_minimum_config_validation(self):
  for n in (0,-1,True,1.5,'2'):
   c=copy.deepcopy(self.config);c['gates']['demo_rules']['minimum_tests']=n
   with self.subTest(n=n),self.assertRaises(HarnessError):validate_config(c)
 def test_required_names_validation(self):
  for names in (['A','A'],[' '],'A',[42]):
   c=copy.deepcopy(self.config);c['gates']['demo_rules']['required_test_names']=names
   with self.subTest(names=names),self.assertRaises(HarnessError):validate_config(c)
 def test_timeout_and_boolean_validation(self):
  for name,value in [('timeout_seconds',0),('timeout_seconds',float('nan')),('enabled','true'),('required',1)]:
   c=copy.deepcopy(self.config);c['gates']['demo_rules'][name]=value
   with self.subTest(name=name,value=value),self.assertRaises(HarnessError):validate_config(c)
 def test_blank_acceptance_rejected(self):
  self.plan['tasks'][0]['acceptance']=[' ']
  with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
 def test_instruction_must_be_text(self):
  self.plan['tasks'][0]['instruction']={'say':'yes'}
  with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
 def unit(self,a,b):
  o=self.p/'stdout';e=self.p/'stderr';o.write_text(a);e.write_text(b);return o,e
 def test_unittest_conflicting_streams(self):
  args=self.unit('Ran 1 test in 0.1s\n\nOK\n','Ran 2 tests in 0.1s\n\nFAILED (failures=1)\n')
  with self.assertRaises(HarnessError):parse_unittest(*args)
 def test_unittest_double_success_ambiguous(self):
  args=self.unit('Ran 1 test in 0.1s\n\nOK\n','Ran 1 test in 0.1s\n\nOK\n')
  with self.assertRaises(HarnessError):parse_unittest(*args)
 def test_unittest_skip_counts(self):
  args=self.unit('test log\n','Ran 3 tests in 0.1s\n\nOK (skipped=1)\n')
  self.assertEqual(parse_unittest(*args,2)['passed'],2)
 def test_unittest_all_skipped_rejected(self):
  args=self.unit('','Ran 3 tests in 0.1s\n\nOK (skipped=3)\n')
  with self.assertRaises(HarnessError):parse_unittest(*args)
 def test_unittest_trailing_fail_not_ignored(self):
  args=self.unit('','Ran 3 tests in 0.1s\n\nOK\nFAILED\n')
  with self.assertRaises(HarnessError):parse_unittest(*args)
 def test_disabled_manual_gate_rejected(self):
  self.config['gates']['human']={'kind':'manual','enabled':False,'required':False}
  src=self.p/'src';shutil.copytree(ROOT/'examples/demo_project',src);run=self.p/'run'
  init_run(src,run,self.plan,self.config,'mock');r=run_tasks(run);stage(run,self.p/'candidate',r['candidate_sha256']);seal(run,'test')
  ev=self.p/'observation.txt';ev.write_text('synthetic regression fixture, not real play')
  with self.assertRaises(HarnessError):attest(run,'human',ev,'test','test',True,True)
if __name__=='__main__':unittest.main()

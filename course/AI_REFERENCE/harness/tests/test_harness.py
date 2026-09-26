from __future__ import annotations
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ashfall_harness.common import HarnessError, FileLock, atomic_json, digest, read_json, safe_relative, scan, sha_bytes
from ashfall_harness.engine import init_run, run_tasks, stage, seal, status, dashboard, validate_plan, validate_config, validate_response
from ashfall_harness.evidence import run_gate, parse_nunit, attest, integrate
from ashfall_harness.provider import run_process

ROOT=Path(__file__).resolve().parents[1]

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
        self.source=self.base/'source';shutil.copytree(ROOT/'examples/demo_project',self.source)
        self.run=self.base/'run';self.dest=self.base/'candidate'
        self.config=read_json(ROOT/'config/demo.json');self.plan=read_json(ROOT/'examples/demo.plan.json')
    def tearDown(self):self.tmp.cleanup()
    def init(self,provider='mock'):
        return init_run(self.source,self.run,self.plan,self.config,provider)
    def complete(self):
        self.init();return run_tasks(self.run)
    def staged(self):
        result=self.complete();stage(self.run,self.dest,result['candidate_sha256']);return result
    def sealed(self):
        self.staged();return seal(self.run,'테스트용 새 후보를 검토함')
    def test_valid_plan(self):self.assertEqual(len(validate_plan(self.plan,self.config)),4)
    def test_cycle_rejected(self):
        self.plan['tasks'][0]['depends_on']=['review']
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_missing_dependency(self):
        self.plan['tasks'][1]['depends_on']=['missing']
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_duplicate_task_id(self):
        self.plan['tasks'][1]['id']='design'
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_unordered_write_conflict(self):
        extra=copy.deepcopy(self.plan['tasks'][1]);extra['id']='parallel';extra['depends_on']=['design']
        self.plan['tasks'].insert(2,extra);self.plan['tasks'][-1]['depends_on'].append('parallel')
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_undefined_role(self):
        self.plan['tasks'][0]['role']='allpowerful'
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_self_review(self):
        self.plan['tasks'][-1]['role']='gameplay_engineer'
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_review_write_forbidden(self):
        self.plan['tasks'][-1]['write_prefixes']=['Game']
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_acceptance_required(self):
        self.plan['tasks'][0]['acceptance']=[]
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_required_gate(self):
        self.config['gates']={}
        with self.assertRaises(HarnessError):validate_config(self.config)
    def test_nonfinite_budget(self):
        self.config['claude']['run_budget_usd']=float('nan')
        with self.assertRaises(HarnessError):validate_config(self.config)
    def test_invalid_paths(self):
        for path in ['../escape','/absolute','a/../b','C:/x','a\\b','a//b','a./b','a/NUL.txt','a/x:ads','a/*/x']:
            with self.subTest(path=path),self.assertRaises(HarnessError):safe_relative(path)
    def test_valid_unicode_path(self):self.assertEqual(safe_relative('Docs/기획.md'),'Docs/기획.md')
    def test_source_secret_name(self):
        (self.source/'Docs/.env').write_text('SECRET=not-a-real-key')
        with self.assertRaises(HarnessError):self.init()
    @unittest.skipIf(os.name=='nt','symlink permission varies on Windows')
    def test_source_symlink(self):
        (self.source/'Game/link').symlink_to(self.source/'Docs',target_is_directory=True)
        with self.assertRaises(HarnessError):self.init()
    def test_source_case_collision(self):
        if os.name=='nt':self.skipTest('case-insensitive filesystem')
        (self.source/'Game/RULES.py').write_text('x=1')
        with self.assertRaises(HarnessError):self.init()
    def test_run_outside_source(self):
        with self.assertRaises(HarnessError):init_run(self.source,self.source/'run',self.plan,self.config,'mock')
    def test_never_overwrite_existing_run(self):
        self.init()
        with self.assertRaises(HarnessError):self.init()
    def test_mock_success_is_not_game_pass(self):
        r=self.complete();self.assertEqual(r['status'],'PROPOSALS_REVIEWED');self.assertEqual(status(self.run)['release_status'],'DEMO_ONLY')
    def test_resume_skips_completed_tasks(self):
        self.complete();a=read_json(self.run/'state.json');run_tasks(self.run);b=read_json(self.run/'state.json')
        self.assertEqual(a,b)
    def test_original_unchanged(self):
        before=scan(self.source,self.config['source_roots']);self.sealed();run_gate(self.run,'demo_rules',True)
        self.assertEqual(before,scan(self.source,self.config['source_roots']))
    def test_external_source_change_stops_run(self):
        self.init();(self.source/'Game/rules.py').write_text('changed')
        with self.assertRaises(HarnessError):run_tasks(self.run)
    def test_config_change_stops_run(self):
        self.init();config=read_json(self.run/'config.json');config['max_attempts_per_task']=5;atomic_json(self.run/'config.json',config)
        with self.assertRaises(HarnessError):run_tasks(self.run)
    def test_stage_requires_exact_candidate(self):
        self.complete()
        with self.assertRaises(HarnessError):stage(self.run,self.dest,'wrong')
    def test_stage_cannot_overwrite_original(self):
        r=self.complete()
        with self.assertRaises(HarnessError):stage(self.run,self.source,r['candidate_sha256'])
    def test_stage_cannot_be_inside_run(self):
        r=self.complete()
        with self.assertRaises(HarnessError):stage(self.run,self.run/'bad',r['candidate_sha256'])
    def test_staged_run_cannot_resume(self):
        self.staged()
        with self.assertRaises(HarnessError):run_tasks(self.run)
    def test_gate_must_be_explicit(self):
        self.sealed()
        with self.assertRaises(HarnessError):run_gate(self.run,'demo_rules',False)
    def test_real_python_gate_executes(self):
        self.sealed();r=run_gate(self.run,'demo_rules',True)
        self.assertEqual(r['status'],'PASS',r);self.assertEqual(r['counts']['passed'],5)
    def test_changed_stage_invalidates_evidence(self):
        self.sealed();run_gate(self.run,'demo_rules',True)
        (self.dest/'Game/rules.py').write_text('changed')
        self.assertEqual(status(self.run)['gates']['demo_rules']['status'],'STALE')
        with self.assertRaises(HarnessError):run_gate(self.run,'demo_rules',True)
    def test_reseal_invalidates_even_same_hash(self):
        self.sealed();run_gate(self.run,'demo_rules',True);seal(self.run,'새 검토 주기')
        self.assertEqual(status(self.run)['gates']['demo_rules']['status'],'STALE')
    def test_modified_evidence_invalidates_pass(self):
        self.sealed();r=run_gate(self.run,'demo_rules',True)
        artifact=self.run/r['artifacts'][0]['path'];artifact.write_text('tampered')
        self.assertEqual(status(self.run)['gates']['demo_rules']['status'],'STALE')
    def test_lock_exclusion(self):
        path=self.base/'test.lock'
        with FileLock(path,'test'):
            with self.assertRaises(HarnessError):
                with FileLock(path,'test'):pass
        self.assertFalse(path.exists())
    def test_no_automatic_lock_expiry(self):
        path=self.base/'old.lock';atomic_json(path,{'token':'old','pid':123,'created':0})
        with self.assertRaises(HarnessError):
            with FileLock(path,'test'):pass
        self.assertTrue(path.exists())
    def test_input_digest_checked(self):
        task=self.plan['tasks'][1];value={'task_id':'implement','input_sha256':'wrong','outcome':'proposal','summary':'x','files':[],'findings':[]}
        with self.assertRaises(HarnessError):validate_response(value,task,'right',{},self.config)
    def test_write_scope_checked(self):
        task=self.plan['tasks'][1];value={'task_id':'implement','input_sha256':'h','outcome':'proposal','summary':'x','files':[{'path':'Tests/test_cheat.py','expected_sha256':None,'content':'pass'}],'findings':[]}
        with self.assertRaises(HarnessError):validate_response(value,task,'h',{},self.config)
    def test_old_file_digest_checked(self):
        task=self.plan['tasks'][1];value={'task_id':'implement','input_sha256':'h','outcome':'proposal','summary':'x','files':[{'path':'Game/rules.py','expected_sha256':'old','content':'pass'}],'findings':[]}
        with self.assertRaises(HarnessError):validate_response(value,task,'h',{'Game/rules.py':'new'},self.config)
    def test_unity_yaml_not_applied(self):
        task=copy.deepcopy(self.plan['tasks'][1]);task['write_prefixes']=['Game']
        value={'task_id':'implement','input_sha256':'h','outcome':'proposal','summary':'x','files':[{'path':'Game/x.prefab','expected_sha256':None,'content':'yaml'}],'findings':[]}
        with self.assertRaises(HarnessError):validate_response(value,task,'h',{},self.config)
    def test_reviewer_finding_blocks_pass(self):
        self.plan['tasks'][-1]['mock_response']['findings']=['실패 반례']
        result=self.complete();self.assertEqual(result['tasks']['review'],'FAILED')
    def test_rejected_review_prevents_stage(self):
        self.plan['tasks'][-1]['mock_response']['outcome']='review_fail';result=self.complete()
        self.assertEqual(result['tasks']['review'],'REVIEW_FAILED')
        with self.assertRaises(HarnessError):stage(self.run,self.dest,result['candidate_sha256'])
    def test_paid_calls_need_optin(self):
        self.init('claude')
        with self.assertRaises(HarnessError):run_tasks(self.run)
    def test_unknown_cost_blocks_retry(self):
        self.init('claude')
        with patch('ashfall_harness.engine.invoke',side_effect=HarnessError('network stopped')):run_tasks(self.run,allow_paid=True)
        self.assertTrue(read_json(self.run/'run.json')['budget_unknown'])
        with self.assertRaises(HarnessError):run_tasks(self.run,allow_paid=True,retry_task='design')
    def test_timeout_kills_owned_process(self):
        info=run_process([sys.executable,'-c','import time; time.sleep(30)'],self.base,'',0.1,self.base/'o',self.base/'e')
        self.assertTrue(info['timed_out']);self.assertNotEqual(info['exit_code'],0)
    def test_unbound_template_rejected(self):
        self.plan['binding_required']=True
        with self.assertRaises(HarnessError):validate_plan(self.plan,self.config)
    def test_integrate_disabled(self):
        self.config['integration_commands']={'prepare':{'enabled':False,'argv':[]}}
        self.staged()
        with self.assertRaises(HarnessError):integrate(self.run,'prepare',True)
    def test_integrate_requires_optin(self):
        self.staged()
        with self.assertRaises(HarnessError):integrate(self.run,'prepare',False)
    def test_integration_runs_but_is_not_game_success(self):
        self.config['integration_commands']={'prepare':{'enabled':True,'argv':['{python}','-B','-c','print("prepared")']}}
        self.sealed();run_gate(self.run,'demo_rules',True)
        report=integrate(self.run,'prepare',True)
        self.assertEqual(report['status'],'EXECUTED_NOT_VERIFIED')
        self.assertNotIn('seal_sha256',read_json(self.run/'run.json'))
        self.assertEqual(status(self.run)['gates']['demo_rules']['status'],'STALE')
    def test_failed_integration_still_invalidates_seal(self):
        self.config['integration_commands']={'prepare':{'enabled':True,'argv':['{python}','-B','-c','raise SystemExit(3)']}}
        self.sealed();report=integrate(self.run,'prepare',True)
        self.assertEqual(report['status'],'FAILED');self.assertNotIn('seal_id',read_json(self.run/'run.json'))
    def test_integration_original_preserved(self):
        self.config['integration_commands']={'prepare':{'enabled':True,'argv':['{python}','-B','-c','from pathlib import Path; Path("Docs/imported.txt").write_text("new")']}}
        self.staged();integrate(self.run,'prepare',True)
        self.assertTrue((self.dest/'Docs/imported.txt').exists());self.assertFalse((self.source/'Docs/imported.txt').exists())
    def test_file_directory_collision_rejected(self):
        task=self.plan['tasks'][1];value={'task_id':'implement','input_sha256':'h','outcome':'proposal','summary':'x','files':[{'path':'Game/rules.py/child.py','expected_sha256':None,'content':'pass'}],'findings':[]}
        with self.assertRaises(HarnessError):validate_response(value,task,'h',{'Game/rules.py':'abc'},self.config)
    def xml(self,text):
        p=self.base/'results.xml';p.write_text(text);return p
    def test_nunit_pass_and_names(self):
        p=self.xml('<test-run result="Passed"><test-case fullname="A" result="Passed"/></test-run>')
        self.assertEqual(parse_nunit(p,1,['A'])['passed'],1)
    def test_nunit_count_mismatch(self):
        with self.assertRaises(HarnessError):parse_nunit(self.xml('<test-run result="Passed" total="8"><test-case fullname="A" result="Passed"/></test-run>'))
    def test_nunit_missing_test_name(self):
        with self.assertRaises(HarnessError):parse_nunit(self.xml('<test-run result="Passed"><test-case result="Passed"/></test-run>'))
    def test_nunit_zero_rejected(self):
        with self.assertRaises(HarnessError):parse_nunit(self.xml('<test-run result="Passed"/>'))
    def test_nunit_skipped_rejected(self):
        with self.assertRaises(HarnessError):parse_nunit(self.xml('<test-run result="Passed"><test-case result="Skipped"/></test-run>'))
    def test_nunit_failure_despite_root_pass(self):
        with self.assertRaises(HarnessError):parse_nunit(self.xml('<test-run result="Passed"><test-case result="Failed"/></test-run>'))
    def test_nunit_wrong_required_test(self):
        with self.assertRaises(HarnessError):parse_nunit(self.xml('<test-run result="Passed"><test-case fullname="B" result="Passed"/></test-run>'),1,['A'])
    def test_nunit_missing_xml(self):
        with self.assertRaises(HarnessError):parse_nunit(self.base/'missing.xml')
    def test_nunit_entity_rejected(self):
        with self.assertRaises(HarnessError):parse_nunit(self.xml('<!DOCTYPE x><test-run result="Passed"/>'))
    def test_human_cannot_override_automated_gate(self):
        self.sealed();p=self.base/'observation.txt';p.write_text('I tried')
        with self.assertRaises(HarnessError):attest(self.run,'demo_rules',p,'I tried','learner',True,True)
    def test_manual_evidence_labelled(self):
        self.config['gates']['mobile']={'kind':'manual','required':True,'enabled':True};self.sealed()
        p=self.base/'observation.txt';p.write_text('not real mobile: unit test fixture')
        r=attest(self.run,'mobile',p,'unit test fixture','test',True,True)
        self.assertEqual(r['basis'],'human_attestation_NOT_machine_verified')
    def test_dashboard_escapes_html(self):
        self.complete();s=read_json(self.run/'state.json');s['design']['error']='<script>alert(1)</script>';atomic_json(self.run/'state.json',s)
        text=dashboard(self.run).read_text();self.assertNotIn('<script>',text);self.assertIn('&lt;script&gt;',text)

if __name__=='__main__':unittest.main()

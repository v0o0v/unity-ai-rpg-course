from __future__ import annotations
import copy
import os
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

E=Path(__file__).resolve().parents[1]
ROOT=E.parent
H=Path(os.environ['ASHFALL_HARNESS_ROOT']).resolve()
sys.path.insert(0,str(H))
spec=importlib.util.spec_from_file_location('workbook',H/'expansion2d/tools/workbook.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
from ashfall_harness.common import HarnessError, read_json, sha_bytes, scan, digest
from ashfall_harness.engine import init_run, run_tasks, stage, seal, status

class WorkbookTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.project=self.root/'source'
        self.project.mkdir()
        # File fixture ONLY; not a playable/compiled Unity project.
        for rel,text in {'Packages/manifest.json':'{}','ProjectSettings/ProjectVersion.txt':'m_EditorVersion: teaching_fixture',
            'Docs/GAME_SPEC.md':'# Game Spec\nQuest and materials always visible.\n',
            'Assets/_Game/Scripts/Core/LootModel.cs':'// fixture only\nclass LootModel {}\n'}.items():
            f=self.project/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,encoding='utf-8')
        self.config=read_json(H/'config/unity.template.json')
        self.recipe=read_json(E/'recipes/E01.loot-filter.recipe.json')
        self.binding=read_json(E/'bindings/E01.example.json')
        self.binding.update(status='REVIEWED',reviewed_by='automated fixture test, not a game review')
        self.binding['inputs']={'game_spec':{'path':'Docs/GAME_SPEC.md','anchor':'Game Spec','reason':'test fixture'},
            'loot_model':{'path':'Assets/_Game/Scripts/Core/LootModel.cs','anchor':'class LootModel','reason':'test fixture'}}
    def tearDown(self): self.temp.cleanup()
    def bind(self,approved=True):
        return w.bind(self.project,self.binding,self.recipe,self.config,self.root/'bound',approved)
    def test_valid_binding_no_game_writes(self):
        before=scan(self.project,self.config['source_roots']); r=self.bind()
        self.assertEqual(r['status'],'BOUND_NOT_RUN');self.assertEqual(before,scan(self.project,self.config['source_roots']))
    def test_verify_unchanged(self):
        self.bind(); self.assertEqual(w.verify(self.project,read_json(self.root/'bound/binding.lock.json'))['status'],'BINDING_UNCHANGED')
    def test_refuses_no_confirmation(self):
        with self.assertRaises(HarnessError):self.bind(False)
    def test_refuses_unreviewed(self):
        self.binding['status']='UNREVIEWED'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_3d(self):
        self.binding['mode']='3D'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_missing_input(self):
        self.binding['inputs']['loot_model']['path']='Assets/missing.cs'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_wrong_anchor(self):
        self.binding['inputs']['loot_model']['anchor']='absent'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_parent_path(self):
        self.binding['outputs']['out_gameplay_engineer']='../escape.cs'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_binary_output(self):
        self.binding['outputs']['out_gameplay_engineer']='Assets/_Game/Scripts/Core/icon.png'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_protected_output(self):
        self.binding['outputs']['out_gameplay_engineer']='Packages/manifest.json'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_role_scope_escalation(self):
        self.binding['outputs']['out_gameplay_engineer']='Assets/_Game/Tests/EditMode/Wrong.cs'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_existing_output_not_read(self):
        p=self.project/self.binding['outputs']['out_gameplay_engineer'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text('exists')
        with self.assertRaises(HarnessError):self.bind()
    def test_existing_output_also_input_allowed(self):
        self.binding['outputs']['out_gameplay_engineer']=self.binding['inputs']['loot_model']['path']
        self.assertEqual(self.bind()['status'],'BOUND_NOT_RUN')
    def test_refuses_missing_dependency(self):
        self.recipe['plan']['tasks'][1]['depends_on']=[]
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_critic_missing_output(self):
        self.recipe['plan']['tasks'][-1]['read_files'].pop()
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_alias_mismatch(self):
        self.binding['inputs']['extra']={'path':'Docs/GAME_SPEC.md','anchor':'Game Spec','reason':'test'}
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_same_alias_in_both(self):
        self.binding['outputs']['loot_model']='Assets/X.cs'
        with self.assertRaises(HarnessError):self.bind()
    def test_refuses_output_in_source(self):
        with self.assertRaises(HarnessError):w.bind(self.project,self.binding,self.recipe,self.config,self.project/'bad',True)
    def test_refuses_overwrite_bound(self):
        self.bind()
        with self.assertRaises(HarnessError):self.bind()
    def test_detects_source_changed(self):
        self.bind(); (self.project/'Docs/GAME_SPEC.md').write_text('changed')
        with self.assertRaises(HarnessError):w.verify(self.project,read_json(self.root/'bound/binding.lock.json'))
    def test_detects_new_output_appeared(self):
        self.bind();p=self.project/self.binding['outputs']['out_gameplay_engineer'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text('late file')
        with self.assertRaises(HarnessError):w.verify(self.project,read_json(self.root/'bound/binding.lock.json'))
    def test_detects_plan_changed(self):
        self.bind();plan=read_json(self.root/'bound/plan.json');plan['title']='changed'
        with self.assertRaises(HarnessError):w.verify(self.project,read_json(self.root/'bound/binding.lock.json'),plan)
    def test_detects_config_changed(self):
        self.bind();config=copy.deepcopy(self.config);config['max_attempts_per_task']=1
        with self.assertRaises(HarnessError):w.verify(self.project,read_json(self.root/'bound/binding.lock.json'),config=config)
    def test_disabled_gates_stay_visible(self):
        self.assertIn('editmode',self.bind()['disabled_required_gates'])
    def test_inventory_does_not_claim_2d_execution(self):
        r=w.inspect(self.project,self.root/'inventory.json');self.assertEqual(r['status'],'INVENTORY_ONLY_NOT_SEMANTICALLY_BOUND')
    def test_inventory_missing_project(self):
        (self.project/'Packages/manifest.json').unlink()
        with self.assertRaises(HarnessError):w.inspect(self.project,self.root/'inventory.json')
    def test_rejects_symlink(self):
        external=self.root/'outside.cs';external.write_text('class LootModel {}')
        original=self.project/'Assets/_Game/Scripts/Core/LootModel.cs'; original.unlink();original.symlink_to(external)
        with self.assertRaises(HarnessError):self.bind()
    def test_rejects_case_alias(self):
        self.binding['outputs']['out_gameplay_engineer']='Assets/_Game/Scripts/Core/lootmodel.cs'
        with self.assertRaises(HarnessError):self.bind()
    def test_rejects_review_write(self):
        self.recipe['plan']['tasks'][-1]['write_prefixes']=['@out_gameplay_engineer']
        with self.assertRaises(HarnessError):self.bind()
    def test_no_mock_success_becomes_unity_pass(self):
        self.bind();plan=read_json(self.root/'bound/plan.json')
        for t in plan['tasks']:
            files=[]
            for rel in t.get('outputs',[]):
                if t['role']=='gameplay_engineer': content=(E/'reference_code/LootFilterPolicy.cs').read_text()
                elif t['role']=='qa_engineer':content=(E/'reference_code/LootFilterPolicyTests.cs').read_text()
                else: content='# MOCK fixture contract\nQuest and materials visible.\n'
                files.append({'path':rel,'expected_sha256':'$CURRENT','content':content})
            t['mock_response']={'outcome':'review_pass' if t['kind']=='review' else 'proposal',
                'summary':'MOCK fixture, not AI review or Unity compilation','files':files,'findings':[]}
        run=self.root/'run';init_run(self.project,run,plan,self.config,'mock')
        result=run_tasks(run);self.assertEqual(result['status'],'PROPOSALS_REVIEWED')
        stage(run,self.root/'candidate',result['candidate_sha256']); seal(run,'fixture only, no Unity launch')
        s=status(run);self.assertEqual(s['release_status'],'DEMO_ONLY');self.assertEqual(s['gates']['editmode']['status'],'NOT RUN')
        # Real source change invalidates old seal; still never means a game passed.
        f=self.root/'candidate'/self.binding['outputs']['out_gameplay_engineer'];f.write_text(f.read_text()+'\n// changed\n')
        self.assertNotEqual(digest(scan(self.root/'candidate',self.config['source_roots'])),s['seal_sha256'])
        report=w.campaign([run],self.root/'campaign.json')
        self.assertEqual(report['status'],'HISTORY_ONLY_FINAL_INTEGRATION_REQUIRED')
    def test_campaign_missing_run_blocked(self):
        r=w.campaign([self.root/'missing'],self.root/'campaign.json'); self.assertEqual(r['runs'][0]['release_status'],'BLOCKED')
    def test_all_recipes_bind_with_real_file_fixtures(self):
        for entry in read_json(E/'recipes/index.json'):
            with self.subTest(lesson=entry['lesson']):
                recipe=read_json(E/entry['recipe']);binding=read_json(E/entry['binding'])
                binding.update(status='REVIEWED',reviewed_by='fixture only')
                for alias in recipe['input_aliases']:
                    path=f'Docs/Fixture_{entry["lesson"]}_{alias}.md';p=self.project/path;p.write_text(f'# {alias}\nfixture not implementation')
                    binding['inputs'][alias]={'path':path,'anchor':alias,'reason':'structural binding test only'}
                r=w.bind(self.project,binding,recipe,self.config,self.root/f'bound{entry["lesson"]}',True)
                self.assertEqual(r['status'],'BOUND_NOT_RUN')

if __name__=='__main__':unittest.main()

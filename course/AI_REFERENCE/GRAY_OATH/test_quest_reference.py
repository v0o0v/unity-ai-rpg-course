import unittest,json
from pathlib import Path
from copy import deepcopy
from quest_reference import validate_draft,preview_apply,ContractError,RewardState,reward_transaction
D=json.loads(Path(__file__).with_name('quest_draft_example.json').read_text())
R=D['declaredRefs']
class QuestReferenceTests(unittest.TestCase):
 def setUp(self):self.d=deepcopy(D)
 def valid(self):return validate_draft(self.d,R)
 def bad(self):
  with self.assertRaises(ContractError):self.valid()
 def test_valid_structure_not_gameplay(self):
  r=self.valid();self.assertEqual(r,{'nodes':14,'edges':16,'structural':'VALID','gameplay':'NOT RUN'})
 def test_input_unchanged(self):self.valid();self.assertEqual(self.d,D)
 def test_schema_bool(self):self.d['schemaVersion']=True;self.bad()
 def test_schema_future(self):self.d['schemaVersion']=2;self.bad()
 def test_wrong_project(self):self.d['projectId']='AshfallRPG2D';self.bad()
 def test_wrong_quest(self):self.d['questId']='M01';self.bad()
 def test_unknown_top_key(self):self.d['shell']='delete';self.bad()
 def test_bad_request_id(self):self.d['requestId']='../../file';self.bad()
 def test_blank_title(self):self.d['title']=' ';self.bad()
 def test_missing_content(self):self.d['needsContent']=['npc_missing'];self.bad()
 def test_limit_zero(self):
  with self.assertRaises(ContractError):validate_draft(self.d,R,node_limit=0)
 def test_duplicate_nodes(self):self.d['nodes'][1]['id']='start';self.bad()
 def test_missing_start(self):self.d['startNode']='missing';self.bad()
 def test_unsupported_node(self):self.d['nodes'][1]['type']='RunCode';self.bad()
 def test_unknown_node_key(self):self.d['nodes'][1]['shell']='bad';self.bad()
 def test_unknown_npc(self):self.d['nodes'][1]['data']['npc']='npc_unknown';self.bad()
 def test_missing_declared_ref(self):self.d['declaredRefs']['npc'].remove('npc_nara');self.bad()
 def test_fake_declared_ref(self):self.d['declaredRefs']['npc'].append('npc_unknown');self.bad()
 def test_duplicate_declared(self):self.d['declaredRefs']['npc'].append('npc_nara');self.bad()
 def test_wrong_edge(self):self.d['edges'][0]['to']='missing';self.bad()
 def test_invalid_edge_type(self):self.d['edges'][0]['to']={};self.bad()
 def test_wrong_port(self):self.d['edges'][0]['port']='invented';self.bad()
 def test_duplicate_port_edge(self):self.d['edges'].append(deepcopy(self.d['edges'][0]));self.bad()
 def test_missing_port(self):self.d['edges'].pop(5);self.bad()
 def test_cycle(self):self.d['edges'][-1]['to']='truth';self.bad()
 def test_unreachable_extra_node(self):self.d['nodes'].append({'id':'lonely','type':'End','data':{'result':'Completed'}});self.bad()
 def test_end_with_edges(self):self.d['edges'].append({'from':'end','port':'next','to':'start'});self.bad()
 def test_unknown_predicate(self):self.d['nodes'][4]['data']['predicate']={'op':'RunShell','id':'x'};self.bad()
 def test_unknown_action(self):self.d['nodes'][6]['data']['actions']=[{'op':'DeleteFile','id':'asset'}];self.bad()
 def test_negative_reward(self):self.d['nodes'][-2]['data']['gold']=-1;self.bad()
 def test_oversized_reward(self):self.d['nodes'][-2]['data']['gold']=999999;self.bad()
 def test_false_count(self):self.d['nodes'][2]['data']['objectives'][0]['count']=False;self.bad()
 def test_unknown_objective(self):self.d['nodes'][2]['data']['objectives'][0]['kind']='ExecuteCode';self.bad()
 def test_retrokill_without_proof(self):del self.d['nodes'][7]['data']['objectives'][0]['proofFact'];self.bad()
 def test_nested_depth(self):
  p={'op':'HasFact','id':'fact_truth_public','value':True}
  for _ in range(8):p={'op':'Not','arg':p}
  self.d['nodes'][4]['data']['predicate']=p;self.bad()
 def test_duplicate_choice(self):self.d['nodes'][3]['data']['options']=['repair','repair'];self.bad()
 def test_reward_scope(self):self.d['nodes'][-2]['data']['gold']=90;self.bad()
 def test_hidden_xp(self):self.d['nodes'][6]['data']['actions'].append({'op':'GrantXP','amount':10});self.bad()
 def test_valid_apply_copy(self):
  out=preview_apply(self.d,R,current_revision=0,approved_request='quest-demo-001',cancelled=False,applied_requests=set())
  self.assertEqual(out['revision'],1);self.assertEqual(self.d,D)
 def test_stale_apply(self):
  with self.assertRaises(ContractError):preview_apply(self.d,R,current_revision=1,approved_request='quest-demo-001',cancelled=False,applied_requests=set())
 def test_cancelled_apply(self):
  with self.assertRaises(ContractError):preview_apply(self.d,R,current_revision=0,approved_request='quest-demo-001',cancelled=True,applied_requests=set())
 def test_missing_approval(self):
  with self.assertRaises(ContractError):preview_apply(self.d,R,current_revision=0,approved_request=None,cancelled=False,applied_requests=set())
 def test_repeated_apply(self):
  with self.assertRaises(ContractError):preview_apply(self.d,R,current_revision=0,approved_request='quest-demo-001',cancelled=False,applied_requests={'quest-demo-001'})
 def test_reward_once(self):
  a=RewardState();b=reward_transaction(a,'instance1','H01.completion',80,120);c=reward_transaction(b,'instance1','H01.completion',80,120)
  self.assertEqual((a.gold,a.xp),(0,0));self.assertEqual((b.gold,b.xp),(80,120));self.assertEqual(b,c)
 def test_reward_new_instance(self):
  a=reward_transaction(RewardState(),'instance1','H01.completion',80,120);b=reward_transaction(a,'instance2','H01.completion',80,120);self.assertEqual((b.gold,b.xp),(160,240))
 def test_reward_ineligible(self):
  a=RewardState()
  with self.assertRaises(ContractError):reward_transaction(a,'instance1','H01.completion',80,120,eligible=False)
  self.assertEqual(a.gold,0)
if __name__=='__main__':unittest.main()

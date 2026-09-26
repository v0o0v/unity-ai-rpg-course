from pathlib import Path
import json, re, hashlib, unittest, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[2];W=R;OLD=R
M={'courseData_v13.json':R/'data/lessons.json','termData_v13.json':R/'data/terms.json','promptGuideData_v13.json':R/'data/prompt_guides_v13.json','courseData.json':R/'review/baseline_data/courseData.json','promptGuideData.json':R/'review/baseline_data/promptGuideData.json','termData.json':R/'review/baseline_data/termData.json','sourceData.json':R/'data/sources.json'}
J=lambda p:json.loads(M.get(p.name,p).read_text())
L=J(W/'courseData_v13.json');OL=J(W/'courseData.json');T=J(W/'termData_v13.json');G=J(W/'promptGuideData_v13.json');OG=J(W/'promptGuideData.json')
html=(R/'index.html').read_text();soup=BeautifulSoup(html,'html.parser')
# Browser script constants have static literal inputs for the three home-only prompts.
start={}
for key,entries in G.items():
 if not key.startswith(('L','T:')):start[key]=entries
P={};OP={}
for dest,src in [(P,L),(OP,OL)]:
 for l in src:
  for i,s in enumerate(l['steps'],1):dest[f'L{l["id"]}:S{i}']=s['prompt']
  for k in ['repair','resume']:dest[f'L{l["id"]}:{k}']=l[k]
for t in T:P['T:'+t['id']]=t['prompt']
class CourseContractTests(unittest.TestCase):
 def test_01_unique_ordered_lessons(self):self.assertEqual([x['id'] for x in L],list(range(1,257)))
 def test_02_glossary_331_preserved(self):self.assertEqual(T,J(W/'termData.json'));self.assertEqual(len({t['id'] for t in T}),331)
 def test_03_four_steps_complete(self):
  for l in L:
   self.assertEqual(len(l['steps']),4)
   for s in l['steps']:
    for k in ['title','prompt','expected','instruction']:self.assertTrue(s[k].strip(),(l['id'],k))
    self.assertGreater(len(s['actions']),0)
 def test_04_no_classroom_contracts_in_work_prompts(self):
  for k,t in P.items():self.assertIsNone(re.search(r'강의|교재|수강생|책의',t),k)
 def test_05_new_prompt_spans_exact_order_coverage(self):
  for k,txt in P.items():
   prev=0;parts=[]
   for e in G[k]:
    self.assertGreaterEqual(e['a'],prev,k);self.assertGreater(e['b'],e['a'],k);self.assertLessEqual(e['b'],len(txt),k)
    self.assertTrue(e['label'].strip() and e['why'].strip(),k);parts.append(txt[e['a']:e['b']]);prev=e['b']
   self.assertEqual(re.sub(r'\s','',''.join(parts)),re.sub(r'\s','',txt),k)
 def test_06_changed_prompt_allowlist(self):
  changes={k for k in OP if OP[k]!=P[k]};self.assertEqual(len(changes),13)
  self.assertEqual({int(re.search(r'L(\d+)',k)[1]) for k in changes},{27,88,94,121,125,129,130,136,141,185,192,240})
 def test_07_individual_message_exports(self):
  for l in L:
   n=l['id']
   for i,s in enumerate(l['steps'],1):
    path=R/'messages'/f'{n:03}-{i}.txt' if n<=160 else R/'messages'/f'{n:03}'/f'step{i}.txt'
    self.assertEqual(path.read_text(),s['prompt']+'\n',str(path))
   for k in ['repair','resume']:self.assertEqual((R/'messages'/f'{n:03}'/(k+'.txt')).read_text(),l[k]+'\n')
 def test_08_no_missing_fake_recipe(self):self.assertFalse(any('E01.loot-filter.recipe.json' in x for x in P.values()))
 def test_09_role_registration_precedes_use(self):
  self.assertIn('unity_integrator',L[120]['steps'][1]['prompt']);self.assertIn('등록',L[120]['steps'][1]['prompt']);self.assertIn('등록·검증',L[124]['prerequisite'])
 def test_10_pickup_before_filter(self):
  p=L[124]['steps'][2]['prompt'];self.assertNotIn('숨긴 이름표',p);self.assertIn('고유 ID가 가방',p);self.assertIn('다음 기능',L[124]['concept'])
 def test_11_no_premature_slot_ui(self):
  self.assertIn('다중 저장 슬롯 UI를 만들었다고 가정하지 마',P['L185:S2']);self.assertIn('테스트 진행 A/B',P['L185:S3'])
 def test_12_floor_not_wall(self):self.assertIn('walkable 셀은 메시 바닥으로, 차단 셀과 그 경계는 벽 Collider',P['L94:S2'])
 def test_13_baseline_readonly_before_implementation(self):self.assertIn('구현 역할 실행·변경안 적용·Unity 통합을 시작하지 마',P['L129:S2']);self.assertNotIn('stage',P['L129:S2'])
 def test_14_current_harness_capability_not_old_assumption(self):self.assertIn('자동 기획의 지원 여부는 등록 명령',P['L130:S2']);self.assertNotIn('없는 병렬 실행이나 자동 기획',P['L130:S2'])
 def test_15_quest_generation_staged(self):self.assertIn('모의 요청 한 건의 왕복 → 취소·리로드·중복 요청 복구',P['L192:S2'])
 def test_16_lod_policy_distinct_from_crossfade(self):self.assertIn('별도의 진입·이탈 임계값 정책',P['L240:S2']);self.assertNotIn('LODGroup과 경계 hysteresis를 적용',P['L240:S2'])
 def test_17_worked_cases_have_input_action_output_explanation(self):
  cases=[l for l in L if l.get('learningCase')];self.assertEqual(len(cases),63)
  for l in cases:
   for k in ['title','idea','before','action','after','trap','question','answer']:self.assertGreater(len(l['learningCase'][k]),5,(l['id'],k))
 def test_18_all_harness_build_steps_have_cases(self):self.assertTrue(all(L[i-1].get('learningCase') for i in range(105,129)))
 def test_19_rules_exposed_not_discarded(self):
  values=[l for l in L if l['rules'].strip()];self.assertEqual(len(values),164)
  for l in values:self.assertTrue(l['rulesHtml'].strip());self.assertIn('값과 규칙 전체',(R/'pages'/f'{l["id"]:03}.md').read_text())
 def test_20_independent_transfer_tasks(self):self.assertEqual([l['id'] for l in L if l.get('transfer')],[40,80,128,160,256])
 def test_21_browser_data_matches_export(self):
  for id,data in [('courseData',L),('termData',T),('promptGuideData',G),('lessonVisualData',J(R/'data/lesson_visuals_v13.json'))]:self.assertEqual(json.loads(soup.find('script',id=id).string),data)
 def test_22_svg_structure_and_paths(self):
  for directory,count in [('lesson_visuals',256),('visuals',331),('visuals_dark',331)]:
   paths=list((R/directory).glob('*.svg'));self.assertEqual(len(paths),count)
   for p in paths:self.assertEqual(ET.fromstring(p.read_text()).tag.split('}')[-1],'svg',str(p))
 def test_23_glossary_relations(self):
  ids={t['id'] for t in T};s=J(W/'sourceData.json')
  for t in T:
   self.assertTrue(set(t['related'])<=ids,t['id']);self.assertTrue(set(t['sources'])<=set(s),t['id'])
   self.assertTrue(all(1<=n<=256 for n in t.get('usedIn',[])),t['id'])
 def test_24_existing_reference_and_skills_byte_preserved(self):
  hashes=J(R/'review/baseline_data/reference_hashes.json')
  for rel,sha in hashes.items():self.assertEqual(hashlib.sha256((R/rel).read_bytes()).hexdigest(),sha,rel)
 def test_25_text_fixes_have_audit_trail(self):
  records=J(W/'review/sentence_repairs.json');self.assertEqual(len(records),444)
  for x in records:self.assertNotEqual(x['before_why'],x['after_why']);self.assertIn(x['sentence'],P[x['key']])
 def test_26_known_wrong_meaning_replaced(self):
  fixtures=[('L1:S2','Windows 와 Android 용 오프라인','캐시','2D'),('L1:S2','설치가 필요하면 공식','자산','설치'),('L25:S4','대화에','선택','기록')]
  for key,part,bad,good in fixtures[:2]:
   old=next(x for x in OG[key] if part in OP[key][x['a']:x['b']]);new=next(x for x in G[key] if part in P[key][x['a']:x['b']]);self.assertIn(bad,old['why']);self.assertNotIn(bad,new['why']);self.assertIn(good,new['why'])
 def test_27_no_automatic_semantic_pass_claim(self):
  self.assertIn("independentReview:'BLOCKED'",html);self.assertIn('독립 비평가',html)
 def test_28_initial_bootstrap_is_in_page(self):self.assertIn('Chat이 아니라 Code',html);self.assertIn('Select folder',html);self.assertIn('Manual',html)
 def test_29_mini_prompt_visible_before_copy(self):self.assertIn('smallSliceText',html);self.assertIn('AI에게 보낼 요청을 먼저 읽기',html)
 def test_30_variants_identical_except_start_route(self):
  for file,route in [('기술_해설.html','tech'),('회색_서약_3D.html','lesson-161')]:
   s=(R/file).read_text().replace(f"if(!location.hash)history.replaceState(null,'','#{route}');\n",'');self.assertEqual(s,html)
 def test_31_no_truncated_quest_policy(self):self.assertNotIn('퀘스트 판정은 이다.',P['L27:S2']);self.assertIn('소개 대화만',P['L27:S2'])
 def test_32_no_walls_between_walkable_cells(self):self.assertIn('통행 가능한 이웃 셀 사이에는 세우지 않는다',P['L94:S2'])
 def test_33_slow_expiry_not_attack_cancellation(self):self.assertIn('감속 종료는 이동 배율만 복구',P['L136:S2']);self.assertNotIn('사망·감속 종료·비활성화',P['L136:S2'])
if __name__=='__main__':unittest.main(verbosity=2)

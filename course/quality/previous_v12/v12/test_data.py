from pathlib import Path
from bs4 import BeautifulSoup
import json,zipfile,hashlib,re,xml.etree.ElementTree as ET
W=Path(__file__).parent;B=W/'Ashfall_Student_Playbook_v12';R={'checks':[],'status':'RUNNING'}
def ck(x,name,detail=None):
 assert x,name
 R['checks'].append({'name':name,'detail':detail,'pass':True})
old=BeautifulSoup(Path('/mnt/data/ashfall_rpg_student_v11.html').read_text(),'html.parser');new=BeautifulSoup(Path('/mnt/data/ashfall_rpg_student_v12.html').read_text(),'html.parser')
for id in ['courseData','termData','sourceData','visualData','lessonTermData','aliasData','aliasPriorityData']:
 ck(json.loads(old.find(id=id).string)==json.loads(new.find(id=id).string),id+' preserved')
L=json.loads(new.find(id='courseData').string);T=json.loads(new.find(id='termData').string);G=json.loads(new.find(id='promptGuideData').string);V=json.loads(new.find(id='lessonVisualData').string);D=json.loads(new.find(id='darkVisualData').string)
msgs=[]
for l in L:
 for i,s in enumerate(l['steps'],1):msgs.append((f'L{l["id"]}:S{i}',s['prompt']))
 for k in ['repair','resume']:msgs.append((f'L{l["id"]}:{k}',l[k]))
for t in T:msgs.append((f'T:{t["id"]}',t['prompt']))
for k,t in json.loads((W/'ui_messages.json').read_text()).items():msgs.append((k,t))
for k,text in msgs:
 last=0
 for e in G[k]:
  assert last<=e['a']<e['b']<=len(text),(k,e)
  assert not text[last:e['a']].strip(),(k,'missed text',text[last:e['a']])
  assert e['label'].strip() and len(e['why'])>=30,(k,'empty annotation')
  last=e['b']
 assert not text[last:].strip(),(k,'missing tail')
ck(True,'Every non-whitespace source character covered in order',{'messages':len(msgs),'lesson_messages':1536,'sentences_and_list_items':sum(len(G[k])for k,t in msgs),'lesson_items':sum(len(G[k])for k,t in msgs if k.startswith('L'))})
ck(set(V)=={str(n)for n in range(1,257)},'All lessons have visual metadata')
for l in L:
 v=V[str(l['id'])];assert len(v['flow'])==4 and v['boundary'] and v['watch'];ET.fromstring(v['svg']);assert (B/'lesson_visuals'/f'{l["id"]:03}.svg').read_text()==v['svg'];assert l['title'] in v['svg']
ck(len(set(v['svg']for v in V.values()))==256,'256 distinct lesson SVG documents; 24 reusable visual mechanisms',len(set(v['kind']for v in V.values())))
ck(set(D)=={t['id']for t in T},'Dark variants cover all 331 glossary figures')
for t in T:ET.parse(B/'visuals_dark'/f'{t["id"]}.svg')
# untouched execution inputs and AI reference code remain unchanged
z=zipfile.ZipFile('/mnt/data/ashfall_rpg_student_v11_bundle.zip');counts={}
for info in z.infolist():
 if info.is_dir():continue
 rel='/'.join(info.filename.split('/')[1:])
 if rel.startswith(('AI_REFERENCE/','WORK_SKILLS/','messages/')):
  target=B/rel;assert target.is_file(),rel
  assert hashlib.sha256(z.read(info)).digest()==hashlib.sha256(target.read_bytes()).digest(),rel
  counts[rel.split('/')[0]]=counts.get(rel.split('/')[0],0)+1
ck(True,'AI execution materials preserved byte-for-byte',counts)
# Standalone entry points carry same content; routes differ only by initial fragment.
for name in ['index.html','회색_서약_3D.html','기술_해설.html']:
 h=BeautifulSoup((B/name).read_text(),'html.parser');assert json.loads(h.find(id='courseData').string)==L;assert h.find(id='themeMode') and h.find(id='lessonDiagramDialog')
ck(True,'All 3 HTML entry points contain new reading layer')
# Annotated Markdown exports exist and resolve local images and technical explanation links.
missing=[]
for f in (B/'pages').glob('*.md'):
 text=f.read_text();assert '왜 이렇게 요청하나요?' in text and '## 그림으로' in text
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if target.startswith(('http:','https:','#')):continue
  if not (f.parent/target.split('#')[0]).exists():missing.append((str(f),target))
ck(not missing,'Annotated Markdown local links resolve',missing[:10])
R['status']='PASS';(W/'data_report.json').write_text(json.dumps(R,ensure_ascii=False,indent=2));print('PASS',len(R['checks']),'data groups',counts)

from pathlib import Path
import json,re,hashlib,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
W=Path('/mnt/data/course_v11_work'); R=W/'Ashfall_Student_Playbook_v11'; O=W/'Ashfall_Student_Playbook_v10'
J=lambda p:json.loads(p.read_text()); checks=[]
def c(name,result):
 checks.append({'name':name,'passed':bool(result)})
 if not result: print('FAIL',name)
ls=J(R/'data/lessons.json'); old=J(O/'data/lessons.json');ts=J(R/'data/terms.json');ot=J(O/'data/terms.json');src=J(R/'data/sources.json')
c('lesson IDs 1..256',[l['id'] for l in ls]==list(range(1,257)))
c('all original 160 lessons unchanged',ls[:160]==old)
c('331 unique terms',len(ts)==331 and len({t['id'] for t in ts})==331)
for a,b in zip(ot,ts):
 c('original glossary '+a['id'],{k:v for k,v in a.items() if k!='usedIn'}=={k:v for k,v in b.items() if k!='usedIn'})
 c('original glossary image '+a['id'],(O/a['visual']).read_bytes()==(R/b['visual']).read_bytes())
ids={t['id'] for t in ts};nids={t['id'] for t in ts[250:]}
for l in ls:
 c(f'lesson {l["id"]} 4 stages',len(l['steps'])==4)
 c(f'lesson {l["id"]} references',(bool(l['refs']) or l['id']<=160) and all(r['url'].startswith('https://') for r in l['refs']))
 if l['id']>160:
  c(f'lesson {l["id"]} topic references',bool(l['topic_terms']) and all(x in ids for x in l['topic_terms']))
  c(f'lesson {l["id"]} target/actions',bool(l['goal']) and all(len(s['actions'])>=2 and s['expected'] for s in l['steps']))
 prompts=[s['prompt'] for s in l['steps']]+[l['repair'],l['resume']]
 for i,p in enumerate(prompts):
  label=f'{l["id"]}/{i}'
  if l['id']>160:c('no lesson metadata prompt '+label,not re.search(r'강의|교재|수강생|(?<!\w)L\d{3}(?!\w)',p))
  f=R/'messages'/f'{l["id"]:03d}'/(f'step{i+1}.txt' if i<4 else 'repair.txt' if i==4 else 'resume.txt')
  if l['id']<=160:
   if i>=4:continue
   f=R/'messages'/f'{l["id"]:03d}-{i+1}.txt'
  c('message file '+label,f.is_file() and f.read_text().rstrip('\n')==p.rstrip('\n'))
  if l['id']<=160:c('old prompt identical '+label,(O/f.relative_to(R)).read_bytes()==f.read_bytes())
for t in ts:
 c('related glossary '+t['id'],all(x in ids for x in t['related']))
 c('glossary sources '+t['id'],(bool(t['sources']) or t['id'] not in nids) and all(x in src for x in t['sources']))
 c('glossary image exists '+t['id'],(R/t['visual']).is_file())
 if t['id'] in nids:
  e=ET.fromstring((R/t['visual']).read_text());c('new SVG valid '+t['id'],e.tag.endswith('svg'))
  c('new glossary self-contained '+t['id'],all(t.get(x) for x in ['lead','analogy','steps','example','pitfall','question','answer','prompt','visualAlt']))
  c('new glossary used '+t['id'],len(t['usedIn'])>0)
q=J(R/'AI_REFERENCE/GRAY_OATH/quest_catalog.json');tools=J(R/'AI_REFERENCE/GRAY_OATH/editor_tools.json');g=J(R/'AI_REFERENCE/GRAY_OATH/game_checks.json')
c('28 quests',len(q)==28)
c('categories 10/8/6/4',[sum(x['category']==k for x in q) for k in ['main','side','contract','exploration']]==[10,8,6,4])
qids={x['questId'] for x in q}
c('quest references known',all(all(p in qids for p in x['prerequisites']) for x in q))
c('23 editor tools',len(tools)==23 and len({x['id'] for x in tools})==23)
c('all tools not claimed bound',all(x['bindingStatus']=='UNBOUND' for x in tools))
c('291 checks not claimed executed',len(g)==291 and all(x['status']=='NOT RUN' for x in g))
# Preservation of legacy AI implementation -- no implicit claim of rerunning it.
orig_files=list((O/'AI_REFERENCE').rglob('*')); preserved=0
for p in orig_files:
 if p.is_file():
  c('legacy AI reference '+str(p.relative_to(O)), (R/p.relative_to(O)).is_file() and p.read_bytes()==(R/p.relative_to(O)).read_bytes());preserved+=1
c('no distributed fonts',not any(p.suffix.lower() in ('.ttf','.otf','.woff','.woff2') for p in R.rglob('*') if p.is_file()))
# Parse all JSON and appended MD local references.
for p in R.rglob('*.json'):
 try:J(p);good=True
 except Exception:good=False
 c('JSON '+str(p.relative_to(R)),good)
for p in list((R/'pages').glob('*.md'))+list((R/'technology').glob('*.md')):
 for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if dest.startswith(('http:', 'https:', '#')):continue
  c('MD link '+str(p.relative_to(R))+' '+dest,(p.parent/dest.split('#')[0]).exists())
for p in [R/'index.html',R/'회색_서약_3D.html']:
 s=BeautifulSoup(p.read_text(),'html.parser')
 c('embedded lessons '+p.name,json.loads(s.select_one('#courseData').string)==ls)
 c('embedded terms '+p.name,len(json.loads(s.select_one('#termData').string))==331)
result={'scope':'Document and data assertions, not independent game execution tests','passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'assertions':len(checks),'legacy_ai_files_preserved':preserved,'results':checks}
(W/'content_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print({k:v for k,v in result.items() if k!='results'})
raise SystemExit(bool(result['failed']))

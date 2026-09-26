from playwright.sync_api import sync_playwright
from pathlib import Path
import json,time,sys
W=Path(__file__).parent; HTML=Path('/mnt/data/ashfall_rpg_student_v12.html').read_text()
report={'method':'Chromium injected HTML; file navigation blocked by environment; simulated storage tests explicitly separate','checks':[],'errors':[],'screenshots':[]}
def record(name,detail=True):
 report['checks'].append({'name':name,'result':detail});print('PASS',name,flush=True)
 (W/'browser_content_partial.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
def ck(v,msg):
 if not v:raise AssertionError(msg)
 record(msg)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=b.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
  page.on('pageerror',lambda e:report['errors'].append(str(e)))
  page.emulate_media(reduced_motion='reduce')
  page.set_content(HTML,wait_until='load',timeout=25000)
  ck(page.evaluate('AshfallReader.version===12&&AshfallPlaybook.lessonCount===256&&AshfallGlossary.termIds.length===331'),'Initial page and content counts')
  ck(page.locator('#storageWarning').is_visible(),'Native storage denied warning remains visible')
  page.emulate_media(color_scheme='dark');page.select_option('#themeMode','system');ck(page.evaluate("document.documentElement.dataset.theme==='dark'"),'System dark preference')
  page.select_option('#themeMode','light');page.emulate_media(color_scheme='light');page.emulate_media(color_scheme='dark');ck(page.evaluate("document.documentElement.dataset.theme==='light'"),'Explicit light overrides system dark')
  page.select_option('#themeMode','dark');page.emulate_media(color_scheme='light');ck(page.evaluate("document.documentElement.dataset.theme==='dark'"),'Explicit dark overrides system light')
  page.select_option('#themeMode','system');ck(page.evaluate("document.documentElement.dataset.theme==='light'"),'Return to automatic light')
  for a in range(1,257,16):
   result=page.evaluate('''([start,end])=>{let n=0,copyN=0;const old=copyText;copyText=async t=>{window.__copy=t;};try{for(let id=start;id<=end;id++){for(let s=0;s<4;s++){showLesson(id,s,true);const box=document.querySelector('[data-prompt=current]');if(!box)throw Error('no box '+id);if(document.querySelectorAll('[data-lesson-visual]').length!==1)throw Error('visual duplicate '+id);const t=byId.get(id).steps[s].prompt;const gs=AshfallReader.guideFor(t);const lines=[...box.querySelectorAll('.req-sentence')];if(lines.length!==gs.length)throw Error('sentence count '+id);lines.forEach((line,i)=>{if(line.textContent!==AshfallReader.sourceSlice(t,gs[i].a,gs[i].b))throw Error('sentence changed '+id);if(!line.querySelector('strong'))throw Error('not bold '+id);});box.querySelector('[data-copy]').click();if(window.__copy!==t)throw Error('copy changed '+id);box.querySelector('[data-prompt-view=raw]').click();if(box.querySelector('.prompt-raw .prompt-text').textContent!==t)throw Error('raw changed '+id);box.querySelector('[data-prompt-view=annotated]').click();copyN++;}const l=byId.get(id);for(const k of ['repair','resume']){document.querySelector('[data-prompt='+k+'] [data-copy]').click();if(window.__copy!==l[k])throw Error('aux copy changed '+id);copyN++;}n++;}}finally{copyText=old;}return {lessons:n,prompts:copyN};}''',[a,min(256,a+15)])
   record(f'Lessons {a}-{min(256,a+15)}: all four steps, bold spans, exact original copy, visual',result)
  # All dark glossary figures render and decode; visual mapping includes every term.
  page.select_option('#themeMode','dark')
  for start in range(0,331,35):
   value=page.evaluate('''async ([start,end])=>{for(const id of AshfallGlossary.termIds.slice(start,end)){showTerm(id);const img=document.querySelector('#techFigure img');await img.decode();if(img.naturalWidth<1||img.src!==DARK_VISUALS[id])throw Error('dark figure '+id);const box=document.querySelector('[data-prompt]');if(!box.querySelector('.req-why'))throw Error('missing rationale '+id);}return end-start;}''',[start,min(331,start+35)])
   record(f'Dark glossary figures {start+1}-{min(331,start+35)} decoded',value)
  ck(not report['errors'],'No JavaScript exceptions in all content render checks')
  b.close()
 report['status']='PASS'
except Exception as e:
 report['status']='FAIL';report['failure']=str(e);print('FAIL',str(e),flush=True)
finally:
 (W/'browser_content_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('REPORT',report['status'],len(report['checks']),flush=True)
if report['status']!='PASS':sys.exit(1)

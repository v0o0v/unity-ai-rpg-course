from pathlib import Path
import json,base64
from playwright.sync_api import sync_playwright
W=Path('/mnt/data/course_v11_work');ROOT=W/'Ashfall_Student_Playbook_v11'; checks=[];errors=[]
def c(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:print('FAIL',n,flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1440,'height':1000})
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content((ROOT/'index.html').read_text(),wait_until='load',timeout=60000)
 c('256 lesson navigation',page.locator('#navList a').count()==256)
 c('five course paths',page.locator('.route-card').count()==5)
 c('metadata',page.evaluate('AshfallPlaybook.lessonCount===256 && AshfallPlaybook.termCount===331'))
 c('unavailable storage warning',page.locator('#storageWarning').evaluate('(e)=>e.classList.contains("show")'))
 page.screenshot(path=str(W/'preview_home_final.png'),full_page=True)
 # Test every lesson renderer and every new copied message, preserving source text.
 for start in range(1,257,16):
  values=page.evaluate('''([a,z])=>{const out=[];window.__copyBackup=copyText;copyText=s=>{window.__copied=s;};
  for(let n=a;n<=z;n++){const l=byId.get(n);showLesson(n,0,false);out.push(["lesson "+n+" title",document.querySelector('h1').textContent===l.title]);out.push(["lesson "+n+" count",document.querySelector('.context').textContent.includes(n+' / 256')]);
  if(n>160){for(let k=0;k<4;k++){showLesson(n,k,false);const text=document.querySelector('[data-prompt="current"] .prompt-text').textContent;document.querySelector('[data-copy="current"]').click();out.push(["prompt "+n+"/"+k,text===l.steps[k].prompt&&window.__copied===l.steps[k].prompt]);}
  document.querySelector('[data-copy="repair"]').click();out.push(["repair "+n,window.__copied===l.repair]);document.querySelector('[data-copy="resume"]').click();out.push(["resume "+n,window.__copied===l.resume]);}}
  copyText=window.__copyBackup;return out;}''',[start,min(256,start+15)])
  for n,v in values:c(n,v)
 print('lesson render/copy checks done',flush=True)
 # Each term renders an actual decodable image; all new SVG text within overall canvas.
 for start in range(0,331,15):
  vals=page.evaluate('''async ([a,z])=>{const out=[];for(let i=a;i<z;i++){const t=TERMS[i];showTerm(t.id);const img=document.querySelector('#techFigure img');await img.decode();out.push(["guide "+t.id,document.querySelector('h1').textContent===t.title&&img.naturalWidth>0]);
  if(i>=250){const svg=(await (await fetch(img.src)).text());const div=document.createElement('div');div.style.cssText='position:absolute;left:-5000px;width:900px';div.innerHTML=svg;document.body.append(div);const bad=[...div.querySelectorAll('text')].filter(e=>{const b=e.getBBox();return b.x<0||b.y<0||b.x+b.width>901||b.y+b.height>541;});out.push(["SVG text within canvas "+t.id,bad.length===0]);div.remove();}}
  return out;}''',[start,min(331,start+15)])
  for n,v in vals:c(n,v)
 print('glossary renders done',flush=True)
 # Actual page controls; simulated rules labelled as simulations.
 page.evaluate("showTerm('quest-simulation')")
 def q(action):page.locator(f'[data-q="{action}"]').click()
 q('claim');c('incomplete quest rejects reward','부족' in page.locator('#labOutput').inner_text())
 q('a');q('a');c('duplicate clue ignored','다시 세지' in page.locator('#labOutput').inner_text())
 for a in ['b','accept','repair']:q(a)
 c('missing repair part blocked','부품' in page.locator('#labOutput').inner_text())
 for a in ['part','repair','reveal','claim','claim']:q(a)
 c('single quest reward','추가 지급하지' in page.locator('#labOutput').inner_text() and '80골드' in page.locator('#labVisual').inner_text())
 q('save');q('load');q('claim');c('reward receipt survives model restore','추가 지급하지' in page.locator('#labOutput').inner_text())
 page.evaluate("showTerm('editor-ai')")
 page.locator('#draftMake').click();page.locator('#originalEdit').click();page.locator('#draftApply').click();c('stale draft denied','버전 충돌' in page.locator('#labOutput').inner_text())
 page.locator('#draftReset').click();page.locator('#draftMake').click();page.locator('#draftCancel').click();page.locator('#draftApply').click();c('cancelled draft denied','취소한' in page.locator('#labOutput').inner_text())
 page.locator('#draftReset').click();page.locator('#draftMake').click();page.locator('#draftApply').click();page.locator('#draftApply').click();c('duplicate apply denied','이미 적용' in page.locator('#labOutput').inner_text())
 page.screenshot(path=str(W/'preview_ai_draft_final.png'),full_page=True)
 page.evaluate("showTerm('map-projection')")
 c('map coordinates correct',page.evaluate('JSON.stringify(mapXZ(192,96))===JSON.stringify({u:.5,v:.25})'))
 page.locator('#worldX').fill('384');page.locator('#worldX').dispatch_event('input');c('map edge matches','1.000' in page.locator('#labOutput').inner_text())
 page.evaluate("showTerm('percentile')")
 c('slow tails and p95 interpretation','p95 16ms / p99 120ms' in page.locator('#labOutput').inner_text())
 page.locator('#slowFrames').uncheck();c('no slow-tail p99','p99 16ms' in page.locator('#labOutput').inner_text())
 c('nearest-rank edge conditions',page.evaluate('nearestRank([4,1,3,2],.5)===2&&nearestRank([4,1,3,2],1)===4'))
 # Route, filter, compatibility. No paid service execution.
 page.evaluate('state.meshy=false');c('native route skips paid service',page.evaluate('!route().includes(173)&&route().includes(172)&&route().includes(177)&&route().at(-1)===256'))
 page.evaluate('state.meshy=true');c('Meshy route includes four pages',page.evaluate('[173,174,175,176].every(x=>route().includes(x))'))
 page.select_option('#groupFilter','saga');c('saga filter96',page.locator('#navList a').count()==96)
 page.locator('#search').fill('퀘스트');c('keyword finds quest',page.locator('#navList a').count()>0)
 page.locator('#search').fill('');page.select_option('#groupFilter','all')
 for v in [9,10,11]:
  c('import version '+str(v),page.evaluate('(v)=>validateState({version:v,last:160,route:"main",art:"local",pad:false,lessons:{160:{checked:[true,false,false,false],note:"이전 기록"}}}).lessons[160].note==="이전 기록"',v))
 c('bad progress rejected',page.evaluate('(()=>{try{validateState({version:11,last:999,route:"main",art:"local",pad:false,lessons:{}});return false}catch(e){return true}})()'))
 # Native download then native upload flow.
 page.evaluate("showLesson(192,3,false)")
 page.locator('#observation').fill('AI 초안 충돌을 모형에서 확인. 실제 Unity는 미검증.')
 with page.expect_download() as d:page.locator('#exportBtn').click()
 downloaded=d.value;downloaded.save_as(str(W/'browser_progress_export.json'))
 exported=json.loads((W/'browser_progress_export.json').read_text());c('actual progress download retains note',exported['lessons']['192']['note'].startswith('AI 초안'))
 page.on('dialog',lambda d:d.accept())
 imported={'version':10,'last':160,'route':'main','art':'local','pad':False,'lessons':{'160':{'checked':[True,True,False,False],'note':'이전10판 기록'}}}
 page.locator('#importFile').set_input_files({'name':'old-progress.json','mimeType':'application/json','buffer':json.dumps(imported).encode()});page.wait_for_timeout(100)
 c('actual file import migrates records',page.evaluate('state.version===11&&state.lessons[160].note==="이전10판 기록"'))
 # Real link origin and stage restore.
 page.evaluate("location.hash='lesson-192'");page.wait_for_timeout(60);page.evaluate('showLesson(192,1,false)')
 a=page.locator('.tech-ribbon [data-tech="editor-ai"]')
 c('relevant inline glossary link exists',a.count()>0)
 a.first.click();page.wait_for_timeout(80)
 c('glossary link navigates',page.locator('h1').inner_text()==page.evaluate("termById.get('editor-ai').title"))
 back=page.locator('[data-back-to-reading]').first
 if back.count():back.click()
 else:
  candidates=page.locator('button').all_text_contents();print('BACKSELECTOR',candidates,flush=True)
 page.wait_for_timeout(80)
 c('return restores step',page.evaluate('activeId===192&&activeStep===1'))
 page.screenshot(path=str(W/'preview_quest_editor_final.png'),full_page=True)
 # Image enlargement; mobile no whole page overflow.
 page.evaluate("showTerm('quest-graph')");page.locator('#enlargeFigure').click();c('image dialog opens',page.locator('#imageDialog').evaluate('(e)=>e.open'));page.locator('#closeImageDialog').click()
 page.set_viewport_size({'width':390,'height':844})
 for n in [161,186,192,237,256]:
  page.evaluate('(n)=>showLesson(n,1,false)',n)
  c('mobile no page overflow '+str(n),page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  if n==237:page.screenshot(path=str(W/'preview_mobile_profiling.png'),full_page=True)
 page.evaluate('go(256)');page.wait_for_timeout(60);c('last page reachable','내 이야기' in page.locator('h1').inner_text())
 c('no JS exceptions',not errors)
 b.close()
result={'scope':'Browser UI assertions, not Unity/game tests','passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'assertions':len(checks),'javascript_errors':errors,'results':checks}
(W/'browser_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print({k:v for k,v in result.items() if k!='results'},flush=True)
raise SystemExit(bool(result['failed']))

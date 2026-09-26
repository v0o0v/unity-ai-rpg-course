from pathlib import Path
from playwright.sync_api import sync_playwright
import json, time, sys, traceback, hashlib
W=Path(__file__).resolve().parents[2];HTML=(W/'index.html').read_text()
R={'status':'RUNNING','checks':[],'errors':[],'screenshots':[],'environment':'Chromium set_content; no user Windows or Unity execution','html_sha256':hashlib.sha256(HTML.encode()).hexdigest()}
def ck(cond,name,data=None):
 R['checks'].append({'name':name,'ok':bool(cond),'detail':data})
 (W/'review/browser_progress.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
 if not cond:raise AssertionError(name+': '+str(data))
 print('PASS',name,flush=True)
def page(b, width=1440, store=None):
 q=b.new_page(viewport={'width':width,'height':1000 if width>500 else 844});q.emulate_media(reduced_motion='reduce',color_scheme='light')
 q.on('pageerror',lambda e:R['errors'].append(str(e)))
 if store is not None:q.evaluate('s=>{window.__store={...s};Object.defineProperty(window,"localStorage",{configurable:true,value:{getItem:k=>Object.hasOwn(__store,k)?__store[k]:null,setItem:(k,v)=>__store[k]=String(v),removeItem:k=>delete __store[k]}})}',store)
 q.set_content(HTML,wait_until='load',timeout=45000)
 return q
def shot(q,name):
 q.evaluate("document.getElementById('toast').style.display='none'")
 q.screenshot(path=str(W/'review'/name),animations='disabled');R['screenshots'].append(name)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  q=page(b)
  ck(q.locator('#localStart').count()==1,'In-page local AI startup guide')
  ck(q.evaluate("AshfallReview.version===13&&AshfallPlaybook.lessonCount===256"),'Version and lesson registry')
  q.evaluate('showLesson(1,1,true)')
  before=q.locator('#stepPanel').bounding_box()['y'];ck(before<1250,'Current prompt starts sooner than v12 1517px',round(before))
  ck(q.locator('#figureDetails').get_attribute('open') is None,'Large diagram no longer blocks every step')
  q.locator('[data-jump=rulesCard]').click();ck(q.locator('#rulesCard table').is_visible(),'Previously hidden specification table is readable')
  q.locator('[data-jump=stepPanel]').click();ck(q.locator('[data-prompt=current]').is_visible(),'Jump directly to current request');ck(q.locator('[data-prompt=current] .req-outline').get_attribute('open') is None,'Jump does not force open requirements outline');q.locator('[data-jump=diagnosticCard]').click();q.locator('.small-slice-preview summary').click();q.evaluate('window.__miniCopy=null;window.__oldCopy=copyText;copyText=t=>window.__miniCopy=t');q.locator('#copySmallSlice').click();ck(q.evaluate('__miniCopy===document.getElementById("smallSliceText").textContent'), 'Fallback request preview matches copied payload');q.evaluate('copyText=window.__oldCopy');q.locator('[data-jump=stepPanel]').click()
  first=q.locator('[data-prompt=current] .req-why').first.inner_text()
  ck('캐시' not in first and '2D' in first,'Project rationale is not a download explanation',first)
  # Real UI buttons, copy intercepted at function boundary; not claiming OS clipboard.
  q.evaluate("window.__copied=[];copyText=async t=>{window.__copied.push(t)}")
  q.locator('[data-copy=current]').click();got=q.evaluate('__copied.at(-1)');expected=q.evaluate('byId.get(1).steps[1].prompt')
  ck(got==expected and '왜 이렇게 요청' not in got,'Copy carries current prompt only')
  q.locator('[data-prompt=current] [data-prompt-view=raw]').click();ck(q.locator('[data-prompt=current] .prompt-raw').is_visible(),'Raw prompt view')
  q.locator('[data-prompt=current] [data-prompt-view=annotated]').click()
  q.locator('[data-jump=figureDetails]').click();q.locator('[data-viz-mode=risk]').click();ck(q.locator('.lesson-viz-svg').evaluate("e=>e.classList.contains('show-risk')"),'Preserved boundary diagram')
  q.locator('[data-enlarge-lesson]').click();ck(q.locator('#lessonDiagramDialog').evaluate('e=>e.open'),'Figure enlargement');q.keyboard.press('Escape')
  # New case and glossary return.
  q.evaluate('showLesson(9,2,true)');q.locator('[data-jump=workedCase]').click();ck(q.locator('.case-result').is_visible(),'Worked result comparison visible')
  q.locator('.understanding summary').click();ck('계산 한도 초과' in q.locator('.understanding').inner_text(),'Distinct unreachable and budget status')
  checks=q.evaluate('JSON.stringify(AshfallPlaybook.getProgress().lessons[9].checked)')
  q.select_option('#themeMode','dark');q.select_option('#themeMode','light')
  ck(checks==q.evaluate('JSON.stringify(AshfallPlaybook.getProgress().lessons[9].checked)'),'Reading does not set completion')
  q.evaluate('showLesson(194,1,true)')
  q.locator('[data-prompt=current] a[data-tech]').first.scroll_into_view_if_needed();origin=q.evaluate('scrollY');q.locator('[data-prompt=current] a[data-tech]').first.click();q.wait_for_timeout(80)
  ck(q.evaluate('location.hash.startsWith("#tech-")'),'Glossary from annotated request')
  q.locator('[data-back-to-reading]').first.click();q.wait_for_timeout(160)
  ck(q.locator('.step-tab.active').get_attribute('data-step')=='1','Return to same step')
  ck(abs(q.evaluate('scrollY')-origin)<70,'Return to original reading scroll',{'was':origin,'now':q.evaluate('scrollY')})
  q.evaluate('showLesson(108,0,true)'); q.locator('#step-tab-0').focus();q.keyboard.press('ArrowRight')
  ck(q.locator('.step-tab.active').get_attribute('data-step')=='1' and q.evaluate('document.activeElement.id')=='step-tab-1','Keyboard tab movement and focus')
  ck(not q.evaluate('rec(108).checked.some(Boolean)'),'Tab keys do not mark completed')
  # Entire page/step render and copy source comparison in batches; semantic teaching success not inferred.
  for start in range(1,257,32):
   result=q.evaluate('''start=>{let count=0;const bad=[];for(let n=start;n<Math.min(start+32,257);n++)for(let s=0;s<4;s++){showLesson(n,s,false);if(document.querySelector('h1').textContent!==byId.get(n).title)bad.push([n,s,'title']);const parts=[...document.querySelectorAll('[data-prompt=current] .req-sentence')].map(e=>e.textContent).join('');if(parts.replace(/\s/g,'')!==byId.get(n).steps[s].prompt.replace(/\s/g,''))bad.push([n,s,'spans']);const p=document.querySelector('[data-prompt=current]');if(!p||!document.querySelector('#diagnosticCard'))bad.push([n,s,'elements']);count++;}return {count,bad};}''',start)
   ck(not result['bad'],f'All steps rendered {start}–{min(start+31,256)}',result)
  q.close()
  # Different viewports and colors, actual screenshots for visual inspection.
  for width,mode,n,s in [(1440,'light',1,1),(1440,'dark',9,1),(390,'dark',194,1),(390,'light',125,2),(1440,'dark',240,2)]:
   q=page(b,width);q.select_option('#themeMode',mode);q.evaluate('([n,s])=>showLesson(n,s,true)',[n,s]);
   ck(q.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'{width}/{mode}/L{n}: no page overflow')
   shot(q,f'v13_{width}_{mode}_{n}_top.png')
   q.locator('[data-jump=stepPanel]').click();shot(q,f'v13_{width}_{mode}_{n}_prompt.png')
   if n in [125,240]:q.locator('[data-jump=workedCase]').click();shot(q,f'v13_{width}_{mode}_{n}_example.png')
   q.close()
  q=page(b)
  for v in [9,10,11,12,13]:ck(q.evaluate('v=>AshfallPlaybook.validateProgress({version:v,last:1,route:"main",art:"local",pad:false,lessons:{}}).version===13',v),f'Import version {v}')
  try:q.evaluate('AshfallPlaybook.validateProgress({version:99})');bad=False
  except Exception:bad=True
  ck(bad,'Reject malformed progress')
  q.evaluate('showLesson(185,3,true)');q.locator('#observation').fill('시험 진행 A만 완료. B와 원본은 유지됨. 아직 실제 Unity에서는 검사하지 않음.')
  with q.expect_download() as ev:q.locator('#exportBtn').click()
  file=W/'review/downloaded_progress.json';ev.value.save_as(file);progress=json.loads(file.read_text());ck(progress['version']==13 and '시험 진행 A' in progress['lessons']['185']['note'],'Actual progress JSON download')
  progress['version']=12;progress['lessons']['185']['note']='이전 확인 기록 테스트';file.write_text(json.dumps(progress,ensure_ascii=False));q.on('dialog',lambda d:d.accept());q.locator('#importFile').set_input_files(str(file));q.wait_for_timeout(180)
  ck(q.evaluate('AshfallPlaybook.getProgress().lessons[185].note')=='이전 확인 기록 테스트','Actual old-progress file import preserves notes')
  q.close()
  q=page(b,store={});q.select_option('#themeMode','dark');q.evaluate('showLesson(9,3,false)');q.locator('#observation').fill('테마와 단계 복원');stored=q.evaluate('__store');q.close()
  q=page(b,store=stored);ck(q.evaluate('AshfallAppearance.getTheme()==="dark"'),'Theme restore from explicit simulated storage');ck(q.evaluate('AshfallPlaybook.getProgress().lessons[9].note')=='테마와 단계 복원','Progress restore from explicit simulated storage');q.close()
  q=page(b);q.select_option('#themeMode','dark');result=q.evaluate('''()=>{let checked=0;const bad=[];for(const t of TERMS){showTerm(t.id);const image=document.querySelector('#techFigure img');if(document.querySelector('h1')?.textContent!==t.title||!image?.src.startsWith('data:image/svg+xml'))bad.push(t.id);checked++;}return {checked,bad};}''');ck(not result['bad'] and result['checked']==331,'All 331 glossary views render in dark mode',result);q.close();ck(not R['errors'],'No uncaught browser errors',R['errors']);b.close()
 R['status']='PASS'
except Exception as e:
 R['status']='FAIL';R['failure']=str(e);R['traceback']=traceback.format_exc();print(R['traceback'],flush=True)
finally:
 (W/'review/browser_report.json').write_text(json.dumps(R,ensure_ascii=False,indent=2));print(R['status'],len(R['checks']),flush=True)
if R['status']!='PASS':sys.exit(1)

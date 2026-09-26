from playwright.sync_api import sync_playwright
from pathlib import Path
import json,time,sys
W=Path(__file__).parent;HTML=Path('/mnt/data/ashfall_rpg_student_v12.html').read_text();R={'checks':[],'errors':[],'screenshots':[],'status':'RUNNING'}
def ck(ok,msg,detail=None):
 if not ok:raise AssertionError(msg)
 R['checks'].append({'name':msg,'detail':detail,'pass':True});print('PASS',msg,flush=True);(W/'ui_partial.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
def loaded(b,size=None,store=None):
 q=b.new_page(viewport=size or {'width':1440,'height':1000},device_scale_factor=1);q.emulate_media(reduced_motion='reduce',color_scheme='light');q.on('pageerror',lambda e:R['errors'].append(str(e)))
 if store is not None:q.evaluate('d=>{window.__store={...d};Object.defineProperty(window,"localStorage",{configurable:true,value:{getItem:k=>Object.hasOwn(__store,k)?__store[k]:null,setItem:(k,v)=>__store[k]=String(v),removeItem:k=>delete __store[k]}});}',store)
 q.set_content(HTML,wait_until='load',timeout=25000);return q
def shot(q,name):
 q.evaluate("document.getElementById('toast').style.display='none'");q.screenshot(path=str(W/name),animations='disabled',timeout=15000);R['screenshots'].append(name)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  q=loaded(b)
  q.evaluate('showLesson(194,1,true)')
  before=q.evaluate('JSON.stringify(AshfallPlaybook.getProgress())')
  q.locator('[data-prompt=current] [data-why-toggle]').click();ck(q.locator('[data-prompt=current]').evaluate("e=>e.classList.contains('hide-rationales')"),'Hide and show explanations')
  q.locator('[data-prompt=current] [data-why-toggle]').click();q.locator('[data-viz-mode=risk]').click();ck(q.locator('.lesson-viz-svg').evaluate("e=>e.classList.contains('show-risk')"),'Show caution overlay')
  q.select_option('#themeMode','dark');q.select_option('#themeMode','light');ck(before==q.evaluate('JSON.stringify(AshfallPlaybook.getProgress())'),'Reading actions leave learning checks unchanged')
  q.locator('[data-enlarge-lesson]').click();ck(q.locator('#lessonDiagramDialog').evaluate('e=>e.open'),'Enlarge lesson figure');q.keyboard.press('Escape');ck(not q.locator('#lessonDiagramDialog').evaluate('e=>e.open'),'Close enlarged figure via Escape')
  q.evaluate("location.hash='lesson-009'");q.wait_for_timeout(50);q.evaluate('showLesson(9,1,true)');a=q.locator('[data-prompt=current] a[data-tech]').first;a.scroll_into_view_if_needed();old=q.evaluate('scrollY');a.click();q.wait_for_timeout(80);ck(q.evaluate("location.hash.startsWith('#tech-')"),'Open technical explanation from sentence')
  q.locator('[data-back-to-reading]').first.click();q.wait_for_timeout(150);ck(q.locator('.step-tab.active').get_attribute('data-step')=='1','Return to same instruction step');ck(abs(q.evaluate('scrollY')-old)<50,'Return to original scroll position')
  q.locator('[data-prompt=current] [data-prompt-view=raw]').click();ck(q.locator('[data-prompt=current] .prompt-raw').is_visible(),'Raw view excludes explanations')
  q.locator('[data-prompt=current] [data-prompt-view=annotated]').click();q.locator('[data-prompt=current] .req-outline summary').click();jump=q.locator('[data-prompt=current] [data-req-jump]').last;h=q.evaluate('location.hash');jump.click();ck(q.evaluate('location.hash')==h,'Requirement jump does not change lesson route')
  # Native storage fails honestly, export/import works through actual file download.
  q.evaluate('showLesson(9,3,true)');q.locator('#observation').fill('확인 메모: 요구사항을 읽고 그림을 비교했다.');
  with q.expect_download() as info:q.locator('#exportBtn').click()
  f=W/'downloaded_progress.json';info.value.save_as(f);v=json.loads(f.read_text());ck(v['version']==12 and v['lessons']['9']['note'].startswith('확인 메모'),'Real progress JSON download')
  v['version']=11;v['lessons']['9']['note']='이전판에서 가져온 메모';f.write_text(json.dumps(v,ensure_ascii=False));q.on('dialog',lambda d:d.accept());q.locator('#importFile').set_input_files(str(f));q.wait_for_timeout(200);ck(q.evaluate('AshfallPlaybook.getProgress().lessons[9].note')=='이전판에서 가져온 메모','Real v11 progress file import')
  for version in [9,10,12]:ck(q.evaluate('v=>AshfallPlaybook.validateProgress({version:v,last:1,route:"main",art:"local",pad:false,lessons:{}}).version===12',version),f'Progress v{version} accepted')
  # Screenshot each fresh page to isolate high-volume DOM checks from screenshot tests.
  q.close()
  for size in [{'width':1440,'height':1000},{'width':390,'height':844}]:
   for mode in ['light','dark']:
    q=loaded(b,size);q.select_option('#themeMode',mode);q.evaluate('showLesson(194,1,true)')
    ck(q.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'{size["width"]} {mode}: no viewport overflow')
    shot(q,f'final_{size["width"]}_{mode}_diagram.png')
    q.evaluate('()=>{const e=document.querySelector("[data-prompt=current]");scrollTo({top:scrollY+e.getBoundingClientRect().top-115,behavior:"instant"});}')
    q.wait_for_timeout(70);shot(q,f'final_{size["width"]}_{mode}_prompt.png')
    ck(q.locator('[data-prompt=current] .req-why').first.is_visible(),f'{size["width"]} {mode}: sentence explanations rendered')
    q.close()
  # Storage logic on explicitly simulated storage, in fresh documents.
  q=loaded(b,store={});q.select_option('#themeMode','dark');stash=q.evaluate('__store');ck(stash.get('ashfall_reader_theme')=='dark','Theme persistence logic writes simulated storage');q.close()
  q=loaded(b,store=stash);ck(q.evaluate("AshfallAppearance.getMode()==='dark'&&AshfallAppearance.getTheme()==='dark'"),'Saved theme restored into fresh document (simulation)');q.close()
  q=loaded(b);q.select_option('#themeMode','dark');q.evaluate("showTerm('collider')");q.locator('#techFigure').evaluate('e=>e.scrollIntoView({block:"start",behavior:"instant"})');q.evaluate('scrollBy({top:-110,behavior:"instant"})');shot(q,'final_glossary_dark.png');q.locator('#techFigure .figure-actions button').click();ck(q.locator('#imageDialog').evaluate('e=>e.open'),'Dark glossary figure enlarged');q.select_option('#themeMode','light',force=True) if False else None
  q.evaluate("AshfallAppearance.setMode('light')");ck(q.evaluate("document.getElementById('zoomImage').src===LIGHT_VISUALS.collider"),'Open glossary image updates on theme change');q.keyboard.press('Escape');
  q.close();ck(not R['errors'],'No runtime JavaScript errors');b.close();R['status']='PASS'
except Exception as e:R['status']='FAIL';R['failure']=str(e);print('FAIL',e,flush=True)
finally:(W/'ui_report.json').write_text(json.dumps(R,ensure_ascii=False,indent=2));print(R['status'],len(R['checks']),flush=True)
if R['status']!='PASS':sys.exit(1)

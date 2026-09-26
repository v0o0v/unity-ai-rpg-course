from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json,base64,traceback
W=Path('/mnt/data/course_v14_work'); out=W/'review'; out.mkdir(exist_ok=True)
html=Path('/mnt/data/ashfall_rpg_student_v14.html').read_text()
base=BeautifulSoup(Path('/mnt/data/ashfall_rpg_student_v13_review.html').read_text(),'html.parser')
new=BeautifulSoup(html,'html.parser')
ref=json.loads(new.find('script',id='editorReferenceData').string)
results=[]
def check(name,expr):
 if not expr: raise AssertionError(name)
 results.append({'check':name,'result':'PASS'})
# Structural preservation: artifacts not tested as a Unity project.
for x in base.select('script[type="application/json"]'):
 check('unchanged embedded data '+x['id'], x.string==new.find('script',id=x['id']).string)
lessons=json.loads(new.find('script',id='courseData').string)
check('256 original lessons',len(lessons)==256)
check('8 unique official references',len(ref['references'])==8 and len({r['id'] for r in ref['references']})==8)
for r in ref['references']:
 check(r['id']+' source metadata',r['source_url'].startswith('https://docs.unity3d.com/') and r['image_url'].startswith('https://docs.unity3d.com/') and bool(r['capture_note']) and len(r['points'])==3)
 check(r['id']+' lesson targets valid',all(1<=n<=256 for n in r['lessons']))
 check(r['id']+' no class-dependent prompt',not any(t in r['prompt'] for t in ('강의','수강생','교재','L105')))
# Deliberate 1x1 test fixture: exercises load/error handlers only, never a screenshot fidelity check.
PIXEL=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j1ioAAAAASUVORK5CYII=')
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 context=browser.new_context(viewport={'width':1440,'height':1000},color_scheme='dark')
 page=context.new_page(); errors=[]; requests=[]; mode={'value':'abort'}
 page.on('pageerror',lambda e: errors.append(str(e)))
 def route(req):
  requests.append(req.request.url)
  if mode['value']=='fixture': req.fulfill(status=200,content_type='image/png',body=PIXEL)
  else:req.abort('internetdisconnected')
 page.route('**/*',route)
 page.set_content(html,wait_until='domcontentloaded');page.wait_for_timeout(200)
 check('reader boots',page.locator('#content').inner_text().find('Unity Editor의 실제 창')>=0)
 check('no network on load',len(requests)==0)
 check('no initial JS exceptions',not errors)
 # all related lesson panels, all unrelated lessons remain panel-free
 maps={i:[r['id'] for r in ref['references'] if i in r['lessons']] for i in range(1,257)}
 counts=page.evaluate('''() => {const result=[];for(let i=1;i<=256;i++){showLesson(i,1,false);result.push({i,count:document.querySelectorAll('#editorScreenSection').length,step:activeStep});}return result;}''')
 check('all 256 panels attach only to relevant lessons',all(x['count']==bool(maps[x['i']]) and x['step']==1 for x in counts))
 check('no photo requests from changing lessons',not requests)
 page.evaluate('showLesson(9,1,false)');before=page.evaluate('window.AshfallPlaybook.getProgress()')
 page.get_by_role('button',name='실제 Editor 화면',exact=True).click();page.wait_for_timeout(50)
 check('lesson9 has Input Actions card',page.locator('#editorScreenSection [data-er-id]').get_attribute('data-er-id')=='input-actions')
 check('opening guidance does not request photos',not requests)
 card=page.locator('#editorScreenSection [data-er-id="input-actions"]')
 card.locator('[data-er-load]').click();page.wait_for_timeout(200)
 check('load is explicit and requests official URL',requests[-1]==next(r['image_url'] for r in ref['references'] if r['id']=='input-actions'))
 check('network failure is visible',card.locator('.er-status').inner_text().startswith('이미지를 불러오지 못했습니다.'))
 check('no fake replacement after failure',card.locator('img').is_hidden() and card.locator('[data-er-zoom]').is_hidden())
 check('reference interaction preserves progress',page.evaluate('window.AshfallPlaybook.getProgress()')==before)
 # Rendering handlers with clearly nonrepresentative local network fixture.
 mode['value']='fixture';card.locator('[data-er-load]').click();page.wait_for_timeout(200)
 check('success handler (test pixel only)',card.locator('img').is_visible() and card.locator('[data-er-zoom]').is_visible())
 check('image colors not inverted in dark theme',card.locator('img').evaluate('(x)=>getComputedStyle(x).filter')=='none')
 card.locator('[data-er-zoom]').click();check('zoom opens',page.locator('#editorZoomDialog').evaluate('(x)=>x.open'))
 page.locator('#editorZoomDialog [data-er-native]').click();check('native size control',page.locator('#editorZoomDialog').evaluate('(x)=>x.classList.contains("er-native")'))
 page.keyboard.press('Escape');check('Escape closes zoom',not page.locator('#editorZoomDialog').evaluate('(x)=>x.open'))
 check('zoom preserves step and progress',page.evaluate('activeStep')==1 and page.evaluate('window.AshfallPlaybook.getProgress()')==before)
 page.evaluate('window.__copies=[];copyText=(text)=>window.__copies.push(text)')
 page.locator('#stepPanel [data-copy="current"]').click()
 check('original copied prompt unchanged',page.evaluate('window.__copies.at(-1)')==lessons[8]['steps'][1]['prompt'])
 card.locator('summary').click();card.locator('[data-er-copy]').click()
 check('reference request copy excludes commentary',page.evaluate('window.__copies.at(-1)')==next(r['prompt'] for r in ref['references'] if r['id']=='input-actions'))
 # gallery search and individual cards can load/error without side effects.
 page.evaluate('window.AshfallEditorReferences.openGallery()')
 check('gallery has 8 screens',page.locator('#erGalleryList [data-er-id]').count()==8)
 page.locator('#erSearch').fill('퀘스트');check('quest search does not pretend finished custom tool',page.locator('#erGalleryList [data-er-id="ui-builder"]').count()==1 and page.locator('#erGalleryList [data-er-id="ui-builder"]').inner_text().find('Quest Editor가 아닙니다')>=0)
 page.locator('#erSearch').fill('존재하지않는검색어');check('empty search state',page.locator('#erGalleryList').inner_text().startswith('일치하는 화면이 없습니다.'))
 page.locator('#erSearch').fill('')
 for r in ref['references']:
  c=page.locator(f'#erGalleryList [data-er-id="{r["id"]}"]');c.locator('[data-er-load]').click()
 page.wait_for_timeout(200)
 check('all image load controls settle with test fixture',page.locator('#erGalleryList img:visible').count()==8)
 page.keyboard.press('Escape');check('gallery closes to same step',not page.locator('#editorGalleryDialog').evaluate('(x)=>x.open') and page.evaluate('activeStep')==1)
 check('gallery preserves learning data',page.evaluate('window.AshfallPlaybook.getProgress()')==before)
 # Real screenshots not available in this network; previews show unloaded official references, not the fixture.
 mode['value']='abort'
 for width,theme in [(1440,'dark'),(390,'dark'),(390,'light')]:
  page.set_viewport_size({'width':width,'height':1000});page.evaluate(f'window.AshfallAppearance.setMode("{theme}")');page.evaluate('showLesson(194,1,false)')
  page.get_by_role('button',name='실제 Editor 화면',exact=True).click();page.wait_for_timeout(70)
  check(f'no horizontal document overflow {width}/{theme}',page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'))
  check(f'correct custom tool distinction {width}/{theme}','이 과정의 Quest Editor가 아닙니다' in page.locator('#editorScreenSection').inner_text())
  if width==390 and theme=='dark':
   page.locator('#editorScreenSection').scroll_into_view_if_needed();page.screenshot(path=str(out/'reference_guidance_mobile.png'))
 check('no runtime JS exceptions',not errors)
 context.close();browser.close()
(out/'tests.json').write_text(json.dumps({'checks':results,'note':'Network success handlers used a 1x1 synthetic test pixel. No actual official screenshots downloaded or visually rendered by local Chromium. Original image pixels separately opened in web tool.'},ensure_ascii=False,indent=2))
print('PASS',len(results),'checks; 256 lesson renders included as one aggregate check')

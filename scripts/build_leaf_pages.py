"""Build independently readable sections from book notes plus authored extensions.
Run after expand_notes.py when rebuilding the original topic pages.
"""
from pathlib import Path
from copy import deepcopy
from html import escape as E
from lxml import html
from opencc import OpenCC
import json,re
ROOT=Path(__file__).resolve().parents[1]
ns={'__file__':str(ROOT/'scripts/expand_notes.py')}
exec((ROOT/'scripts/expand_notes.py').read_text().split('SOURCES=')[0],ns)
render=ns['render'];CATS=ns['CATS'];cc=OpenCC('s2twp')
def clean(s):
 return cc.convert(s).replace('疾病程式','疾病進程').replace('有效迴圈','有效循環').replace('循環支援','循環支援').replace('物件、目的','對象、目的')
def save(path,doc):
 path.write_text(clean('<!doctype html>\n'+html.tostring(doc,encoding='unicode',method='html')))
def chunkmap(folder):
 result={}
 for md in sorted(folder.glob('*.md')):
  for ch in re.split(r'^@@ ',md.read_text(),flags=re.M)[1:]:
   key,body=ch.split('\n',1);assert key.strip() not in result,key;result[key.strip()]=clean(body)
 return result
extensions=chunkmap(ROOT/'scripts/leaf-notes')
diseases=chunkmap(ROOT/'scripts/disease-notes') if (ROOT/'scripts/disease-notes').exists() else {}
allpages=[];parents={};source_titles={}
for key,body in chunkmap(ROOT/'scripts/detailed-notes').items():
 parentpath=ROOT/'medicine'/f'{key}.html';doc=html.fromstring(parentpath.read_text());title=''.join(doc.xpath('//h1')[0].itertext());source_titles[key]=title
 sections=doc.xpath('//*[@data-detailed-notes="true"]/section[contains(@class,"detailed-section")]');assert sections,key
 parents[key]=(doc,[])
 for n,original in enumerate(sections,1):
  extkey=f'{key}#{n:02}';assert extkey in extensions,extkey
  section=deepcopy(original);h2=section.xpath('./h2')[0]
  label=''.join(h2.itertext())
  for badge in h2.xpath('./span'):
   label=label.replace(''.join(badge.itertext()),'',1);h2.remove(badge)
  label=label.strip();assert label,extkey
  section.set('id','core');h2.text='核心整理｜'+label
  slug=f'{key}-section-{n:02}';content=[section];extra,_,_,_=render(extensions[extkey]);content.extend(html.fragments_fromstring(extra))
  parents[key][1].append({'slug':slug,'title':label,'kind':'逐項詳讀'})
  allpages.append({'slug':slug,'title':label,'parent':key,'content':content,'kind':'逐項詳讀'})
assert len(extensions)==sum(len(v[1]) for v in parents.values()),'orphan extension'
for key,body in diseases.items():
 # key syntax: parent-topic#disease-slug | page title
 mapping,title=key.split(' | ',1);parent,slug=mapping.split('#',1);assert parent in parents,parent
 fullslug=parent.rsplit('/',1)[0]+'/'+slug
 content,_,_,_=render(body)
 item={'slug':fullslug,'title':title,'kind':'疾病詳讀'};parents[parent][1].append(item)
 allpages.append({**item,'parent':parent,'content':html.fragments_fromstring(content)})
for entry in allpages:
 parent=entry['parent'];source=parents[parent][0];doc=deepcopy(source);slug=entry['slug'];filename=slug.split('/')[-1]+'.html';cat=slug.split('/')[0];parentfile=parent.split('/')[-1]+'.html'
 doc.xpath('//title')[0].text=entry['title']+'｜'+CATS[cat]+'｜臨床醫學知識整理';doc.xpath('//h1')[0].text=entry['title']
 doc.xpath('//meta[@name="description"]')[0].set('content',entry['title']+'：講義架構、機轉解釋、判讀與國考辨析。')
 hero=doc.xpath('//div[@class="page-hero"]/p')[0];hero.text='從核心概念讀到臨床判讀，再回到同章比較。'+entry['kind']+'｜'+source_titles[parent]
 crumb=doc.xpath('//div[@class="breadcrumbs"]')[0];crumb.clear();crumb.set('class','breadcrumbs');crumb.text=''
 crumb.append(html.fragment_fromstring(f'<span><a href="../../index.html">首頁</a> › <a href="../index.html">內科</a> › <a href="index.html">{E(CATS[cat])}</a> › <a href="{parentfile}">{E(source_titles[parent])}</a> › {E(entry["title"])}</span>'))
 for n in doc.xpath('//*[@data-leaf-directory]'):n.getparent().remove(n)
 for n in doc.xpath('//*[contains(@class,"updated")]'):n.text='逐項擴充 2026/10/06；各來源版本見頁尾'
 article=doc.xpath('//div[@class="article-body"]')[0];article.clear();article.set('class','article-body')
 article.append(html.fragment_fromstring(f'<div class="back-row"><a href="{parentfile}">回本章目錄</a><a href="index.html">回{E(CATS[cat])}</a></div>'))
 for node in entry['content']:article.append(deepcopy(node))
 refs=deepcopy(source.xpath('//*[@id="references"]')[0]);refs.set('class','source-note')
 for n in refs.xpath('.//*[@data-detailed-notes]'):n.getparent().remove(n)
 for p in refs.xpath('./p'):
  if '本頁對應章節' in ''.join(p.itertext()):p.text=''.join(p.itertext()).replace('本頁對應章節導讀位置為','本章來源範圍為')+' 此為整章範圍，不代表這一小項逐頁對應。'
  elif '核對日' in ''.join(p.itertext()):p.text='依講義主題重寫與補充病生理、判讀、治療選擇及考點；不逐字轉載講義或指引，不聲稱收錄全部歷屆試題。'
 sources=json.loads((ROOT/'scripts/detail-sources.json').read_text()).get(parent,[])
 if parent=='cardiology/heart-failure-structure':sources=sources+[['ACC/AHA 2020 瓣膜病：本頁介入架構採此版本','https://www.acc.org/Guidelines/Guidelines/2020/12/17/14/24/Valvular-Heart-Disease']]
 refs.append(html.fragment_fromstring('<div><h3>來源用途與版本</h3><p>講義提供基礎與國考主題；下列指引支援其對應診斷或治療主題，並非每一個段落都來自同一份指引。舊題與新版門檻不同時，按題目指定版本作答。</p>'+('<ul>'+''.join(f'<li><a href="{E(url,quote=True)}" target="_blank" rel="noopener">{E(label)}</a></li>' for label,url in sources)+'</ul>' if sources else '<p>本小項補充基礎病理、判讀與鑑別；個別疾病的治療更新請併讀本章列出的指引補充。</p>')+'</div>'));article.append(refs)
 items=parents[parent][1];pos=next(i for i,x in enumerate(items) if x['slug']==slug);links=[]
 for i,label in [(pos-1,'上一項'),(pos+1,'下一項')]:
  if 0<=i<len(items):links.append(f'<a href="{items[i]["slug"].split("/")[-1]}.html"><small>{label}</small>{E(items[i]["title"])}</a>')
 article.append(html.fragment_fromstring('<nav class="chapter-pager" aria-label="章節閱讀順序">'+''.join(links)+'</nav>'))
 nav=doc.xpath('//nav[@aria-label="本頁章節"]')[0];nav.clear();nav.set('aria-label','本頁章節')
 for i,node in enumerate(article.xpath('./section')):
  node.set('id',f'chapter-{i+1:02}');h=node.xpath('./h2')[0];label=''.join(h.itertext());nav.append(html.fragment_fromstring(f'<a href="#{node.get("id")}">{E(label)}</a>'))
 nav.append(html.fragment_fromstring('<a href="#references">來源與版本</a>'))
 save(ROOT/'medicine'/f'{slug}.html',doc)
for key,(doc,items) in parents.items():
 for old in doc.xpath('//*[@data-leaf-directory]'):old.getparent().remove(old)
 main=doc.xpath('//main')[0];layout=main.xpath('./div[@class="reading-layout"]')[0]
 # Preserve old anchors in a clearly labeled reference view; directory is primary.
 layout.set('id','combined-reference')
 grid=''.join(f'<a class="topic-link leaf-topic" href="{x["slug"].split("/")[-1]}.html"><span class="tag">{E(x["kind"])} {i+1:02}</span><h3>{E(x["title"])}</h3><span class="go">開啟獨立詳讀頁 →</span></a>' for i,x in enumerate(items))
 block=html.fragment_fromstring(f'<section class="section leaf-directory" data-leaf-directory="true" id="chapter-directory"><h2>本章閱讀目錄</h2><p>每個小項可獨立閱讀；逐項詳讀補充機轉與判讀，疾病詳讀再展開個別病變。依序讀完後，可用下方整章比較表交叉複習。</p><div class="topic-grid">{grid}</div><p><a href="#combined-reference">整章比較與原整理 ↓</a></p></section>');main.insert(main.index(layout),block)
 for stamp in doc.xpath('//*[contains(@class,"updated")]'):stamp.text='分頁與目錄更新 2026/10/06；來源版本見頁尾'
 hero=doc.xpath('//div[@class="page-hero"]/p')[0];hero.text=f'本章包含 {len(items)} 個獨立詳讀頁，依基礎、判讀與疾病排列；整章比較整理保留於目錄下方。'
 save(ROOT/'medicine'/f'{key}.html',doc)
for cat in CATS:
 path=ROOT/'medicine'/cat/'index.html';doc=html.fromstring(path.read_text());sec=doc.xpath('//section[contains(@class,"book-topics")]')[0]
 for old in sec.xpath('./div[@data-leaf-directory]'):sec.remove(old)
 count=sum(len(items) for key,(_,items) in parents.items() if key.startswith(cat+'/'))
 sec.xpath('./p')[0].text=f'先選章節，再進入個別小項。本科目前有 {count} 個独立詳讀頁；原章節保留比較表與整體整理。'
 for a in sec.xpath('.//a[contains(@class,"topic-link")]'):
  key=cat+'/'+a.get('href','').replace('.html','')
  if key in parents:
   a.xpath('./p')[0].text=f'{len(parents[key][1])} 個小項：'+ '、'.join(x['title'] for x in parents[key][1][:3])+'等。';a.xpath('./span')[0].text='查看章節目錄 →'
 save(path,doc)
path=ROOT/'medicine/book-index.html';doc=html.fromstring(path.read_text());sec=doc.xpath('//*[@id="detailed-chapters"]')[0]
sec.xpath('./p')[0].text=f'28 章依序展開為 {len(allpages)} 個小項與疾病詳讀頁。從各章目錄進入；頁內目錄定位段落，前後項導覽協助連續閱讀。'
for row in sec.xpath('.//tbody/tr'):
 a=row.xpath('./td[2]/a')[0];key=a.get('href').split('#')[0].replace('.html','');a.set('href',key+'.html#chapter-directory');row.xpath('./td[3]')[0].text=f'{len(parents[key][1])} 個獨立詳讀頁'
save(path,doc)
search=[]
for path in sorted(ROOT.rglob('*.html')):
 doc=html.fromstring(path.read_text());main=doc.xpath('//main')
 if not main:continue
 rel=path.relative_to(ROOT).as_posix();parts=rel.split('/');specialty=CATS.get(parts[1],'') if len(parts)>2 and parts[0]=='medicine' else ''
 title=' '.join(doc.xpath('//h1')[0].itertext()) if doc.xpath('//h1') else ''.join(doc.xpath('//title/text()'))
 trail=' '.join(doc.xpath('//div[contains(@class,"breadcrumbs")]')[0].itertext()) if doc.xpath('//div[contains(@class,"breadcrumbs")]') else '首頁'
 for node in main[0].xpath('.//aside|.//footer|.//script|.//button|.//div[contains(@class,"page-tools")]|.//nav[@class="chapter-pager"]'):node.getparent().remove(node)
 search.append(dict(url=rel,title=title,trail=trail,specialty=specialty,text=re.sub(r'\s+',' ',' '.join(main[0].itertext())).strip()))
(ROOT/'assets/search-index.json').write_text(json.dumps(search,ensure_ascii=False,separators=(',',':')))
report=dict(sectionPages=len(extensions),diseasePages=len(diseases),leafPages=len(allpages),newCharacters=sum(len(s) for s in extensions.values())+sum(len(s) for s in diseases.values()),searchPages=len(search),pages=[{k:v for k,v in x.items() if k!='content'} for x in allpages])
(ROOT/'scripts/leaf-pages-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='pages'},ensure_ascii=False))
# Detailed chapters are authoritative overrides; preserve them on future rebuilds.
import subprocess,sys
if (ROOT/'scripts/build_textbook_pages.py').exists():
 subprocess.run([sys.executable,str(ROOT/'scripts/build_textbook_pages.py')],check=True)

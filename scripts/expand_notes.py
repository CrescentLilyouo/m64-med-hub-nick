from pathlib import Path
from html import escape as E
from lxml import html
from opencc import OpenCC
import json,re
ROOT=Path(__file__).resolve().parents[1]
cc=OpenCC('s2twp')
CATS={'cardiology':'心臟內科','pulmonology':'胸腔內科','gastroenterology':'腸胃肝膽','endocrinology':'內分泌與新陳代謝','nephrology':'腎臟內科','infectious-disease':'感染科','rheumatology':'免疫風濕科','hematology':'血液科','oncology':'腫瘤科','family-medicine':'家庭醫學'}
def txt(v):
 v=cc.convert(v)
 v=re.sub(r'([\u3400-\u9fff])([A-Za-z])',r'\1 \2',v)
 return E(re.sub(r'([A-Za-z])([\u3400-\u9fff])',r'\1 \2',v))
def render(body):
 out=[];sections=[];sid=None;sub=0;lines=body.strip().splitlines();i=0;tables=0;cases=0
 while i<len(lines):
  line=lines[i].strip()
  if not line:i+=1;continue
  if line.startswith('## '):
   if sid:out.append('</section>')
   sid=f'detail-{len(sections)+1:02}';sub=0;label=line[3:];sections.append((sid,label,[]))
   out.append(f'<section class="section detailed-section" id="{sid}"><h2><span class="chapter-number">詳讀 {len(sections):02}</span>{txt(label)}</h2>')
  elif line.startswith('### '):
   sub+=1;subid=f'{sid}-part-{sub:02}';label=line[4:];sections[-1][2].append((subid,label));out.append(f'<h3 id="{subid}">{txt(label)}</h3>')
  elif line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    rows.append([v.strip() for v in lines[i].strip().strip('|').split('|')]);i+=1
   assert all(len(r)==len(rows[0]) for r in rows),rows
   out.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+txt(v)+'</th>' for v in rows[0])+'</tr></thead><tbody>')
   out.extend('<tr>'+''.join('<td>'+txt(v)+'</td>' for v in row)+'</tr>' for row in rows[1:])
   out.append('</tbody></table></div><p class="table-hint">寬表格可左右捲動</p>');tables+=1;continue
  elif line.startswith('- '):
   out.append('<ul class="study-list">')
   while i<len(lines) and lines[i].strip().startswith('- '):out.append('<li>'+txt(lines[i].strip()[2:])+'</li>');i+=1
   out.append('</ul>');continue
  elif line.startswith('? '):
   assert i+1<len(lines) and lines[i+1].strip().startswith('! ')
   cases+=1;out.append('<details class="quiz detailed-quiz"><summary>'+txt(line[2:])+'</summary><div class="answer"><strong>判讀與解題：</strong><p>'+txt(lines[i+1].strip()[2:])+'</p></div></details>');i+=1
  else:out.append('<p>'+txt(line)+'</p>')
  i+=1
 if sid:out.append('</section>')
 return ''.join(out),sections,tables,cases
SOURCES=json.loads((ROOT/'scripts/detail-sources.json').read_text())
summary=[]
for md in sorted((ROOT/'scripts/detailed-notes').glob('*.md')):
 for chunk in re.split(r'^@@ ',md.read_text(),flags=re.M)[1:]:
  key,body=chunk.split('\n',1);key=key.strip();path=ROOT/'medicine'/f'{key}.html';doc=html.fromstring(path.read_text());article=doc.xpath('//div[contains(concat(" ",@class," ")," article-body ")]')[0]
  for old in doc.xpath('//*[@data-detailed-notes]'):old.getparent().remove(old)
  content,sections,tables,cases=render(body);first=article.xpath('./section[@id="s1"]')[0]
  block=html.fragment_fromstring('<div class="detailed-notes" data-detailed-notes="true">'+content+'</div>');article.insert(article.index(first),block)
  quick=html.fragment_fromstring('<section class="section quick-review" id="quick-review" data-detailed-notes="true"><h2>比較表速覽</h2><p>讀完上方詳解後，用以下表格複習診斷差異與治療重點。</p></section>');article.insert(article.index(first),quick)
  nav=doc.xpath('//nav[@aria-label="本頁章節"]')[0];links=['<div class="toc-label">逐節詳讀</div>']
  for sid,label,subs in sections:
   links.append(f'<a href="#{sid}">{txt(label)}</a>');links.extend(f'<a class="toc-subsection" href="#{subid}">{txt(label2)}</a>' for subid,label2 in subs)
  links.append('<div class="toc-label">複習與來源</div><a href="#quick-review">比較表速覽</a>');nav.insert(1 if nav.xpath('./a[@href="#overview"]') else 0,html.fragment_fromstring('<div data-detailed-notes="true">'+''.join(links)+'</div>'))
  for h in doc.xpath('//section[starts-with(@id,"s")]/h2'):
   if re.match(r'^s\d+$',h.getparent().get('id','')):h.text='速覽｜'+re.sub(r'^速覽｜','',h.text or '')
  for n in doc.xpath('//*[contains(concat(" ",@class," ")," updated ")]'):n.text='詳讀擴充 2026/10/05；指引版本見頁尾'
  ref=doc.xpath('//*[@id="references"]')[0];sources=SOURCES.get(key,[])
  source='<div data-detailed-notes="true"><h3>詳細補充的來源範圍</h3><p>上方「詳讀」為依原參考書主題架構重寫的基礎、臨床判讀與國考複習說明；原表格保留於速覽區。數值適用條件及舊題版本差異寫於對應小節；本頁未逐題收錄所有歷屆試題。</p>'
  if sources:source+='<ul>'+''.join(f'<li><a href="{E(url,quote=True)}" target="_blank" rel="noopener">{txt(label)}</a></li>' for label,url in sources)+'</ul>'
  source+='<p>本輪擴充：2026/10/05。指引連結支援各自的更新主題；基礎病生理、藥物機轉與鑑別依書籍架構整理。</p></div>';ref.append(html.fragment_fromstring(source))
  path.write_text('<!doctype html>\n'+html.tostring(doc,encoding='unicode',method='html'))
  summary.append(dict(key=key,title=''.join(doc.xpath('//h1')[0].itertext()),characters=len(cc.convert(body)),sections=len(sections),subsections=sum(len(s[2]) for s in sections),tables=tables,cases=cases))
indexpath=ROOT/'medicine/book-index.html';doc=html.fromstring(indexpath.read_text());main=doc.xpath('//main')[0]
for old in doc.xpath('//*[@data-detail-index]'):old.getparent().remove(old)
rows=''.join(f'<tr><td>{CATS[x["key"].split("/")[0]]}</td><td><a href="{x["key"]}.html#detail-01">{E(x["title"])}</a></td><td>{x["sections"]} 節詳讀＋{x["subsections"]} 個子節</td></tr>' for x in summary)
section=html.fragment_fromstring('<section class="section" data-detail-index="true" id="detailed-chapters"><h2>詳細筆記：閱讀順序與章節</h2><p>先讀機轉與臨床判斷，再讀檢查與治療，最後用速覽表和情境解析複習；跨章節內容可由全站搜尋定位。</p><div class="table-wrap"><table><thead><tr><th scope="col">分科</th><th scope="col">詳細主題</th><th scope="col">章節層次</th></tr></thead><tbody>'+rows+'</tbody></table></div></section>')
anchor=main.xpath('./section')[0];main.insert(main.index(anchor),section);indexpath.write_text('<!doctype html>\n'+html.tostring(doc,encoding='unicode',method='html'))
for cat in CATS:
 path=ROOT/'medicine'/cat/'index.html';doc=html.fromstring(path.read_text())
 for p in doc.xpath('//section[contains(@class,"book-topics")]/p'):p.text='每個主題先放逐節詳解，後附比較表、情境解析與來源；從機轉、診斷到治療依序閱讀。'
 path.write_text('<!doctype html>\n'+html.tostring(doc,encoding='unicode',method='html'))
search=[]
for path in sorted(ROOT.rglob('*.html')):
 doc=html.fromstring(path.read_text());main=doc.xpath('//main')
 if not main:continue
 rel=path.relative_to(ROOT).as_posix();parts=rel.split('/');specialty=CATS.get(parts[1],'') if len(parts)>2 and parts[0]=='medicine' else ''
 title=' '.join(doc.xpath('//h1')[0].itertext()) if doc.xpath('//h1') else ''.join(doc.xpath('//title/text()'))
 trail=' '.join(doc.xpath('//div[contains(@class,"breadcrumbs")]')[0].itertext()) if doc.xpath('//div[contains(@class,"breadcrumbs")]') else '首頁'
 for n in main[0].xpath('.//aside|.//footer|.//script|.//button|.//div[contains(@class,"page-tools")]'):n.getparent().remove(n)
 search.append(dict(url=rel,title=title,trail=trail,specialty=specialty,text=re.sub(r'\s+',' ',' '.join(main[0].itertext())).strip()))
(ROOT/'assets/search-index.json').write_text(json.dumps(search,ensure_ascii=False,separators=(',',':')))
report={'topics':len(summary),'newCharacters':sum(x['characters'] for x in summary),'newSections':sum(x['sections'] for x in summary),'newSubsections':sum(x['subsections'] for x in summary),'newTables':sum(x['tables'] for x in summary),'newCases':sum(x['cases'] for x in summary),'searchPages':len(search),'pages':summary}
(ROOT/'scripts/detailed-notes-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='pages'},ensure_ascii=False))

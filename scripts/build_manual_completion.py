"""Append authored, topic-specific teaching to the preserved GI handbook pages."""
from pathlib import Path
from lxml import html
from html import escape as E
import re,json
ROOT=Path(__file__).resolve().parents[1]
ns={'__file__':str(ROOT/'scripts/expand_notes.py')};exec((ROOT/'scripts/expand_notes.py').read_text().split('SOURCES=')[0],ns)
render,cc=ns['render'],ns['cc']
def chunks(folder):
 out={}
 for p in (ROOT/'scripts'/folder).glob('*.md'):
  for part in re.split(r'^@@ ',p.read_text(),flags=re.M)[1:]:
   k,b=part.split('\n',1);out[k.strip()]=b
 return out
manual=chunks('manual-completion');clinical=chunks('clinical-completion');disease=chunks('disease-completion')
map_to={
 'symptoms/abdominal-pain-nausea':'exam-luminal#06','symptoms/bowel-habit':'exam-luminal#04',
 'symptoms/dysphagia':'exam-luminal#01','symptoms/gi-bleeding':'exam-luminal#03',
 'symptoms/jaundice-ascites':'exam-hepatobiliary#02','diagnostics/liver-labs':'exam-hepatobiliary#01',
 'hepatology/viral-hepatitis':'exam-hepatobiliary#02','hepatology/cirrhosis':'exam-hepatobiliary#03',
 'pancreas/pancreatitis':'exam-hepatobiliary#04','luminal/upper-gi':'exam-luminal#02',
 'luminal/ibd-ibs':'exam-luminal#05'}
for target,key in map_to.items():manual['gastroenterology/'+target]=clinical['gastroenterology/'+key]
sources=json.loads((ROOT/'scripts/detail-sources.json').read_text())
stats=[]
for key,body in manual.items():
 path=ROOT/'medicine'/f'{key}.html';assert path.exists(),key
 doc=html.fromstring(path.read_text());main=doc.xpath('//main')[0]
 for old in doc.xpath('//*[@data-manual-completion]'):old.getparent().remove(old)
 article=doc.xpath('//div[@class="article-body"]');article=article[0] if article else main
 markup,sections,tables,cases=render(cc.convert(body));block=html.fragment_fromstring('<div data-manual-completion="true" class="manual-completion"><div class="source-note"><strong>講義與指引整合補充 · 2026/10/06</strong><p>以下將病房手冊的主題接到國考判讀、鑑別、治療與情境。上方手冊內容保留原版用途；含舊年份的藥物與門檻需與下列版本併讀。</p></div>'+markup+'</div>')
 for el in block.iter():
  if el.get('id'):el.set('id','integration-'+el.get('id'))
 refkey='gastroenterology/exam-luminal' if '/luminal/' in key or '/symptoms/' in key else 'gastroenterology/exam-hepatobiliary'
 refs='<section class="source-note"><h3>國考與手冊接續閱讀</h3><p><a href="../'+refkey.split('/')[-1]+'.html">國考同科章節目錄</a> · <a href="../manual-index.html">手冊章節與原頁碼</a></p><p>版本核對：手冊第二十版 114/08/08；藥物更新由指定主題指引支援，不代表每段都由同一來源得出。</p><ul>'+''.join('<li><a target="_blank" rel="noopener" href="'+E(u,quote=True)+'">'+E(t)+'</a></li>' for t,u in sources[refkey])+'</ul></section>'
 block.append(html.fragment_fromstring(refs))
 footer=article.xpath('./footer|./a[contains(@class,"to-top")]')
 article.insert(article.index(footer[0]) if footer else len(article),block)
 nav=doc.xpath('//nav[@aria-label="本頁章節"]')
 if nav:
  for sid,title,_ in sections:
   a=html.fragment_fromstring('<a data-manual-completion="true" href="#integration-'+sid+'">'+E(title)+'</a>');nav[0].append(a)
 for stamp in doc.xpath('//*[contains(concat(" ",@class," ")," updated " )]'):stamp.text='講義與手冊整合 2026/10/06；原版與更新來源分列'
 if nav:
  summary=nav[0].getparent().xpath('./summary')
  if summary:summary[0].text='本頁目錄 · '+str(len(nav[0].xpath('./a')))+' 節'
 path.write_text('<!doctype html>\n'+html.tostring(doc,encoding='unicode',method='html'))
 stats.append(dict(slug=key,characters=len(body),sections=len(sections),tables=tables,cases=cases))
expected={p.relative_to(ROOT/'medicine').with_suffix('').as_posix() for p in (ROOT/'medicine/gastroenterology').glob('*/*.html') if p.name!='index.html'}
assert {x['slug'] for x in stats}==expected,expected-{x['slug'] for x in stats}
(ROOT/'scripts/manual-completion-summary.json').write_text(json.dumps({'pages':stats,'count':len(stats),'characters':sum(x['characters'] for x in stats)},ensure_ascii=False,indent=2))
print('GI handbook integration:',len(stats),'pages')

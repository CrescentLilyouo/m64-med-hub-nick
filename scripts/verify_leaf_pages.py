from pathlib import Path
from lxml import html
from urllib.parse import urlsplit,unquote
import json
root=Path(__file__).resolve().parents[1];errors=[];docs={}
for p in root.rglob('*.html'):
 d=html.fromstring(p.read_text());docs[p.resolve()]=d
 ids=d.xpath('//@id')
 if len(ids)!=len(set(ids)):errors.append(f'duplicate ids: {p}')
 if not ''.join(d.xpath('//h1')[0].itertext()).strip():errors.append(f'empty h1: {p}')
 if len(d.xpath('//h1'))!=1:errors.append(f'h1 count: {p}')
for p,d in docs.items():
 for node in d.xpath('//*[@href or @src]'):
  for attr in ['href','src']:
   ref=node.get(attr)
   if not ref:continue
   url=urlsplit(ref)
   if url.scheme or url.netloc:continue
   target=(p.parent/unquote(url.path)).resolve() if url.path else p
   if target.is_dir():target/= 'index.html'
   if not target.exists():errors.append(f'missing target {p.name}: {ref}')
   elif url.fragment and target in docs and not docs[target].xpath('//*[@id=$id]',id=unquote(url.fragment)):errors.append(f'missing fragment {p.name}: {ref}')
report=json.loads((root/'scripts/leaf-pages-summary.json').read_text());index=json.loads((root/'assets/search-index.json').read_text());urls={x['url'] for x in index}
for entry in report['pages']:
 p=root/'medicine'/f'{entry["slug"]}.html';d=docs[p.resolve()]
 if 'medicine/'+entry['slug']+'.html' not in urls:errors.append('not searchable:'+entry['slug'])
 if len(d.xpath('//div[@class="article-body"]/section'))<3:errors.append('too few sections:'+entry['slug'])
 if not d.xpath('//*[@id="references"]//a[starts-with(@href,"http")]') and entry['kind']=='疾病詳讀':errors.append('missing guideline source:'+entry['slug'])
home=docs[(root/'index.html').resolve()]
assert not home.xpath('//*[@data-open-search]')
print(json.dumps(dict(htmlPages=len(docs),leafPages=report['leafPages'],errors=errors),ensure_ascii=False,indent=2));assert not errors

"""Apply authored long chapters, an honest coverage inventory, and the search index.

Run directly, or automatically after build_leaf_pages.py. Does not rewrite the
homepage or promote page counts to an examination coverage percentage.
"""
from pathlib import Path
from copy import deepcopy
from html import escape as E
from lxml import html
import json, re

ROOT = Path(__file__).resolve().parents[1]
ns = {'__file__': str(ROOT / 'scripts/expand_notes.py')}
exec((ROOT / 'scripts/expand_notes.py').read_text().split('SOURCES=')[0], ns)
render, CATS, cc = ns['render'], ns['CATS'], ns['cc']
metadata = json.loads((ROOT / 'scripts/textbook-chapters.json').read_text())
chapters = metadata['chapters']
report = json.loads((ROOT / 'scripts/leaf-pages-summary.json').read_text())
expanded = {c['slug']: c for c in chapters}

def save(path, doc):
    path.write_text('<!doctype html>\n' + html.tostring(doc, encoding='unicode', method='html'))

def fragment(markup):
    return html.fragment_fromstring(markup)

def table(heads, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th scope="col">' + E(h) + '</th>' for h in heads) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + c + '</td>' for c in row) + '</tr>' for row in rows) + '</tbody></table></div>'

stats = []
for c in chapters:
    path = ROOT / 'medicine' / (c['slug'] + '.html')
    doc = html.fromstring(path.read_text())
    body = cc.convert((ROOT / 'scripts/textbook-notes' / (path.stem + '.md')).read_text())
    markup, sections, tables, cases = render(body)
    article = doc.xpath('//div[@class="article-body"]')[0]
    back = deepcopy(article.xpath('./div[@class="back-row"]')[0])
    pager = deepcopy(article.xpath('./nav[@class="chapter-pager"]')[0])
    article.clear(); article.set('class', 'article-body'); article.append(back)
    article.append(fragment('<div class="source-note textbook-status"><strong>詳細章節稿 · 2026/10/06</strong><p>已展開定義、機轉、診斷、鑑別、治療、追蹤與情境解析。歷屆題目逐題對照及全考綱涵蓋仍待核對。</p><a href="../coverage.html">查看各科內容與缺漏 →</a></div>'))
    for node in html.fragments_fromstring(markup):
        article.append(node)
    refs = '<section class="section source-note" id="references"><h2>來源、版本與尚待補充</h2><p>教材架構：使用者提供的《國考分科詳解—醫學（三）》2020 年版，' + E(c['book']) + '。PDF 頁碼從封面計算。基礎機轉與國考概念依教材重新組織並補充解釋，不逐字轉載。</p><p>本章指引核對日：2026/10/06。數值更新依下列指定版本；不同文件的診斷及解除標準分開說明。情境解析為原創練習。</p><ul>' + ''.join('<li><a href="' + E(url, quote=True) + '" target="_blank" rel="noopener">' + E(label) + '</a></li>' for label, url in c['sources']) + '</ul><p>仍待補充：完整歷屆題號與更正答案逐題對照、兒童及特殊族群的獨立章節，以及新版正式考綱逐項映射。詳細稿不等於全國考內容已完成。</p></section>'
    article.append(fragment(refs)); article.append(pager)
    nav = doc.xpath('//nav[@aria-label="本頁章節"]')[0]
    nav.clear(); nav.set('aria-label', '本頁章節')
    for sid, label, subs in sections:
        nav.append(fragment('<a href="#' + sid + '">' + E(label) + '</a>'))
        for subid, subtitle in subs:
            nav.append(fragment('<a class="toc-subsection" href="#' + subid + '">' + E(subtitle) + '</a>'))
    nav.append(fragment('<a href="#references">來源與待補充</a>'))
    doc.xpath('//h1')[0].text = c['title']
    doc.xpath('//title')[0].text = c['title'] + '｜國考詳細章節｜臨床醫學知識整理'
    doc.xpath('//div[@class="page-hero"]/p')[0].text = '依講義與指引整合的成人詳細章節：從機轉、檢查判讀到治療理由與國考情境。'
    doc.xpath('//meta[@name="description"]')[0].set('content', c['title'] + '：定義、病因、機轉、診斷、鑑別、治療、追蹤、版本差異與國考推理。')
    for n in doc.xpath('//*[contains(concat(" ", @class, " "), " updated ")]'):
        n.text = '詳細章節更新 2026/10/06；來源版本見頁尾'
    save(path, doc)
    stats.append({'slug': c['slug'], 'characters': len(body), 'sections': len(sections), 'subsections': sum(len(s[2]) for s in sections), 'tables': tables, 'cases': cases})

# Keep authoring and status links visible in the existing hierarchy.
for c in chapters:
    parent = ROOT / 'medicine' / (c['parent'] + '.html')
    doc = html.fromstring(parent.read_text())
    link = doc.xpath('//*[@data-leaf-directory]//a[@href=$href]', href=c['slug'].split('/')[-1] + '.html')[0]
    link.xpath('./span[contains(@class,"tag")]')[0].text = '詳細章節稿'
    link.xpath('./h3')[0].text = c['title']
    link.xpath('./span[contains(@class,"go")]')[0].text = '機轉 → 診斷 → 治療 → 情境解析 →'
    save(parent, doc)

index = html.fromstring((ROOT / 'medicine/index.html').read_text())
for n in index.xpath('//*[@data-coverage-link]'):
    n.getparent().remove(n)
hero = index.xpath('//div[@class="page-hero"]')[0]
hero.addnext(fragment('<section class="section" data-coverage-link="true"><h2>國考複習：閱讀範圍與詳細章節</h2><p>目前以四冊醫學（三）講義為基礎。從分科进入章節；先看涵蓋清單，確認哪些已補成詳細稿、哪些仍需擴寫。</p><div class="back-row"><a href="coverage.html">各科內容與缺漏</a><a href="endocrinology/diabetic-ketoacidosis.html">DKA 詳細章</a><a href="endocrinology/hyperosmolar-hyperglycemic-state.html">HHS 詳細章</a><a href="endocrinology/adrenal-insufficiency.html">腎上腺不足詳細章</a></div></section>'))
save(ROOT / 'medicine/index.html', index)

# Overall scope uses the official subject groupings. Detailed 116 syllabus
# mapping remains explicitly pending while the official document is unavailable.
scope = [
    ['醫學（三）', '內科、家庭醫學及相關臨床案例、醫學倫理', '四冊講義已有章節與分頁；本輪 3 項詳細稿，其餘逐章補深。'],
    ['醫學（四）', '小兒科、皮膚科、神經科、精神科', '尚未建立完整教材；不得以內科相關頁面視為全科已涵蓋。'],
    ['醫學（五）', '外科、骨科、泌尿科', '尚未建立完整教材。'],
    ['醫學（六）', '麻醉科、眼科、耳鼻喉科、婦產科、復健科', '尚未建立完整教材。'],
]
gaps = {
    'cardiology': '高血壓與次發性病因、ACS、完整 ECG 判讀、心衰竭分型與藥物、感染性心內膜炎、心肌及心包病的完整診療流程。',
    'pulmonology': '氣喘、COPD 分階治療、肺炎與結核、各類 ILD、肺栓塞機率與抗凝、ARDS 與呼吸器、肺癌及肋膜疾病。',
    'gastroenterology': '逐一核對國考講義與消化手冊：食道、胃腸、IBD、出血、病毒性肝炎、肝硬化、肝膽胰疾病；現有手冊分頁不代表逐項考綱已對齊。',
    'endocrinology': '下一批：Graves、甲狀腺低下、甲狀腺炎、甲狀腺風暴、Cushing、原發性醛固酮過多。仍需補垂體、糖尿病常規治療與慢性併發症、鈣骨與性腺。',
    'nephrology': '完整酸鹼例題、各類電解質與 RTA、AKI／CKD、個別腎絲球疾病、透析適應症與併發症、移植。',
    'infectious-disease': '各感染症候群、採檢與抗菌決策、藥物劑量適用情境、HIV／病毒、黴菌及寄生蟲、耐藥與特殊宿主。',
    'rheumatology': 'SLE、RA、個別結締組織病、血管炎、脊椎關節炎、結晶關節炎、過敏與免疫學。',
    'hematology': '各類貧血、溶血與抹片判讀、ITP／TTP／DIC／HIT、血栓、白血病與淋巴瘤、骨髓瘤及輸血。',
    'oncology': '腫瘤治療類別與副作用、個別癌症分期與治療、腫瘤急症、標記與副腫瘤；跨外科章節仍需補齊。',
    'family-medicine': '臺灣預防與篩檢、疫苗、統計與研究方法、溝通、老人、職業與旅遊、社區及緩和照護、倫理與法規。',
}
coverage = deepcopy(index)
main = coverage.xpath('//main')[0]
footer = deepcopy(main.xpath('./footer')[0]); main.clear(); main.set('id', 'main-content'); main.set('class', 'page-shell'); main.set('tabindex', '-1')
main.append(fragment('<div class="breadcrumbs"><a href="../index.html">首頁</a> › <a href="index.html">內科</a> › 國考內容與缺漏</div>'))
main.append(fragment('<div class="page-hero"><h1>國考複習網：內容與缺漏清單</h1><p>以現有臨床講義為起點，逐章補成可連續閱讀的詳細教材。這份清單區分「已有分頁」和「內容已充分展開」。</p></div>'))
main.append(fragment('<section class="section"><h2>目前可以怎麼讀</h2><p>先由分科目錄進入主題，再選獨立小項；詳細章依定義、機轉、診斷、鑑別、治療、追蹤與情境解析排列。頁面目錄可定位，前後項導覽可接續閱讀。</p><p><strong>本輪已展開 3 個詳細章節稿，其餘 175 個講義小項仍需補深。</strong>這是現有 178 個分頁的編寫狀態，並非全國考完成率。消化手冊與其他既有頁面另保留於原分類。</p><p>尚未完成所有科目、所有疾病或所有歷屆題目；詳細稿也仍待逐題對照與完整考綱映射。</p></section>'))
cards = ''.join('<a class="topic-link" href="' + c['slug'] + '.html"><span class="tag">詳細章節稿</span><h3>' + E(c['title']) + '</h3><p>11 節：從病理機轉、判讀到治療與原創情境解析。</p><span class="go">開始詳讀 →</span></a>' for c in chapters)
main.append(fragment('<section class="section"><h2>本轮詳細章節</h2><div class="topic-grid">' + cards + '</div></section>'))
main.append(fragment('<section class="section" id="exam-scope"><h2>第二階段科目範圍與尚缺教材</h2><p>目前工作範圍依現有醫學（三）臨床講義與二階補充要求建立。下表依考選部 115 年考試科目表列出科目群；不是新版命題大綱的全部細項。</p>' + table(['科目群', '官方科目範圍', '網站目前狀態'], [[E(x) for x in r] for r in scope]) + '<p>考選部公告醫師新版命題大綱自民國 116 年第一次考試起實施。官方細項文件尚待完整取得與逐項比對，因此此頁不宣稱已完成 116 年大綱對照。</p><p><a href="https://wwwc.moex.gov.tw/main/exam/FileHandler.ashx?File=3997&amp;MCode=7744&amp;PCode=5113&amp;f=115&amp;t=P" target="_blank" rel="noopener">考選部 115 年科目表</a> · <a href="https://wwwc.moex.gov.tw/main/content/wfrmcontentlink4.aspx?inc_url=1&amp;menu_id=154&amp;sub_menu_id=613" target="_blank" rel="noopener">官方命題大綱與適用版本</a></p></section>'))
main.append(fragment('<section class="section"><h2>怎樣才算章節已充分整理</h2><p>逐項核對以下內容，再判定完成。頁數、字數及分頁數只用來管理內容，不代替涵蓋審查。</p>' + table(['檢查面向', '章節應有內容'], [[E(a), E(b)] for a, b in [
    ('知識', '定義、分類、病因、危險因子與可推理的病生理。'),
    ('辨識與診斷', '症狀、理學、檢驗與影像、條件限制、鑑別及下一步。'),
    ('治療', '第一線與替代、急慢性流程、藥物機轉與禁忌、例外與監測。'),
    ('後續', '併發症、預後、預防與追蹤，特殊族群另列適用範圍。'),
    ('國考', '原創情境解析、考點與錯誤選項理由；歷屆題号另逐題核對。'),
    ('來源', '講義對應、指引版本、數值差異及仍未核對的內容。'),
]]) + '</section>'))
for cat, label in CATS.items():
    entries = [p for p in report['pages'] if p['slug'].startswith(cat + '/')]
    rows = []
    for p in entries:
        title = expanded[p['slug']]['title'] if p['slug'] in expanded else p['title']
        rows.append(['<a href="' + p['slug'] + '.html">' + E(title) + '</a>', '詳細章節稿；仍待全題對照' if p['slug'] in expanded else '基礎稿；待詳細擴寫'])
    main.append(fragment('<section class="section" id="scope-' + cat + '"><h2>' + E(label) + '</h2><p><a href="' + cat + '/index.html">進入本科目錄 →</a></p><p><strong>待補方向：</strong>' + E(gaps[cat]) + '</p><details class="coverage-list"><summary>展開 ' + str(len(entries)) + ' 項內容與編寫狀態</summary>' + table(['現有小項', '編寫狀態'], rows) + '</details></section>'))
main.append(fragment('<section class="section source-note"><h2>教材盤點與核對狀態</h2><p>四冊《國考分科詳解—醫學（三）》2020 年版已建立分類與 PDF 章節範圍，<a href="book-index.html">查看四冊對照</a>。書內收錄較舊考題，不能視為含所有新年度題目。</p><p>《11409 消化內科工作手冊》已有 <a href="gastroenterology/manual-index.html">手冊主題目錄</a>；與國考講義的逐節合併、重複內容及缺漏仍待逐项核對。</p><p>更新日期：2026/10/06。科目表與大綱作為範圍來源，疾病指引在各詳細章末列出。這份清單會隨實際內容更新，不以新增頁面自動升級為完成。</p></section>'))
main.append(footer)
coverage.xpath('//title')[0].text = '國考內容與缺漏｜臨床醫學知識整理'
coverage.xpath('//meta[@name="description"]')[0].set('content', '國考複習網的教材範圍、逐項編寫狀態、詳細章節與尚待補齊的科目。')
# Normalize Chinese in the newly authored inventory, preserving original file URLs.
save(ROOT / 'medicine/coverage.html', html.fromstring(cc.convert(html.tostring(coverage, encoding='unicode'))))

for path in [ROOT / 'medicine/book-index.html', ROOT / 'medicine/endocrinology/index.html']:
    doc = html.fromstring(path.read_text())
    for n in doc.xpath('//*[@data-textbook-link]'):
        n.getparent().remove(n)
    doc.xpath('//div[@class="page-hero"]')[0].addnext(fragment('<div class="source-note" data-textbook-link="true"><a href="' + ('coverage.html' if path.parent.name == 'medicine' else '../coverage.html') + '">查看詳細章節、教材範圍與待補內容 →</a></div>'))
    save(path, doc)

search = []
for path in sorted(ROOT.rglob('*.html')):
    doc = html.fromstring(path.read_text()); mains = doc.xpath('//main')
    if not mains: continue
    rel = path.relative_to(ROOT).as_posix(); parts = rel.split('/')
    specialty = CATS.get(parts[1], '') if len(parts) > 2 and parts[0] == 'medicine' else ''
    title = ' '.join(doc.xpath('//h1')[0].itertext())
    crumbs = doc.xpath('//div[contains(@class,"breadcrumbs")]')
    trail = ' '.join(crumbs[0].itertext()) if crumbs else '首頁'
    for node in mains[0].xpath('.//aside|.//footer|.//script|.//button|.//div[contains(@class,"page-tools")]|.//nav[@class="chapter-pager"]'):
        node.getparent().remove(node)
    search.append(dict(url=rel, title=title, trail=trail, specialty=specialty, text=re.sub(r'\s+', ' ', ' '.join(mains[0].itertext())).strip()))
(ROOT / 'assets/search-index.json').write_text(json.dumps(search, ensure_ascii=False, separators=(',', ':')))
summary = {'date': metadata['reviewDate'], 'expandedChapters': len(chapters), 'characters': sum(s['characters'] for s in stats), 'sections': sum(s['sections'] for s in stats), 'tables': sum(s['tables'] for s in stats), 'cases': sum(s['cases'] for s in stats), 'searchPages': len(search), 'chapters': stats}
(ROOT / 'scripts/textbook-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False))

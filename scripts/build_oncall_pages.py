"""Build the source classification and cross-links, without republishing old orders."""
from pathlib import Path
from html import escape as E
import json,re
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=[
('renal','腎臟、水電解質與酸鹼','nephrology',['nephrology/sodium/index.html','nephrology/acid-base.html','nephrology/potassium-minerals.html','nephrology/renal-syndromes.html'],[
('hypernatremia','高血鈉','3','水分流失與鈉負荷增加；體液狀態判讀；血漿滲透壓與尿鈉；尿崩症；神經症狀；補液與矯正監測','內分泌、體液調控'),
('hyponatremia','低血鈉','4–5','滲透壓分類；低、正常與高血容量；尿液檢查；SIADH；症狀嚴重度；矯正原則與併發症','胸腔、內分泌、藥物'),
('hyperkalemia','高血鉀','6–7','假性高血鉀；腎排泄障礙；藥物與細胞內外移動；心電圖；心肌保護；鉀移入細胞與移除體內鉀','心血管、藥物'),
('hypokalemia','低血鉀','8–9','腸胃道與腎臟流失；細胞內移動；低血鎂；肌肉與心電圖表現；口服與靜脈補鉀；追蹤','心血管、腸胃、藥物'),
('acidemia','酸血症','25–27','血氣判讀；代謝性與呼吸性酸中毒；陰離子間隙；代償反應；病因鑑別與處理','胸腔、糖尿病急症'),
('alkalemia','鹼血症','28–29','代謝性與呼吸性鹼中毒；嘔吐與利尿劑；氯與鉀缺乏；過度換氣；病因處理','胸腔、腸胃、藥物'),
('polyuria','多尿、頻尿與尿失禁','53–55','多尿與頻尿區別；滲透性利尿與尿崩症；泌尿道感染；尿路阻塞；急迫性、壓力性、溢流性與功能性尿失禁','內分泌、泌尿、老年'),
('oliguria','尿量減少','93–95','導尿管與尿滯留；腎前性、腎性與腎後性病因；灌流與體液評估；急性腎損傷；檢查與監測','泌尿、循環、重症')]),
('endocrine','內分泌與代謝','endocrinology',['endocrinology/diabetes.html','endocrinology/diabetes-section-01.html','endocrinology/diabetes-section-02.html','endocrinology/diabetic-ketoacidosis.html','endocrinology/hyperosmolar-hyperglycemic-state.html','endocrinology/calcium-metabolism.html'],[
('hyperglycemia','高血糖','10–11','高血糖原因；藥物與感染誘因；DKA；HHS；補液、胰島素與鉀離子；治療監測','感染、腎臟、酸鹼'),
('hypoglycemia','低血糖','12–13','胰島素與降血糖藥；進食不足；肝腎功能問題；自律神經與神經低血糖症狀；矯正及復發觀察','神經、肝腎功能、藥物'),
('hypercalcemia','高血鈣','14–17','副甲狀腺與惡性腫瘤；藥物；鈣值判讀；腎臟與神經症狀；補液及降鈣治療','腫瘤、腎臟、骨代謝'),
('hypocalcemia','低血鈣','18–19','副甲狀腺與維生素 D；腎病與低血鎂；抽搐與心電圖變化；鈣補充；病因處理','腎臟、神經、心血管')]),
('cardiovascular','心血管與循環','cardiology',['cardiology/hypertension-lipids.html','cardiology/ecg-arrhythmia.html','cardiology/ischemic-heart-disease.html','cardiology/heart-failure-structure.html','infectious-disease/syndrome-sepsis.html'],[
('syncope','暈厥','33–35','暈厥與其他意識喪失的區別；反射性與姿勢性原因；心因性暈厥；病史與心電圖；危險徵象','神經、藥物'),
('shock','低血壓與休克','63–65','低血容量、分布性、心因性與阻塞性原因；灌流評估；補液與升壓；病因處理','感染、出血、過敏、重症'),
('hypertension','高血壓','71–73','血壓量測與誘因；急性標的器官損傷；高血壓急症；腦部、心臟與主動脈情境；降壓藥','神經、腎臟、妊娠'),
('arrhythmia','心率與心律異常','74–81','規則與不規則心搏過速；心房顫動與撲動；SVT 與 VT；心搏過緩；房室傳導阻滯；藥物與電解質原因','電解質、藥物、急救'),
('chest-pain','胸痛','102–105','急性冠心症；主動脈剝離；肺栓塞與氣胸；食道破裂；心包膜炎；消化道及肌肉骨骼原因','胸腔、腸胃、急診')]),
('respiratory','胸腔與呼吸','pulmonology',['pulmonology/physiology-airways.html','pulmonology/infection-interstitial.html','pulmonology/critical-pleura-cancer.html','cardiology/heart-failure-structure.html'],[
('dyspnea','呼吸困難','45–52','嚴重度與氧合評估；呼吸衰竭；心衰竭；肺栓塞；肺炎；氣喘與 COPD；檢查及初步處理','心血管、感染、重症')]),
('hematology','血液、凝血與輸血','hematology',['hematology/anemia.html','hematology/coagulation-thrombosis.html','hematology/malignancy-transfusion.html'],[
('anemia','貧血','20–21','出血、溶血與生成不足；血球與網狀紅血球判讀；急慢性區別；輸血評估','腸胃出血、腎臟、腫瘤'),
('coagulopathy','凝血異常','22–24','血小板、凝血因子與血管問題；PT 與 aPTT 判讀；肝病與抗凝血藥；出血評估','肝臟、感染、藥物'),
('transfusion','輸血反應','30–32','溶血性、發熱性及過敏反應；呼吸症狀；輸血相關循環負荷與肺損傷鑑別；反應發生後的評估','胸腔、過敏、感染')]),
('gastrointestinal','腸胃與腹部','gastroenterology',['gastroenterology/exam-luminal.html','gastroenterology/exam-hepatobiliary.html','gastroenterology/manual-index.html'],[
('gi-bleeding','消化道出血','86–88','上下消化道出血；吐血與黑便；循環穩定度；潰瘍與靜脈曲張；檢查、內視鏡與藥物','循環、血液、肝臟'),
('diarrhea','腹瀉','96–97','急慢性區別；感染與藥物；抗生素相關腹瀉；脫水與電解質；糞便檢查及處理','感染、腎臟、藥物'),
('abdominal-pain','腹痛','106–109','疼痛位置與病史；腹膜刺激徵象；穿孔與腸缺血；膽道感染、胰臟炎與闌尾炎；泌尿與婦科原因','外科、感染、泌尿、婦科')]),
('infection','感染與發燒','infectious-disease',['infectious-disease/syndrome-sepsis.html','infectious-disease/bacteria-antibiotics.html','pulmonology/infection-interstitial.html'],[
('fever','發燒','89–92','感染部位尋找；病史與身體檢查；培養與影像；抗感染處理；藥物及其他非感染性原因','胸腔、泌尿、腹腔、皮膚、循環')]),
('neurology','神經與精神急症',None,['endocrinology/diabetes.html','family-medicine/communication-geriatric-palliative.html','gastroenterology/hepatic-encephalopathy.html'],[
('stroke','中風','36–39','發病時間；神經學評估；缺血性與出血性中風；影像；急性治療；血壓與併發症','心血管、復健'),
('seizures','癲癇／抽搐','56–57','發作辨識；代謝與藥物原因；急性發作處理；癲癇重積狀態；發作後評估','內分泌、電解質、藥物'),
('headache','頭痛','82–85','雷擊性頭痛；蛛網膜下腔出血；中樞神經感染；顱內病灶；偏頭痛、緊縮型與叢發性頭痛','感染、急診'),
('confusion','混亂／意識下降','98–101','系統性病因鑑別；低血糖與缺氧；藥物與中毒；感染與器官衰竭；譫妄；神經學與代謝評估','內分泌、感染、肝腎、老年'),
('combativeness','躁動／失控行為','110','身體疾病與精神疾病鑑別；譫妄；藥物與戒斷；溝通；安全評估及處置','精神、老年、藥物')]),
('allergy','皮膚、過敏與免疫','rheumatology',['rheumatology/allergy-immunology.html'],[
('rash','搔癢、皮疹與蕁麻疹','40–44','皮疹型態；藥物反應；蕁麻疹；血管性水腫；全身性過敏反應；嚴重皮膚反應辨識','皮膚、藥物、循環')]),
('limb','肢體、血管與軟組織',None,['hematology/coagulation-thrombosis.html','rheumatology/arthritis-vasculitis.html','infectious-disease/syndrome-sepsis.html'],[
('leg-pain','腿痛','58–62','急性動脈缺血；深部靜脈栓塞；腔室症候群；壞死性軟組織感染；感染性關節炎；痛風、退化性關節炎與坐骨神經痛','血管、感染、骨科、風濕')]),
('medications','值班常用藥與症狀控制','family-medicine',['family-medicine/communication-geriatric-palliative.html','gastroenterology/exam-luminal.html'],[
('symptom-medications','安眠藥、瀉劑與止痛藥','66–70','安眠藥（第 66 頁）：失眠評估、藥物種類與注意事項；瀉劑（第 67–68 頁）：便秘原因、藥物分類與選擇；止痛藥（第 69–70 頁）：疼痛評估、藥物分類、副作用與監測','老年、腸胃、藥理')])]
OUT=ROOT/'medicine/oncall';OUT.mkdir(exist_ok=True)
NOTICE='<div class="source-note"><p>來源：Oncall-survival-guide-Ver2，2020 年版，共 111 頁。頁碼為原 PDF 頁碼。</p><p>本區已完成 33 主題的分類與內容範圍整理。用藥劑量與急救流程尚未逐項核對新版指引；相關連結通往既有複習章節，各頁更新範圍請看其來源說明。</p></div>'
def links(paths):
 s=[]
 for p in paths:
  d=html.fromstring((ROOT/'medicine'/p).read_text());title=d.xpath('string(//h1)')
  s.append(f'<li><a href="../{E(p)}">{E(title)}</a></li>')
 return '<ul>'+''.join(s)+'</ul>'
def page(title,desc,body,crumb=''):
 return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)}｜臨床醫學知識整理</title><meta name="description" content="{E(desc)}"><link rel="stylesheet" href="../../assets/site.css"><script defer src="../../assets/site.js"></script></head><body id="top"><a class="skip-link" href="#main-content">跳至主要內容</a><header class="site-header"><div class="inner"><a class="site-title" href="../../index.html">臨床醫學知識整理</a><div class="header-actions"><nav aria-label="主要導覽"><a href="../../index.html">首頁</a><a href="../index.html">內科</a><a href="index.html">值班手冊</a></nav><button type="button" class="search-launch" data-open-search aria-haspopup="dialog">搜尋<kbd>⌘ / Ctrl K</kbd></button></div></div></header><main id="main-content" class="page-shell" tabindex="-1"><div class="breadcrumbs"><a href="../../index.html">首頁</a> › <a href="../index.html">內科</a> › {crumb or '值班手冊分類'}</div><div class="page-hero"><h1>{E(title)}</h1><p>{E(desc)}</p></div>{body}{NOTICE}<div class="back-row"><a href="index.html">全部分類</a><a href="../index.html">回內科</a></div><footer class="footer">臨床醫學教育與複習用途；實際診療請依病人情境、指引版本與院內規範。</footer></main></body></html>'''
cards=[];rows=[];catalog=[]
for slug,title,dept,related,topics in CATEGORIES:
 cards.append(f'<a class="topic-link" href="{slug}.html"><h3>{E(title)}</h3><p>{E("、".join(t[1] for t in topics))}</p><span class="go">{len(topics)} 個主題・進入分類 →</span></a>')
 toc='<section class="section"><h2>本分類主題</h2><ul>'+''.join(f'<li><a href="#{s}">{E(t)}</a>（第 {p} 頁）</li>' for s,t,p,_,_ in topics)+'</ul></section>'
 sections=[]
 for s,t,p,scope,tags in topics:
  catalog.append(dict(category=slug,id=s,title=t,pages=p,scope=scope.split('；'),tags=tags.split('、')))
  sections.append(f'<section class="section" id="{s}"><h2>{E(t)}</h2><p><strong>原書位置：</strong>第 {p} 頁。<strong>跨科標籤：</strong>{E(tags)}。</p><h3>原章內容範圍</h3><ul>'+''.join(f'<li>{E(x)}</li>' for x in scope.split('；'))+'</ul></section>')
  rows.append(f'<tr><td>{E(title)}</td><td><a href="{slug}.html#{s}">{E(t)}</a></td><td>{p}</td><td>{E(tags)}</td></tr>')
 body=toc+''.join(sections)+'<section class="section" id="related"><h2>相關複習章節</h2><p>下列章節補充本分類涉及的疾病與機轉；涵蓋範圍依各章內容為準。</p>'+links(related)+'</section>'
 (OUT/(slug+'.html')).write_text(page(title+'｜值班手冊分類','從症狀與異常數值，找到原章內容範圍、頁碼與相關複習章節。',body,f'<a href="index.html">值班手冊分類</a> › {E(title)}'))
 assert len(topics)>0
 if dept:
  path=ROOT/'medicine'/dept/'index.html';d=html.fromstring(path.read_text())
  for n in d.xpath('//*[@data-oncall-link]'): n.getparent().remove(n)
  markup=f'<section class="section" data-oncall-link="true"><h2>值班手冊：症狀與急症分類</h2><p>{E("、".join(t[1] for t in topics))}。保留原書頁碼與內容範圍，連到相關複習章節。</p><div class="back-row"><a href="../oncall/{slug}.html">{E(title)}分類 →</a><a href="../oncall/index.html">全部 33 個主題</a></div></section>'
  d.xpath('//div[@class="page-hero"]')[0].addnext(html.fragment_fromstring(markup))
  path.write_text('<!doctype html>\n'+html.tostring(d,encoding='unicode',method='html'))
assert len(catalog)==33 and len({x['id'] for x in catalog})==33
body='<section class="section"><h2>依分類閱讀</h2><p>先選分類，再選主題；每項列出原書頁碼、內容範圍與跨科標籤。第 1–2 頁為目錄與前言，第 111 頁為參考資料。</p><div class="topic-grid">'+''.join(cards)+'</div></section><section class="section" id="all-topics"><h2>33 主題與頁碼對照</h2><div class="table-wrap"><table><thead><tr><th scope="col">主分類</th><th scope="col">主題</th><th scope="col">原書頁碼</th><th scope="col">跨科標籤</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></section>'
(OUT/'index.html').write_text(page('值班手冊分類｜33 主題','11 大類，整合症狀、異常數值、急症與常用藥章節的查閱入口。',body))
(ROOT/'scripts/oncall-catalog.json').write_text(json.dumps(dict(source='Oncall-survival-guide-Ver2.pdf',edition='2020',pages=111,status='classification-and-crosslinks',topics=catalog),ensure_ascii=False,indent=2)+'\n')
p=ROOT/'medicine/index.html';d=html.fromstring(p.read_text())
for n in d.xpath('//*[@data-oncall-link]'): n.getparent().remove(n)
d.xpath('//div[@class="page-hero"]')[0].addnext(html.fragment_fromstring('<section class="section" data-oncall-link="true"><h2>值班手冊：症狀、急症與用藥分類</h2><p>2020 年版手冊已依 11 大類整理全部 33 個主題，附原書頁碼、內容範圍及相關複習章節。</p><div class="back-row"><a href="oncall/index.html">進入值班手冊分類 →</a><a href="oncall/index.html#all-topics">33 主題與頁碼對照</a><a href="oncall/medications.html">常用藥分類</a></div></section>'))
p.write_text('<!doctype html>\n'+html.tostring(d,encoding='unicode',method='html'))
# Refresh the same searchable-page schema as the main builder.
search=[]
for p in sorted(ROOT.rglob('*.html')):
 d=html.fromstring(p.read_text());m=d.xpath('//main')
 if not m:continue
 rel=p.relative_to(ROOT).as_posix();old=json.loads((ROOT/'assets/search-index.json').read_text()) if not search else None
 if old is not None: specialties={x['url']:x.get('specialty','') for x in old}
 for n in m[0].xpath('.//aside|.//footer|.//script|.//button|.//div[contains(@class,"page-tools")]|.//nav[@class="chapter-pager"]'):n.getparent().remove(n)
 crumbs=d.xpath('//div[contains(@class,"breadcrumbs")]')
 search.append(dict(url=rel,title=d.xpath('string(//h1)'),trail=' '.join(crumbs[0].itertext()) if crumbs else '首頁',specialty='值班手冊' if rel.startswith('medicine/oncall/') else specialties.get(rel,''),text=re.sub(r'\s+',' ',' '.join(m[0].itertext())).strip()))
(ROOT/'assets/search-index.json').write_text(json.dumps(search,ensure_ascii=False,separators=(',',':')))
print(json.dumps(dict(categories=len(CATEGORIES),topics=len(catalog),pages=len(CATEGORIES)+1,searchPages=len(search)),ensure_ascii=False))

(() => {
  'use strict';
  const script = document.currentScript;
  const base = new URL('../', script.src);
  const main = document.querySelector('main');
  if (!main) return;
  const dialog = document.createElement('dialog');
  dialog.className = 'search-dialog';
  dialog.setAttribute('aria-labelledby', 'search-title');
  dialog.innerHTML = `<div class="search-top"><h2 id="search-title">搜尋醫學資料</h2><button type="button" class="icon-button" aria-label="關閉搜尋">關閉</button></div><form role="search"><label for="site-query">疾病、症狀或英文縮寫</label><div class="search-fields"><input type="search" id="site-query" placeholder="例如：水腫、SBP、低血鈉" autocomplete="off"><select id="search-specialty" aria-label="搜尋科別"><option value="">全部科別</option><option value="腎臟內科">腎臟內科</option><option value="消化內科">消化內科</option></select></div></form><p class="search-status" role="status" aria-live="polite"></p><div class="search-results"></div>`;
  document.body.append(dialog);
  const query = dialog.querySelector('input');
  const specialty = dialog.querySelector('select');
  const results = dialog.querySelector('.search-results');
  const status = dialog.querySelector('.search-status');
  const normalize = value => value.normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
  let indexPromise;
  let searchIndex = [];
  let loadFailed = false;
  const aliases = { '洗腎': ['透析', 'dialysis', 'krt'], '水腫': ['edema', '腹水'], '低血鈉': ['hyponatremia'], '高血鈉': ['hypernatremia'], '肝炎': ['hepatitis'], '肝硬化': ['cirrhosis'], '肝性腦病': ['encephalopathy', 'he'], '腹水': ['ascites'], '肝癌': ['hcc'], '黑便': ['melena', 'gi bleeding'] };
  function appendText(parent, tag, value, className) {
    const el = document.createElement(tag);
    el.textContent = value;
    if (className) el.className = className;
    parent.append(el);
    return el;
  }
  function render() {
    results.replaceChildren();
    const raw = normalize(query.value);
    if (!raw) {
      status.textContent = loadFailed ? '搜尋資料載入失敗。請關閉後重新開啟搜尋；仍可使用分類導覽。' : '輸入關鍵字，搜尋主題與內文。';
      if (!loadFailed) {
        const tips = document.createElement('div');
        tips.className = 'search-suggestions';
        ['水腫', '低血鈉', '腹水', '肝炎', 'SBP', 'IBD'].forEach(term => {
          const button = appendText(tips, 'button', term);
          button.type = 'button';
          button.addEventListener('click', () => { query.value = term; render(); query.focus(); });
        });
        results.append(tips);
      }
      return;
    }
    if (loadFailed) { status.textContent = '搜尋資料載入失敗。請關閉後重新開啟搜尋；仍可使用分類導覽。'; return; }
    const tokens = raw.split(' ').map(token => [token, ...(aliases[token] || [])]);
    const hits = searchIndex.filter(entry => !specialty.value || entry.specialty === specialty.value).map(entry => {
      const title = normalize(entry.title);
      const haystack = normalize(entry.title + ' ' + entry.trail + ' ' + entry.text);
      if (!tokens.every(alternatives => alternatives.some(term => haystack.includes(term)))) return null;
      const score = tokens.reduce((sum, alternatives) => sum + Math.max(...alternatives.map(term => title.includes(term) ? 10 : haystack.includes(term) ? 1 : 0)), 0);
      return { entry, score };
    }).filter(Boolean).sort((a, b) => b.score - a.score || a.entry.title.localeCompare(b.entry.title, 'zh-Hant'));
    status.textContent = hits.length ? `找到 ${hits.length} 個主題${hits.length > 30 ? '，顯示前 30 個；可增加關鍵字縮小範圍' : ''}。` : '找不到相符主題。試試較短的關鍵字或英文縮寫。';
    hits.slice(0, 30).forEach(({ entry }) => {
      const link = document.createElement('a');
      link.className = 'search-result';
      link.href = new URL(entry.url, base).href;
      appendText(link, 'span', entry.trail, 'search-trail');
      appendText(link, 'strong', entry.title);
      const text = entry.text;
      const positions = tokens.flat().map(term => normalize(text).indexOf(term)).filter(n => n >= 0);
      const start = positions.length ? Math.max(0, Math.min(...positions) - 35) : 0;
      appendText(link, 'p', (start ? '…' : '') + text.slice(start, start + 140) + (text.length > start + 140 ? '…' : ''));
      results.append(link);
    });
  }
  async function openSearch() {
    if (dialog.open) return;
    dialog.showModal();
    query.focus();
    if (!indexPromise) {
      status.textContent = '正在載入搜尋資料…';
      indexPromise = fetch(new URL('assets/search-index.json', base)).then(response => {
        if (!response.ok) throw new Error('Search index unavailable');
        return response.json();
      }).then(data => { searchIndex = data; loadFailed = false; }).catch(() => { loadFailed = true; indexPromise = null; });
      await indexPromise;
    }
    if (dialog.open) render();
  }
  document.querySelectorAll('[data-open-search]').forEach(button => button.addEventListener('click', openSearch));
  dialog.querySelector('.icon-button').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const box = dialog.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close(); } });
  dialog.querySelector('form').addEventListener('submit', event => { event.preventDefault(); render(); results.querySelector('a')?.focus(); });
  query.addEventListener('input', render);
  specialty.addEventListener('change', render);
  query.addEventListener('keydown', event => { if (event.key === 'ArrowDown') { event.preventDefault(); results.querySelector('a')?.focus(); } });
  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); openSearch(); }
  });
  document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
  document.querySelectorAll('.table-wrap').forEach((wrap, i) => {
    wrap.tabIndex = 0;
    wrap.setAttribute('role', 'region');
    wrap.setAttribute('aria-label', `資料表 ${i + 1}；寬表格可左右捲動`);
    const table = wrap.querySelector('table');
    table?.querySelectorAll('thead th').forEach(th => { if (!th.hasAttribute('scope')) th.scope = 'col'; });
    const update = () => wrap.classList.toggle('is-scrollable', wrap.scrollWidth > wrap.clientWidth + 2);
    update();
    if (window.ResizeObserver) new ResizeObserver(update).observe(wrap);
  });
  const toc = document.querySelector('.reading-nav details');
  if (toc) {
    const media = window.matchMedia('(min-width: 1100px)');
    const update = () => { toc.open = media.matches; };
    update();
    media.addEventListener('change', update);
    const links = [...toc.querySelectorAll('a')];
    const sections = links.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1)))).filter(Boolean);
    let scheduled = false;
    const highlight = () => {
      scheduled = false;
      let current = sections[0];
      sections.forEach(section => { if (section.getBoundingClientRect().top <= 150) current = section; });
      links.forEach(link => {
        const active = current && decodeURIComponent(link.hash.slice(1)) === current.id;
        link.classList.toggle('active', Boolean(active));
        if (active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
      });
    };
    window.addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(highlight); } }, { passive: true });
    links.forEach(link => link.addEventListener('click', () => { if (!media.matches) toc.open = false; }));
    highlight();
  }
  document.querySelectorAll('.site-header nav a').forEach(link => {
    if (new URL(link.href).pathname === location.pathname) link.setAttribute('aria-current', 'page');
  });
})();

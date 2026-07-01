
(() => {
  const input = document.getElementById('search-input');
  const button = document.getElementById('search-button');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  let index = [];

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  }

  function snippet(text, query) {
    const clean = String(text || '').replace(/\s+/g, ' ');
    const pos = clean.toLowerCase().indexOf(query.toLowerCase());
    const start = Math.max(0, pos - 64);
    return clean.slice(start, start + 170) + (clean.length > start + 170 ? '...' : '');
  }

  function runSearch() {
    const q = input.value.trim();
    results.innerHTML = '';
    if (!q) {
      status.textContent = '请输入关键词。';
      return;
    }
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    const found = index
      .map((item) => {
        const hay = `${item.title} ${item.chapter} ${item.summary} ${item.text}`.toLowerCase();
        const score = terms.reduce((sum, term) => sum + (hay.includes(term) ? 1 : 0), 0);
        return { item, score };
      })
      .filter((row) => row.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 30);
    status.textContent = `找到 ${found.length} 条结果。`;
    results.innerHTML = found.map(({ item }) => `
      <a class="search-result" href="${item.url}">
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.chapter)}</span>
        <p>${escapeHtml(snippet(`${item.summary} ${item.text}`, q))}</p>
      </a>
    `).join('');
  }

  fetch('assets/data/search-index.json')
    .then((res) => res.json())
    .then((data) => {
      index = data;
      const params = new URLSearchParams(location.search);
      const q = params.get('q');
      if (q) {
        input.value = q;
        runSearch();
      } else {
        status.textContent = `索引已加载，共 ${index.length} 条。`;
      }
    })
    .catch(() => {
      status.textContent = '搜索索引加载失败。';
    });

  button?.addEventListener('click', runSearch);
  input?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') runSearch();
  });
})();

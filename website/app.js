(() => {
  const readerMenu = document.querySelector('[data-reader-menu]');
  if (readerMenu && window.matchMedia('(min-width: 761px)').matches) readerMenu.open = true;
  const menu = document.querySelector('[data-menu]');
  const nav = document.querySelector('.nav');
  if (menu && nav) {
    const mobile = window.matchMedia('(max-width: 760px)');
    const setMenu = (open, restoreFocus = false) => {
      nav.classList.toggle('open', open);
      menu.setAttribute('aria-expanded', String(open));
      menu.textContent = open ? '关闭' : '导航';
      if (restoreFocus && mobile.matches) menu.focus();
    };
    menu.addEventListener('click', () => setMenu(!nav.classList.contains('open')));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && mobile.matches && nav.classList.contains('open')
          && (event.target === menu || nav.contains(event.target))) {
        event.preventDefault();
        setMenu(false, true);
      }
    });
    document.addEventListener('focusin', event => {
      if (mobile.matches && nav.classList.contains('open') && event.target !== menu
          && !nav.contains(event.target)) setMenu(false);
    });
    mobile.addEventListener('change', () => {
      const wasFocused = nav.contains(document.activeElement);
      setMenu(false, wasFocused);
    });
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setMenu(false)));
  }
  const query = document.querySelector('[data-region-query]');
  const group = document.querySelector('[data-region-group]');
  const status = document.querySelector('[data-region-status]');
  const cards = [...document.querySelectorAll('[data-region]')];
  const filter = () => {
    const q = (query?.value || '').trim().toLocaleLowerCase();
    let count = 0;
    cards.forEach(card => {
      const matched = (!q || card.dataset.search.toLocaleLowerCase().includes(q))
        && (!group?.value || card.dataset.group === group.value)
        && (!status?.value || card.dataset.status === status.value);
      card.hidden = !matched;
      count += Number(matched);
    });
    document.querySelectorAll('.region-group').forEach(section => {
      section.hidden = ![...section.querySelectorAll('[data-region]')].some(card => !card.hidden);
    });
    const text = document.querySelector('[data-region-count]');
    if (text) text.textContent = `当前显示 ${count} 个国家或地区。核验深度与缺口见各地区正文。`;
    const empty = document.querySelector('[data-region-empty]');
    if (empty) empty.hidden = count !== 0;
  };
  [query,group,status].forEach(control => control?.addEventListener('input', filter));
  const resetFilters = document.querySelector('[data-region-reset]');
  resetFilters?.addEventListener('click', () => {
    if (query) query.value = '';
    if (group) group.value = '';
    if (status) status.value = '';
    filter();
    query?.focus();
  });
  if (cards.length) filter();
  // Historical source review: dynamic freshness priority is not a live policy check.
  const sourceCards = [...document.querySelectorAll('[data-source]')];
  const sourceQuery = document.querySelector('[data-source-query]');
  const sourceMode = document.querySelector('[data-source-filter]');
  const sourceExport = document.querySelector('[data-source-export]');
  const requiresReview = card => {
    if (card.dataset.sourceStatus !== 'verified') return true;
    const value = card.dataset.sourceDate || '';
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return true;
    const date = Date.parse(value + 'T00:00:00Z');
    const now = Date.now();
    return !Number.isFinite(date) || new Date(date).toISOString().slice(0, 10) !== value
      || date > now || now - date > 30 * 86400000;
  };
  const filterSources = () => {
    if (!sourceCards.length) return [];
    const q = (sourceQuery?.value || '').trim().toLocaleLowerCase();
    const mode = sourceMode?.value || 'all';
    const visible = sourceCards.filter(card => {
      const match = (!q || (card.dataset.search || '').toLocaleLowerCase().includes(q))
        && (mode === 'all' || (mode === 'partial' ? card.dataset.sourceStatus !== 'verified' : requiresReview(card)));
      card.hidden = !match;
      return match;
    });
    const count = document.querySelector('[data-source-count]');
    if (count) count.textContent = '当前显示 ' + visible.length + ' / ' + sourceCards.length + ' 条；其中 ' + visible.filter(requiresReview).length + ' 条建议复核。';
    const empty = document.querySelector('[data-source-empty]');
    if (empty) empty.hidden = visible.length > 0;
    if (sourceExport) sourceExport.disabled = visible.length === 0;
    return visible;
  };
  [sourceQuery, sourceMode].forEach(input => input?.addEventListener('input', filterSources));
  document.querySelector('[data-source-reset]')?.addEventListener('click', () => {
    if (sourceQuery) sourceQuery.value = '';
    if (sourceMode) sourceMode.value = 'all';
    filterSources();
    sourceQuery?.focus();
  });
  sourceExport?.addEventListener('click', () => {
    const visible = filterSources();
    if (!visible.length) return;
    const lines = [
      '中国留学生求职：来源复核清单（历史台账，非最新规则认证）',
      '生成日期：' + new Date().toISOString().slice(0, 10),
      '导出条数：' + visible.length,
      '注意：以官网最新岗位/官方资格原文为准；不得据此推断申请一定成功。',
      '微信：AIPMAndy  个人官网：https://metaver.vip/  公司官网：https://www.a6no1.cn/  服务：https://metaver.vip/services',
      '',
      ...visible.flatMap(card => [
        card.id + ' | ' + (card.dataset.sourceTitle || ''),
        '历史核验日期：' + (card.dataset.sourceDate || '未记录') + ' | 状态：' + (card.dataset.sourceStatus || '未知'),
        '官方原文：' + (card.dataset.sourceUrl || '未记录'),
        '复核：□ 页面可访问 □ 适用年份/地区 □ 资格 □ 当前职位状态 □ 更新记录日期',
        '',
      ]),
    ];
    const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'career-source-review-list.txt';
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  if (sourceCards.length) filterSources();
  document.querySelectorAll('[data-copy-wechat]').forEach(button => button.addEventListener('click', async () => {
    const target = document.querySelector('[data-copy-status]');
    try {
      await navigator.clipboard.writeText('AIPMAndy');
      if (target) target.textContent = '已复制微信号 AIPMAndy';
    } catch {
      if (target) target.textContent = '微信号：AIPMAndy。可长按选择并复制。';
    }
  }));
  document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
})();

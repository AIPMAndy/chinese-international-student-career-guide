(() => {
  const readerMenu = document.querySelector('[data-reader-menu]');
  if (readerMenu && window.matchMedia('(min-width: 761px)').matches) readerMenu.open = true;
  const menu = document.querySelector('[data-menu]');
  const nav = document.querySelector('.nav');
  menu?.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    menu.setAttribute('aria-expanded', String(open));
    menu.textContent = open ? '关闭' : '导航';
  });
  nav?.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    nav.classList.remove('open');
    menu?.setAttribute('aria-expanded', 'false');
    if (menu) menu.textContent = '导航';
  }));
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
  if (cards.length) filter();
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

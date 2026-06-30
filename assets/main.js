
(() => {
  const progress = document.getElementById('reading-progress');
  const backTop = document.getElementById('back-top');
  const sidebar = document.getElementById('sidebar');
  const tocToggle = document.getElementById('toc-toggle');
  const links = Array.from(document.querySelectorAll('.toc-link'));
  const pageAnchors = links
    .map((link) => document.getElementById(link.getAttribute('href').slice(1)))
    .filter(Boolean);

  function updateProgress() {
    const doc = document.documentElement;
    const max = doc.scrollHeight - window.innerHeight;
    const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
    progress.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    backTop.classList.toggle('visible', window.scrollY > 900);
  }

  window.addEventListener('scroll', updateProgress, { passive: true });
  window.addEventListener('resize', updateProgress);
  updateProgress();

  backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  if (tocToggle && sidebar) {
    tocToggle.addEventListener('click', () => {
      const open = sidebar.classList.toggle('open');
      tocToggle.setAttribute('aria-expanded', String(open));
    });
    links.forEach((link) => {
      link.addEventListener('click', () => {
        sidebar.classList.remove('open');
        tocToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  const byId = new Map(links.map((link) => [link.getAttribute('href').slice(1), link]));
  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (!visible) return;
    links.forEach((link) => link.classList.remove('active'));
    const active = byId.get(visible.target.id);
    if (active) active.classList.add('active');
  }, { rootMargin: '-15% 0px -75% 0px', threshold: 0.01 });

  pageAnchors.forEach((anchor) => observer.observe(anchor));

  document.querySelectorAll('a[href^="#ref-"], a.citation').forEach((link) => {
    link.addEventListener('click', () => {
      const id = link.getAttribute('href').slice(1);
      const target = document.getElementById(id);
      if (!target) return;
      target.classList.add('flash');
      window.setTimeout(() => target.classList.remove('flash'), 1100);
    });
  });
})();

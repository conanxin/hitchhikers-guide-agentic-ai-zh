
(() => {
  const links = Array.from(document.querySelectorAll('.outline-link'));
  if (!links.length) return;
  const byId = new Map(links.map((link) => [decodeURIComponent(link.getAttribute('href').slice(1)), link]));
  const headings = Array.from(document.querySelectorAll('.article-body h2[id], .article-body h3[id]'));
  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (!visible) return;
    links.forEach((link) => link.classList.remove('active'));
    byId.get(visible.target.id)?.classList.add('active');
  }, { rootMargin: '-18% 0px -72% 0px', threshold: 0.01 });
  headings.forEach((heading) => observer.observe(heading));
})();

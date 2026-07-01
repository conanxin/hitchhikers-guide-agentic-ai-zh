
(() => {
  const navToggle = document.getElementById('nav-toggle');
  const topnav = document.getElementById('topnav');
  const leftNav = document.getElementById('left-nav');
  const backTop = document.getElementById('back-top');

  navToggle?.addEventListener('click', () => {
    const topOpen = topnav?.classList.toggle('open');
    if (leftNav && document.body.classList.contains('article-page')) {
      leftNav.classList.toggle('open');
    }
    navToggle.setAttribute('aria-expanded', String(Boolean(topOpen || leftNav?.classList.contains('open'))));
  });

  leftNav?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      leftNav.classList.remove('open');
      navToggle?.setAttribute('aria-expanded', 'false');
    });
  });

  backTop?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
})();

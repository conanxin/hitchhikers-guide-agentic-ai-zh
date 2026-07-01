
(() => {
  const progress = document.getElementById('reading-progress');
  const backTop = document.getElementById('back-top');
  function updateProgress() {
    if (!progress) return;
    const doc = document.documentElement;
    const max = doc.scrollHeight - window.innerHeight;
    const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
    progress.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    backTop?.classList.toggle('visible', window.scrollY > 700);
  }
  window.addEventListener('scroll', updateProgress, { passive: true });
  window.addEventListener('resize', updateProgress);
  updateProgress();
})();

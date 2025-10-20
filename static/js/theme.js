(function(){
  const btn = document.getElementById('theme-toggle');
  if(!btn) return;

  function setTheme(t){
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('theme', t); } catch(e){}
    btn.setAttribute('aria-pressed', t === 'dark');
  }

  // nie nadpisujemy wyboru z boot-skrpytu
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  setTheme(current);

  btn.addEventListener('click', function(){
    const cur = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(cur === 'dark' ? 'light' : 'dark');
  });
})();

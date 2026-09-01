document.addEventListener('DOMContentLoaded', function(){
  // Navbar scroll state
  const header = document.querySelector('.site-header');
  if(header){
    const onScroll = () => header.classList.toggle('scrolled', window.scrollY > 20);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive:true });
  }

  // Mobile menu
  const navToggle = document.getElementById('nav-toggle');
  const siteNav = document.getElementById('site-nav');
  if(navToggle && siteNav){
    const close = ()=>{ navToggle.setAttribute('aria-expanded','false'); siteNav.classList.remove('open'); document.body.style.overflow=''; }
    const open = ()=>{ navToggle.setAttribute('aria-expanded','true'); siteNav.classList.add('open'); document.body.style.overflow='hidden'; }
    navToggle.addEventListener('click', ()=> navToggle.getAttribute('aria-expanded') === 'true' ? close() : open());
    siteNav.addEventListener('click', (e)=>{ if(e.target.tagName === 'A') close(); });
    document.addEventListener('click', (e)=>{ if(!siteNav.contains(e.target) && !navToggle.contains(e.target)) close(); });
    document.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') close(); });
  }

  // FAQ accordion
  document.querySelectorAll('.faq-item').forEach(item=>{
    const btn = item.querySelector('.faq-question');
    btn.addEventListener('click', ()=> item.classList.toggle('open'));
    btn.addEventListener('keydown', (e)=>{ if(e.key==='Enter' || e.key===' ') item.classList.toggle('open'); });
  });
});

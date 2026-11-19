document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', event => {
      if (window.innerWidth <= 800 && sidebar.classList.contains('open') &&
          !sidebar.contains(event.target) && !toggle.contains(event.target)) sidebar.classList.remove('open');
    });
  }
  document.querySelectorAll('.flash').forEach(flash => {
    window.setTimeout(() => { if (flash.isConnected) flash.remove(); }, 5500);
  });
});

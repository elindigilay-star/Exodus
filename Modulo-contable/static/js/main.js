document.addEventListener('DOMContentLoaded', function () {
  var toggles = document.querySelectorAll('.nav-toggle');
  toggles.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!expanded));
      var submenu = document.getElementById(btn.getAttribute('aria-controls'));
      if (submenu) submenu.classList.toggle('open');
    });
  });

  var activeSub = document.querySelector('.submenu a.active');
  if (activeSub) {
    var submenu = activeSub.closest('.submenu');
    var toggle = submenu && submenu.parentElement.querySelector('.nav-toggle');
    if (submenu) submenu.classList.add('open');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'true');
      toggle.classList.add('active');
    }
  }
});

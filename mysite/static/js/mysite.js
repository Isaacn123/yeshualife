(function () {
  "use strict";

  function isMobileNav() {
    return window.matchMedia("(max-width: 767.98px)").matches;
  }

  function dropdownOptions() {
    if (isMobileNav()) {
      return {
        autoClose: "outside",
        display: "static",
      };
    }
    return {
      autoClose: "outside",
    };
  }

  function initNavbarDropdowns() {
    if (!window.bootstrap || !window.bootstrap.Dropdown) {
      return;
    }

    document.querySelectorAll(".navbar .dropdown-toggle").forEach(function (toggle) {
      var existing = bootstrap.Dropdown.getInstance(toggle);
      if (existing) {
        existing.dispose();
      }
      bootstrap.Dropdown.getOrCreateInstance(toggle, dropdownOptions());
    });
  }

  function initNavbarCollapse() {
    if (!window.bootstrap || !window.bootstrap.Collapse) {
      return;
    }

    var toggler = document.getElementById("ylNavbarToggler");
    var menu = document.getElementById("navbarCollapse");
    if (!toggler || !menu) {
      return;
    }

    if (toggler._ylCollapseInit) {
      return;
    }
    toggler._ylCollapseInit = true;

    var collapse = bootstrap.Collapse.getOrCreateInstance(menu, { toggle: false });

    function toggleMenu(event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      collapse.toggle();
    }

    toggler.addEventListener("click", toggleMenu);
  }

  function initNavbar() {
    initNavbarCollapse();
    initNavbarDropdowns();
  }

  document.addEventListener("DOMContentLoaded", initNavbar);
  window.addEventListener("pageshow", initNavbar);
})();

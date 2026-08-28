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

    document.querySelectorAll(".yl-site-nav .dropdown-toggle").forEach(function (toggle) {
      var existing = bootstrap.Dropdown.getInstance(toggle);
      if (existing) {
        existing.dispose();
      }
      bootstrap.Dropdown.getOrCreateInstance(toggle, dropdownOptions());
    });
  }

  function bindNavbarCollapse() {
    if (document.documentElement._ylNavbarCollapseBound) {
      return;
    }
    document.documentElement._ylNavbarCollapseBound = true;

    document.addEventListener(
      "click",
      function (event) {
        var toggler = event.target.closest(".yl-site-nav .navbar-toggler");
        if (!toggler || !window.bootstrap || !window.bootstrap.Collapse) {
          return;
        }

        var menu = document.getElementById("navbarCollapse");
        if (!menu) {
          return;
        }

        event.preventDefault();
        event.stopPropagation();
        bootstrap.Collapse.getOrCreateInstance(menu, { toggle: false }).toggle();
      },
      true
    );
  }

  function initNavbar() {
    bindNavbarCollapse();
    initNavbarDropdowns();
  }

  document.addEventListener("DOMContentLoaded", initNavbar);
  window.addEventListener("pageshow", initNavbar);
})();

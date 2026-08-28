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

  document.addEventListener("DOMContentLoaded", initNavbarDropdowns);
  window.addEventListener("pageshow", initNavbarDropdowns);
})();

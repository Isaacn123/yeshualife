(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    if (!window.bootstrap) {
      return;
    }

    document.querySelectorAll('.navbar [data-bs-toggle="dropdown"]').forEach(function (toggle) {
      toggle.addEventListener("click", function (event) {
        event.preventDefault();
      });
    });
  });
})();

(function () {
  "use strict";

  function copyPublicUrl(btn) {
    var row = btn.closest(".gs-admin-public-url");
    var input = row && row.querySelector(".gs-admin-public-url__input");
    if (!input || !input.value) return;

    function markCopied() {
      var old = btn.textContent;
      btn.textContent = "Copied!";
      window.setTimeout(function () {
        btn.textContent = old;
      }, 2000);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(input.value).then(markCopied).catch(function () {
        input.focus();
        input.select();
        try {
          document.execCommand("copy");
          markCopied();
        } catch (e) {
          /* ignore */
        }
      });
      return;
    }

    input.focus();
    input.select();
    try {
      document.execCommand("copy");
      markCopied();
    } catch (e) {
      /* ignore */
    }
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".gs-admin-copy-url");
    if (btn) copyPublicUrl(btn);
  });
})();

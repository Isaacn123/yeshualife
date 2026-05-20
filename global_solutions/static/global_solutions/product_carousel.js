(function () {
  function initProductCarousels() {
    if (typeof bootstrap === "undefined" || !bootstrap.Carousel) {
      return;
    }

    document.querySelectorAll(".gs-product-carousel").forEach(function (el) {
      var instance = bootstrap.Carousel.getOrCreateInstance(el, {
        interval: 5000,
        ride: false,
        wrap: true,
        touch: true,
        keyboard: true,
      });
      instance.cycle();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProductCarousels);
  } else {
    initProductCarousels();
  }
})();

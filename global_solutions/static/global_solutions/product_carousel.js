(function () {
  function initProductCarousels() {
    if (typeof bootstrap === "undefined" || !bootstrap.Carousel) {
      return;
    }

    document.querySelectorAll(".gs-product-carousel").forEach(function (el) {
      var isVideo = el.classList.contains("gs-video-carousel");
      var instance = bootstrap.Carousel.getOrCreateInstance(el, {
        interval: isVideo ? false : 5000,
        ride: false,
        wrap: true,
        touch: true,
        keyboard: true,
      });
      if (!isVideo) {
        instance.cycle();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProductCarousels);
  } else {
    initProductCarousels();
  }
})();

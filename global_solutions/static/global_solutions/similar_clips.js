(function () {
  "use strict";

  function attachHls(video) {
    if (!video || video.dataset.hlsBound === "true") {
      return;
    }
    var src = video.getAttribute("data-playback-src");
    if (!src || video.getAttribute("data-playback-hls") !== "true") {
      return;
    }
    video.dataset.hlsBound = "true";

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      return;
    }

    if (window.Hls && window.Hls.isSupported()) {
      var hls = new window.Hls({
        enableWorker: true,
        lowLatencyMode: false,
        backBufferLength: 30,
      });
      hls.loadSource(src);
      hls.attachMedia(video);
    }
  }

  function pauseAllVideos(root) {
    root.querySelectorAll("video").forEach(function (video) {
      try {
        video.pause();
      } catch (e) {
        /* ignore */
      }
    });
  }

  function bindControl(el, instance, handler) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      pauseAllVideos(instance._element);
      handler();
    });
  }

  function initCarousel(el) {
    if (typeof bootstrap === "undefined" || !bootstrap.Carousel) {
      return null;
    }

    var instance = bootstrap.Carousel.getOrCreateInstance(el, {
      interval: false,
      ride: false,
      wrap: true,
      touch: true,
      keyboard: true,
    });

    var prevBtn = el.querySelector(".fh-similar-clips__control.carousel-control-prev");
    var nextBtn = el.querySelector(".fh-similar-clips__control.carousel-control-next");

    if (prevBtn) {
      bindControl(prevBtn, instance, function () {
        instance.prev();
      });
    }

    if (nextBtn) {
      bindControl(nextBtn, instance, function () {
        instance.next();
      });
    }

    el.querySelectorAll(".fh-similar-clips__indicators [data-bs-slide-to]").forEach(function (btn) {
      bindControl(btn, instance, function () {
        var index = parseInt(btn.getAttribute("data-bs-slide-to"), 10);
        if (!isNaN(index)) {
          instance.to(index);
        }
      });
    });

    el.addEventListener("slide.bs.carousel", function () {
      pauseAllVideos(el);
    });

    return instance;
  }

  function initSimilarClips() {
    document.querySelectorAll(".fh-similar-clips").forEach(function (section) {
      section.querySelectorAll('video[data-playback-hls="true"][data-playback-src]').forEach(attachHls);

      var carousel = section.querySelector(".fh-similar-clips__carousel");
      if (carousel) {
        initCarousel(carousel);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSimilarClips);
  } else {
    initSimilarClips();
  }
})();

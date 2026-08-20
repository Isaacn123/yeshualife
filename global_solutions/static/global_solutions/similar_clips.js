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

    el.addEventListener("slide.bs.carousel", function () {
      pauseAllVideos(el);
    });

    el.querySelectorAll(".fh-similar-clips__control, .carousel-indicators button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        pauseAllVideos(el);
      });
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

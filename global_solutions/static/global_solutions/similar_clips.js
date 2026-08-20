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

  function bindAction(el, handler) {
    el.addEventListener(
      "click",
      function (event) {
        event.preventDefault();
        event.stopImmediatePropagation();
        handler();
      },
      true
    );
  }

  function initSimilarClipsCarousel(root) {
    if (root.dataset.fhSimilarReady === "true") {
      return;
    }
    root.dataset.fhSimilarReady = "true";

    var slides = root.querySelectorAll(".fh-similar-clips__slide");
    if (slides.length <= 1) {
      return;
    }

    var prevBtn = root.querySelector(".fh-similar-clips__control--prev");
    var nextBtn = root.querySelector(".fh-similar-clips__control--next");
    var dots = root.querySelectorAll(".fh-similar-clips__dot");
    var viewport = root.querySelector(".fh-similar-clips__viewport");
    var current = 0;

    function syncUi() {
      slides.forEach(function (slide, i) {
        var active = i === current;
        slide.classList.toggle("is-active", active);
        slide.hidden = !active;
      });

      dots.forEach(function (dot, i) {
        var active = i === current;
        dot.classList.toggle("is-active", active);
        if (active) {
          dot.setAttribute("aria-current", "true");
        } else {
          dot.removeAttribute("aria-current");
        }
      });
    }

    function goTo(nextIndex) {
      var total = slides.length;
      if (total === 0) {
        return;
      }

      if (nextIndex < 0) {
        nextIndex = total - 1;
      } else if (nextIndex >= total) {
        nextIndex = 0;
      }

      if (nextIndex === current) {
        return;
      }

      pauseAllVideos(root);
      current = nextIndex;
      syncUi();

      var activeVideo = slides[current].querySelector("video");
      if (activeVideo) {
        attachHls(activeVideo);
        if (activeVideo.readyState === 0) {
          activeVideo.load();
        }
      }
    }

    if (prevBtn) {
      bindAction(prevBtn, function () {
        goTo(current - 1);
      });
    }

    if (nextBtn) {
      bindAction(nextBtn, function () {
        goTo(current + 1);
      });
    }

    dots.forEach(function (dot) {
      bindAction(dot, function () {
        var index = parseInt(dot.getAttribute("data-slide-index"), 10);
        if (!isNaN(index)) {
          goTo(index);
        }
      });
    });

    if (viewport) {
      var touchStartX = 0;
      viewport.addEventListener(
        "touchstart",
        function (event) {
          touchStartX = event.changedTouches[0].screenX;
        },
        { passive: true }
      );
      viewport.addEventListener(
        "touchend",
        function (event) {
          var delta = event.changedTouches[0].screenX - touchStartX;
          if (Math.abs(delta) < 45) {
            return;
          }
          if (delta < 0) {
            goTo(current + 1);
          } else {
            goTo(current - 1);
          }
        },
        { passive: true }
      );
    }

    root.addEventListener("keydown", function (event) {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goTo(current - 1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        goTo(current + 1);
      }
    });

    syncUi();

    var firstVideo = slides[0] && slides[0].querySelector("video");
    if (firstVideo) {
      attachHls(firstVideo);
    }
  }

  function initSimilarClips() {
    document.querySelectorAll(".fh-similar-clips").forEach(function (section) {
      section.querySelectorAll('video[data-playback-hls="true"][data-playback-src]').forEach(attachHls);
      section.querySelectorAll("[data-fh-similar-carousel]").forEach(initSimilarClipsCarousel);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSimilarClips);
  } else {
    initSimilarClips();
  }
})();

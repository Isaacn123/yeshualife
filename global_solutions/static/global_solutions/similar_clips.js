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

  function initSimilarClipsCarousel(root) {
    var slides = root.querySelectorAll(".carousel-item");
    if (!slides.length) {
      return;
    }

    var prevBtn = root.querySelector(".fh-similar-clips__control--prev");
    var nextBtn = root.querySelector(".fh-similar-clips__control--next");
    var dots = root.querySelectorAll(".fh-similar-clips__dot");
    var viewport = root.querySelector(".fh-similar-clips__viewport");
    var current = 0;

    slides.forEach(function (slide, i) {
      slide.classList.toggle("active", i === 0);
      slide.setAttribute("aria-hidden", i === 0 ? "false" : "true");
    });

    dots.forEach(function (dot, i) {
      dot.classList.toggle("active", i === 0);
      if (i === 0) {
        dot.setAttribute("aria-current", "true");
      } else {
        dot.removeAttribute("aria-current");
      }
    });

    function goTo(nextIndex) {
      if (nextIndex < 0) {
        nextIndex = slides.length - 1;
      } else if (nextIndex >= slides.length) {
        nextIndex = 0;
      }
      if (nextIndex === current) {
        return;
      }

      pauseAllVideos(root);

      slides[current].classList.remove("active");
      slides[current].setAttribute("aria-hidden", "true");
      if (dots[current]) {
        dots[current].classList.remove("active");
        dots[current].removeAttribute("aria-current");
      }

      current = nextIndex;

      slides[current].classList.add("active");
      slides[current].setAttribute("aria-hidden", "false");
      if (dots[current]) {
        dots[current].classList.add("active");
        dots[current].setAttribute("aria-current", "true");
      }

      var activeVideo = slides[current].querySelector("video");
      if (activeVideo) {
        attachHls(activeVideo);
        if (activeVideo.readyState === 0) {
          activeVideo.load();
        }
      }
    }

    function onPrev(event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      goTo(current - 1);
    }

    function onNext(event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      goTo(current + 1);
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", onPrev);
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", onNext);
    }

    dots.forEach(function (dot, index) {
      dot.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        goTo(index);
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
            onNext();
          } else {
            onPrev();
          }
        },
        { passive: true }
      );
    }

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

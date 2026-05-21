(function () {
  function attachHlsPlayback(video) {
    var src = video.getAttribute("data-playback-src");
    if (!src || video.dataset.hlsBound === "true") {
      return Promise.resolve();
    }
    video.dataset.hlsBound = "true";

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      return Promise.resolve();
    }

    if (window.Hls && window.Hls.isSupported()) {
      return new Promise(function (resolve) {
        var hls = new window.Hls({
          enableWorker: true,
          lowLatencyMode: false,
          backBufferLength: 30,
        });
        hls.on(window.Hls.Events.MEDIA_ATTACHED, function () {
          resolve();
        });
        hls.loadSource(src);
        hls.attachMedia(video);
      });
    }

    return Promise.resolve();
  }

  function setPlayerState(player, state) {
    player.classList.remove("is-playing", "is-paused", "is-ended");
    player.classList.add("is-" + state);
  }

  function showPlayOverlay(player) {
    setPlayerState(player, player.querySelector("video").ended ? "ended" : "paused");
  }

  function hidePlayOverlay(player) {
    setPlayerState(player, "playing");
  }

  function pauseAllInCarousel(carousel) {
    carousel.querySelectorAll(".gs-video-player-el").forEach(function (video) {
      video.pause();
      video.muted = true;
    });
    carousel.querySelectorAll(".gs-video-player").forEach(showPlayOverlay);
  }

  function updateCarouselSlideDescription(carousel) {
    var targetId = carousel.getAttribute("data-description-target");
    if (!targetId) return;

    var target = document.getElementById(targetId);
    if (!target) return;

    var activeItem = carousel.querySelector(".carousel-item.active");
    var source = activeItem
      ? activeItem.querySelector(".gs-slide-description-source")
      : null;
    var text = source ? source.textContent.trim() : "";
    if (!text) {
      text = carousel.getAttribute("data-description-fallback") || "";
    }
    target.textContent = text;
  }

  function playActiveSlideVideo(carousel) {
    var activeItem = carousel.querySelector(".carousel-item.active");
    if (!activeItem) return;

    var player = activeItem.querySelector(".gs-video-player");
    var video = activeItem.querySelector(".gs-video-player-el");
    if (!player || !video) return;

    pauseAllInCarousel(carousel);

    var startPlayback = function () {
      video.muted = true;
      var playPromise = video.play();
      if (playPromise && playPromise.then) {
        playPromise
          .then(function () {
            hidePlayOverlay(player);
          })
          .catch(function () {
            showPlayOverlay(player);
          });
      } else {
        hidePlayOverlay(player);
      }
    };

    if (video.getAttribute("data-playback-hls") === "true" && !video.src && video.getAttribute("data-playback-src")) {
      attachHlsPlayback(video).then(startPlayback);
    } else {
      startPlayback();
    }
  }

  function getFullscreenElement() {
    return (
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.mozFullScreenElement ||
      document.msFullscreenElement ||
      null
    );
  }

  function requestFullscreen(el) {
    if (el.requestFullscreen) {
      return el.requestFullscreen();
    }
    if (el.webkitRequestFullscreen) {
      return el.webkitRequestFullscreen();
    }
    if (el.mozRequestFullScreen) {
      return el.mozRequestFullScreen();
    }
    if (el.msRequestFullscreen) {
      return el.msRequestFullscreen();
    }
    return Promise.reject(new Error("Fullscreen not supported"));
  }

  function exitFullscreen() {
    if (document.exitFullscreen) {
      return document.exitFullscreen();
    }
    if (document.webkitExitFullscreen) {
      return document.webkitExitFullscreen();
    }
    if (document.mozCancelFullScreen) {
      return document.mozCancelFullScreen();
    }
    if (document.msExitFullscreen) {
      return document.msExitFullscreen();
    }
    return Promise.resolve();
  }

  function isPlayerFullscreen(player, video) {
    var fs = getFullscreenElement();
    return fs === player || fs === video;
  }

  function updateFullscreenButton(player, video) {
    var btn = player.querySelector(".gs-video-fullscreen-btn");
    if (!btn) return;

    var active = isPlayerFullscreen(player, video);
    player.classList.toggle("is-fullscreen", active);
    btn.setAttribute("aria-label", active ? "Exit fullscreen" : "Maximize video");
    btn.setAttribute("title", active ? "Exit fullscreen" : "Maximize");
    btn.classList.toggle("is-active", active);
  }

  function applyFullscreenAudio(player, video, inFullscreen) {
    video.muted = !inFullscreen;
    player.classList.toggle("is-fullscreen", inFullscreen);
    updateFullscreenButton(player, video);
  }

  function enterFullscreen(player, video) {
    if (typeof video.webkitEnterFullscreen === "function") {
      video.webkitEnterFullscreen();
      return Promise.resolve();
    }
    return requestFullscreen(player);
  }

  function bindVideoPlayer(player) {
    var video = player.querySelector(".gs-video-player-el");
    var playBtn = player.querySelector(".gs-video-play-btn");
    var fullscreenBtn = player.querySelector(".gs-video-fullscreen-btn");
    if (!video || !playBtn) return;

    if (video.getAttribute("data-playback-hls") === "true" && video.getAttribute("data-playback-src")) {
      attachHlsPlayback(video);
    }

    function stopCarouselFromClick(event) {
      event.preventDefault();
      event.stopPropagation();
      if (event.stopImmediatePropagation) {
        event.stopImmediatePropagation();
      }
    }

    playBtn.addEventListener("mousedown", stopCarouselFromClick);
    playBtn.addEventListener("click", function (event) {
      stopCarouselFromClick(event);
      if (!isPlayerFullscreen(player, video)) {
        video.muted = true;
      }
      var playPromise = video.play();
      if (playPromise && playPromise.catch) {
        playPromise.catch(function () {
          showPlayOverlay(player);
        });
      }
    });

    if (fullscreenBtn) {
      fullscreenBtn.addEventListener("mousedown", stopCarouselFromClick);
      fullscreenBtn.addEventListener("click", function (event) {
        stopCarouselFromClick(event);

        if (isPlayerFullscreen(player, video)) {
          exitFullscreen();
          return;
        }

        var playPromise = video.play();
        var goFullscreen = function () {
          enterFullscreen(player, video)
            .then(function () {
              applyFullscreenAudio(player, video, true);
            })
            .catch(function () {
              /* ignore */
            });
        };

        if (playPromise && playPromise.then) {
          playPromise.then(goFullscreen).catch(goFullscreen);
        } else {
          goFullscreen();
        }
      });
    }

    video.addEventListener("play", function () {
      hidePlayOverlay(player);
    });

    video.addEventListener("pause", function () {
      if (!video.ended && !isPlayerFullscreen(player, video)) {
        showPlayOverlay(player);
      }
    });

    video.addEventListener("ended", function () {
      showPlayOverlay(player);
    });

    video.addEventListener("webkitbeginfullscreen", function () {
      applyFullscreenAudio(player, video, true);
    });

    video.addEventListener("webkitendfullscreen", function () {
      applyFullscreenAudio(player, video, false);
    });

    ["fullscreenchange", "webkitfullscreenchange", "mozfullscreenchange", "MSFullscreenChange"].forEach(
      function (eventName) {
        document.addEventListener(eventName, function () {
          applyFullscreenAudio(player, video, isPlayerFullscreen(player, video));
        });
      }
    );

    video.muted = true;
    updateFullscreenButton(player, video);
  }

  function initVideoCarousels() {
    document.querySelectorAll(".gs-video-carousel").forEach(function (carousel) {
      carousel.querySelectorAll(".gs-video-player").forEach(bindVideoPlayer);

      carousel.addEventListener("slid.bs.carousel", function () {
        updateCarouselSlideDescription(carousel);
        playActiveSlideVideo(carousel);
      });

      updateCarouselSlideDescription(carousel);

      window.setTimeout(function () {
        playActiveSlideVideo(carousel);
      }, 400);
    });
  }

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

    initVideoCarousels();
  }

  function init() {
    initProductCarousels();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

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
    });
    carousel.querySelectorAll(".gs-video-player").forEach(showPlayOverlay);
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

  function bindVideoPlayer(player) {
    var video = player.querySelector(".gs-video-player-el");
    var playBtn = player.querySelector(".gs-video-play-btn");
    if (!video || !playBtn) return;

    if (video.getAttribute("data-playback-hls") === "true" && video.getAttribute("data-playback-src")) {
      attachHlsPlayback(video);
    }

    playBtn.addEventListener("click", function () {
      video.muted = false;
      var playPromise = video.play();
      if (playPromise && playPromise.catch) {
        playPromise.catch(function () {
          showPlayOverlay(player);
        });
      }
    });

    video.addEventListener("play", function () {
      hidePlayOverlay(player);
    });

    video.addEventListener("pause", function () {
      if (!video.ended) {
        showPlayOverlay(player);
      }
    });

    video.addEventListener("ended", function () {
      showPlayOverlay(player);
    });
  }

  function initVideoCarousels() {
    document.querySelectorAll(".gs-video-carousel").forEach(function (carousel) {
      carousel.querySelectorAll(".gs-video-player").forEach(bindVideoPlayer);

      carousel.addEventListener("slid.bs.carousel", function () {
        playActiveSlideVideo(carousel);
      });

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

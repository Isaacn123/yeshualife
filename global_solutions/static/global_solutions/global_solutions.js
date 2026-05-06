(function () {
  function attachPlayback(video) {
    var src = video.getAttribute("data-playback-src");
    if (!src) return;

    // Native HLS (Safari/iOS)
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      return;
    }

    // Hls.js for most browsers
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

  document.addEventListener("DOMContentLoaded", function () {
    var videos = document.querySelectorAll(
      'video[data-playback-hls="true"][data-playback-src]'
    );
    for (var i = 0; i < videos.length; i++) {
      attachPlayback(videos[i]);
    }

    document.querySelectorAll(".gs-video-carousel").forEach(function (carouselEl) {
      carouselEl.addEventListener("slid.bs.carousel", function () {
        carouselEl.querySelectorAll("video").forEach(function (video) {
          video.pause();
        });
      });
    });
  });
})();


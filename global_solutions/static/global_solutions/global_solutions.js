(function () {
  function attachPlayback(video) {
    var src = video.getAttribute("data-playback-src");
    if (!src) return;

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

  document.addEventListener("DOMContentLoaded", function () {
    document
      .querySelectorAll('video[data-playback-hls="true"][data-playback-src]')
      .forEach(function (video) {
        if (video.closest(".gs-video-player")) {
          return;
        }
        attachPlayback(video);
      });
  });
})();

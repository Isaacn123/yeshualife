(function () {
  "use strict";

  var LIKED_KEY = "response_liked_videos";
  var playlistBySlug = {};
  var playlistOrder = [];
  var DESKTOP_MQ = window.matchMedia("(min-width: 900px)");
  var swipeState = {
    active: false,
    x: 0,
    y: 0,
    locked: false,
  };

  function getCsrfToken() {
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function apiBase() {
    var root = document.querySelector(".yl-rv");
    return (root && root.getAttribute("data-api-base")) || "/karamoja-response/api/videos/";
  }

  function loadPlaylist() {
    var el = document.getElementById("yl-rv-playlist");
    if (!el) return;
    try {
      var items = JSON.parse(el.textContent || "[]");
      if (!Array.isArray(items)) return;
      playlistOrder = [];
      playlistBySlug = {};
      items.forEach(function (item) {
        if (!item || !item.slug) return;
        playlistBySlug[item.slug] = item;
        playlistOrder.push(item.slug);
      });
    } catch (e) {
      playlistBySlug = {};
      playlistOrder = [];
    }
  }

  function playlistIndex(slug) {
    return playlistOrder.indexOf(slug);
  }

  function neighborSlug(slug, delta) {
    var index = playlistIndex(slug);
    if (index < 0 || !playlistOrder.length) return "";
    var next = index + delta;
    if (next < 0 || next >= playlistOrder.length) return "";
    return playlistOrder[next];
  }

  function readLiked() {
    try {
      var parsed = JSON.parse(localStorage.getItem(LIKED_KEY) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function saveLiked(slug) {
    var slugs = readLiked();
    if (slugs.indexOf(slug) === -1) {
      slugs.push(slug);
      localStorage.setItem(LIKED_KEY, JSON.stringify(slugs));
    }
  }

  function setLikeUi(slug, liked, likesDisplay) {
    document.querySelectorAll('.yl-rv__engagement[data-video-slug="' + slug + '"]').forEach(function (box) {
      var btn = box.querySelector(".yl-rv__like-btn");
      var count = box.querySelector(".yl-rv__likes");
      if (btn) {
        btn.classList.toggle("is-liked", liked);
        btn.setAttribute("aria-pressed", liked ? "true" : "false");
        btn.disabled = liked;
      }
      if (count && likesDisplay != null) count.textContent = likesDisplay;
    });
  }

  function viewThreshold(durationSeconds) {
    var d = parseFloat(durationSeconds);
    if (d && d > 0) {
      if (d <= 15) return Math.max(3, d * 0.5);
      if (d < 60) return Math.max(8, d * 0.5);
      return 15;
    }
    return 12;
  }

  function postJson(url, body) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": getCsrfToken(),
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    }).then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok, data: data };
      });
    });
  }

  function likeVideo(slug) {
    if (!slug || readLiked().indexOf(slug) !== -1) return;
    postJson(apiBase() + encodeURIComponent(slug) + "/like/")
      .then(function (result) {
        if (!result.ok) return;
        saveLiked(slug);
        setLikeUi(slug, true, result.data.likes_display);
      })
      .catch(function () {});
  }

  function shareVideo(btn) {
    var path = btn.getAttribute("data-share-path") || window.location.pathname;
    var title = btn.getAttribute("data-share-title") || document.title;
    var slug = btn.getAttribute("data-video-slug");
    var url = new URL(path, window.location.origin).href;

    function counted() {
      if (!slug) return;
      postJson(apiBase() + encodeURIComponent(slug) + "/share/").catch(function () {});
    }

    if (navigator.share) {
      navigator.share({ title: title, url: url }).then(counted).catch(function () {});
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(counted);
      return;
    }
    window.prompt("Copy this link:", url);
    counted();
  }

  function clearWatchTracking(player) {
    if (!player || !player._ylRvWatchCleanup) return;
    player._ylRvWatchCleanup();
    player._ylRvWatchCleanup = null;
  }

  function bindWatchTracking(player, wrap) {
    if (!player || !wrap) return;
    clearWatchTracking(player);

    var slug = wrap.getAttribute("data-video-slug") || wrap.getAttribute("data-slug");
    if (!slug || wrap.getAttribute("data-view-counted") === "true") return;

    var duration = wrap.getAttribute("data-video-duration") || "0";
    var threshold = viewThreshold(duration);
    var watched = 0;
    var last = player.currentTime || 0;
    var recorded = false;
    var pending = false;

    function tryRecord() {
      if (pending || recorded || watched < threshold) return;
      pending = true;
      postJson(apiBase() + encodeURIComponent(slug) + "/view/", { watched_seconds: watched })
        .then(function (result) {
          pending = false;
          if (!result.ok) return;
          if (result.data.counted || result.data.already_counted) {
            recorded = true;
            wrap.setAttribute("data-view-counted", "true");
          }
          if (result.data.views_display != null) {
            document
              .querySelectorAll('.yl-rv__engagement[data-video-slug="' + slug + '"] .yl-rv__views')
              .forEach(function (el) {
                el.textContent = result.data.views_display;
              });
            var likesText = "0";
            var likesEl = document.querySelector(
              '.yl-rv__engagement[data-video-slug="' + slug + '"] .yl-rv__likes'
            );
            if (likesEl) likesText = likesEl.textContent || "0";
            document
              .querySelectorAll('.yl-rv__thumb[data-slug="' + slug + '"] .yl-rv__thumb-stats')
              .forEach(function (el) {
                el.textContent = result.data.views_display + " views · " + likesText + " likes";
              });
          }
        })
        .catch(function () {
          pending = false;
        });
    }

    function onMeta() {
      if (!duration || duration === "0") threshold = viewThreshold(player.duration);
    }
    function onPlay() {
      last = player.currentTime;
    }
    function onSeeked() {
      last = player.currentTime;
    }
    function onTime() {
      var now = player.currentTime || 0;
      var delta = now - last;
      if (delta > 0 && delta < 2.5) watched += delta;
      last = now;
      tryRecord();
    }

    player.addEventListener("loadedmetadata", onMeta);
    player.addEventListener("play", onPlay);
    player.addEventListener("seeked", onSeeked);
    player.addEventListener("timeupdate", onTime);
    player._ylRvWatchCleanup = function () {
      player.removeEventListener("loadedmetadata", onMeta);
      player.removeEventListener("play", onPlay);
      player.removeEventListener("seeked", onSeeked);
      player.removeEventListener("timeupdate", onTime);
    };
  }

  function pauseAllVideos(except) {
    document.querySelectorAll(".yl-rv video").forEach(function (video) {
      if (video === except) return;
      try {
        video.pause();
      } catch (e) {}
    });
    document.querySelectorAll(".yl-rv__card.is-playing").forEach(function (card) {
      if (except && card.contains(except)) return;
      card.classList.remove("is-playing");
    });
  }

  function tryAutoplay(player) {
    if (!player) return;
    var playPromise = player.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(function () {});
    }
  }

  function getFullscreenVideo() {
    var fs =
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.msFullscreenElement ||
      null;
    if (fs) {
      if (fs.tagName === "VIDEO") return fs;
      if (fs.querySelector) {
        var nested = fs.querySelector("video.yl-rv__player, video.yl-rv__card-video");
        if (nested) return nested;
      }
    }
    var ios = document.querySelector(".yl-rv video");
    if (ios && ios.webkitDisplayingFullscreen) return ios;
    return null;
  }

  function isFullscreenActive() {
    return !!getFullscreenVideo();
  }

  function currentSlug() {
    if (DESKTOP_MQ.matches) {
      var wrap = document.querySelector(".yl-rv__player-wrap");
      return (wrap && wrap.getAttribute("data-video-slug")) || playlistOrder[0] || "";
    }
    var playing = document.querySelector(".yl-rv__card.is-playing");
    if (playing) return playing.getAttribute("data-slug") || "";
    var fsVideo = getFullscreenVideo();
    if (fsVideo) {
      var card = fsVideo.closest(".yl-rv__card");
      if (card) return card.getAttribute("data-slug") || "";
      var wrapFs = fsVideo.closest(".yl-rv__player-wrap");
      if (wrapFs) return wrapFs.getAttribute("data-video-slug") || "";
    }
    return playlistOrder[0] || "";
  }

  function applySourceToVideo(player, item) {
    if (!player || !item) return;
    var wasFs = false;
    try {
      wasFs =
        document.fullscreenElement === player ||
        document.webkitFullscreenElement === player ||
        !!player.webkitDisplayingFullscreen;
    } catch (e) {
      wasFs = false;
    }

    clearWatchTracking(player);
    player.pause();
    if (item.poster) player.setAttribute("poster", item.poster);
    else player.removeAttribute("poster");
    player.src = item.src || "";
    player.load();

    // Re-enter fullscreen on the same element if the browser dropped it on source change
    function ensureFs() {
      if (!wasFs) return;
      if (document.fullscreenElement === player || document.webkitFullscreenElement === player) return;
      if (player.webkitDisplayingFullscreen) return;
      if (player.requestFullscreen) {
        player.requestFullscreen().catch(function () {});
      } else if (player.webkitEnterFullscreen) {
        try {
          player.webkitEnterFullscreen();
        } catch (e) {}
      } else if (player.webkitRequestFullscreen) {
        try {
          player.webkitRequestFullscreen();
        } catch (e) {}
      }
    }

    player.addEventListener(
      "loadeddata",
      function () {
        ensureFs();
        tryAutoplay(player);
      },
      { once: true }
    );
  }

  function selectDesktop(slug, shouldPlay, skipScroll) {
    var item = playlistBySlug[slug];
    var player = document.getElementById("yl-rv-player");
    var wrap = document.querySelector(".yl-rv__player-wrap");
    var title = document.getElementById("yl-rv-title");
    var engagement = document.querySelector(".yl-rv__desktop .yl-rv__engagement");
    if (!item || !player || !slug) return;

    pauseAllVideos(player);
    applySourceToVideo(player, item);

    if (wrap) {
      wrap.setAttribute("data-video-slug", slug);
      wrap.setAttribute("data-video-duration", item.duration || "0");
      wrap.removeAttribute("data-view-counted");
      if (!skipScroll && !isFullscreenActive()) {
        wrap.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      bindWatchTracking(player, wrap);
    }

    if (title) title.textContent = item.title || "";
    if (engagement) {
      engagement.setAttribute("data-video-slug", slug);
      var likeBtn = engagement.querySelector(".yl-rv__like-btn");
      var shareBtn = engagement.querySelector(".yl-rv__share-btn");
      var views = engagement.querySelector(".yl-rv__views");
      var likes = engagement.querySelector(".yl-rv__likes");
      if (likeBtn) {
        likeBtn.setAttribute("data-video-slug", slug);
        likeBtn.disabled = false;
        setLikeUi(slug, readLiked().indexOf(slug) !== -1);
      }
      if (shareBtn) {
        shareBtn.setAttribute("data-video-slug", slug);
        shareBtn.setAttribute("data-share-path", item.share_path || "");
        shareBtn.setAttribute("data-share-title", item.title || "");
      }
      if (views) views.textContent = item.views || "0";
      if (likes) likes.textContent = item.likes || "0";
    }

    document.querySelectorAll(".yl-rv__thumb").forEach(function (el) {
      var active = el.getAttribute("data-slug") === slug;
      el.classList.toggle("is-active", active);
      el.setAttribute("aria-pressed", active ? "true" : "false");
    });

    if (shouldPlay) tryAutoplay(player);
  }

  function playMobileCard(slug, shouldPlay) {
    var card = document.querySelector('.yl-rv__card[data-slug="' + slug + '"]');
    if (!card) return;
    var video = card.querySelector(".yl-rv__card-video");
    var item = playlistBySlug[slug];
    if (!video || !item) return;

    pauseAllVideos(video);
    applySourceToVideo(video, item);

    card.classList.add("is-playing");
    card.removeAttribute("data-view-counted");
    card.setAttribute("data-video-slug", slug);
    card.setAttribute("data-video-duration", item.duration || "0");
    bindWatchTracking(video, card);
    if (!isFullscreenActive()) {
      card.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    if (shouldPlay !== false) tryAutoplay(video);
  }

  function stepPlaylist(delta) {
    if (swipeState.locked || playlistOrder.length < 2) return;
    var slug = currentSlug();
    var next = neighborSlug(slug, delta);
    if (!next) return;

    swipeState.locked = true;
    window.setTimeout(function () {
      swipeState.locked = false;
    }, 350);

    var fsVideo = getFullscreenVideo();

    if (DESKTOP_MQ.matches) {
      // Keep the same fullscreen element; only change source.
      selectDesktop(next, true, true);
      if (fsVideo && fsVideo.id === "yl-rv-player") {
        // already updated by selectDesktop on same element
      }
      return;
    }

    // Mobile: if fullscreen on a card video, swap source on that same element
    // and update page state to the target card.
    if (fsVideo && fsVideo.classList.contains("yl-rv__card-video")) {
      var item = playlistBySlug[next];
      applySourceToVideo(fsVideo, item);
      // Mark the destination card as active for when they exit fullscreen
      document.querySelectorAll(".yl-rv__card.is-playing").forEach(function (c) {
        c.classList.remove("is-playing");
      });
      var nextCard = document.querySelector('.yl-rv__card[data-slug="' + next + '"]');
      if (nextCard) {
        nextCard.classList.add("is-playing");
        nextCard.setAttribute("data-video-slug", next);
        nextCard.setAttribute("data-video-duration", (item && item.duration) || "0");
        nextCard.removeAttribute("data-view-counted");
        // Keep the fullscreen video element in sync with card tracking after exit
        var nextVideo = nextCard.querySelector(".yl-rv__card-video");
        if (nextVideo && nextVideo !== fsVideo && item) {
          nextVideo.setAttribute("src", item.src || "");
          if (item.poster) nextVideo.setAttribute("poster", item.poster);
        }
        bindWatchTracking(fsVideo, nextCard);
      }
      return;
    }

    playMobileCard(next, true);
  }

  function bindSwipeOn(el) {
    if (!el || el._ylRvSwipeBound) return;
    el._ylRvSwipeBound = true;

    el.addEventListener(
      "touchstart",
      function (event) {
        if (!event.touches || !event.touches.length) return;
        swipeState.active = true;
        swipeState.x = event.touches[0].clientX;
        swipeState.y = event.touches[0].clientY;
      },
      { passive: true }
    );

    el.addEventListener(
      "touchend",
      function (event) {
        if (!swipeState.active || !event.changedTouches || !event.changedTouches.length) return;
        swipeState.active = false;
        var dx = event.changedTouches[0].clientX - swipeState.x;
        var dy = event.changedTouches[0].clientY - swipeState.y;
        var absX = Math.abs(dx);
        var absY = Math.abs(dy);
        if (Math.max(absX, absY) < 55) return;

        // In fullscreen prefer horizontal + vertical; otherwise require a clear swipe
        if (absY >= absX) stepPlaylist(dy < 0 ? 1 : -1);
        else stepPlaylist(dx < 0 ? 1 : -1);
      },
      { passive: true }
    );
  }

  function bindFullscreenSwipe() {
    // Capture swipes while the browser fullscreen player is open
    document.addEventListener(
      "touchstart",
      function (event) {
        if (!isFullscreenActive()) return;
        if (!event.touches || !event.touches.length) return;
        swipeState.active = true;
        swipeState.x = event.touches[0].clientX;
        swipeState.y = event.touches[0].clientY;
      },
      { passive: true, capture: true }
    );

    document.addEventListener(
      "touchend",
      function (event) {
        if (!isFullscreenActive() || !swipeState.active) return;
        if (!event.changedTouches || !event.changedTouches.length) return;
        swipeState.active = false;
        var dx = event.changedTouches[0].clientX - swipeState.x;
        var dy = event.changedTouches[0].clientY - swipeState.y;
        var absX = Math.abs(dx);
        var absY = Math.abs(dy);
        if (Math.max(absX, absY) < 50) return;
        if (absY >= absX) stepPlaylist(dy < 0 ? 1 : -1);
        else stepPlaylist(dx < 0 ? 1 : -1);
      },
      { passive: true, capture: true }
    );

    document.addEventListener("keydown", function (event) {
      if (!isFullscreenActive()) return;
      if (event.key === "ArrowRight" || event.key === "ArrowUp") {
        event.preventDefault();
        stepPlaylist(1);
      } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
        event.preventDefault();
        stepPlaylist(-1);
      }
    });
  }

  function initLikedState() {
    readLiked().forEach(function (slug) {
      setLikeUi(slug, true);
    });
  }

  function init() {
    var root = document.querySelector(".yl-rv");
    if (!root) return;

    loadPlaylist();
    initLikedState();
    bindFullscreenSwipe();

    var desktopPlayer = document.getElementById("yl-rv-player");
    var desktopWrap = document.querySelector(".yl-rv__player-wrap");
    if (desktopPlayer && desktopWrap) {
      bindWatchTracking(desktopPlayer, desktopWrap);
      bindSwipeOn(desktopWrap);
    }

    document.querySelectorAll(".yl-rv__card-media").forEach(function (media) {
      bindSwipeOn(media);
    });

    // Remove leftover custom theater if an old page still had it open
    var oldTheater = document.getElementById("yl-rv-theater");
    if (oldTheater) oldTheater.remove();
    document.body.classList.remove("yl-rv-theater-open");

    document.addEventListener(
      "click",
      function (event) {
        var likeBtn = event.target.closest(".yl-rv__like-btn");
        if (likeBtn) {
          event.preventDefault();
          event.stopPropagation();
          likeVideo(likeBtn.getAttribute("data-video-slug"));
          return;
        }

        var shareBtn = event.target.closest(".yl-rv__share-btn");
        if (shareBtn) {
          event.preventDefault();
          event.stopPropagation();
          shareVideo(shareBtn);
          return;
        }

        var cardStart = event.target.closest(".yl-rv__card-start");
        if (cardStart) {
          event.preventDefault();
          event.stopPropagation();
          playMobileCard(cardStart.getAttribute("data-slug"), true);
          return;
        }

        var thumb = event.target.closest(".yl-rv__thumb");
        if (thumb) {
          event.preventDefault();
          event.stopPropagation();
          selectDesktop(thumb.getAttribute("data-slug"), true);
        }
      },
      true
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

(function () {
  "use strict";

  var LIKED_KEY = "response_liked_videos";
  var playlistBySlug = {};
  var playlistOrder = [];
  var DESKTOP_MQ = window.matchMedia("(min-width: 900px)");
  var fs = {
    open: false,
    slug: "",
    touchActive: false,
    x: 0,
    y: 0,
    locked: false,
    redirecting: false,
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
    if (!playlistOrder.length) return "";
    var index = playlistIndex(slug);
    if (index < 0) index = 0;
    // Wrap around so last ↔ first always moves
    var next = (index + delta) % playlistOrder.length;
    if (next < 0) next = playlistOrder.length - 1;
    return playlistOrder[next] || "";
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

    var slug = wrap.getAttribute("data-video-slug") || wrap.getAttribute("data-slug") || fs.slug;
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
    document.querySelectorAll(".yl-rv video, #yl-rv-fs-player").forEach(function (video) {
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

  function currentPageSlug() {
    if (fs.open && fs.slug) return fs.slug;
    if (DESKTOP_MQ.matches) {
      var wrap = document.querySelector(".yl-rv__player-wrap");
      return (wrap && wrap.getAttribute("data-video-slug")) || playlistOrder[0] || "";
    }
    var playing = document.querySelector(".yl-rv__card.is-playing");
    if (playing) return playing.getAttribute("data-slug") || "";
    return playlistOrder[0] || "";
  }

  function slugFromVideoEl(video) {
    if (!video) return currentPageSlug();
    if (video.id === "yl-rv-fs-player") return fs.slug || currentPageSlug();
    var card = video.closest(".yl-rv__card");
    if (card) return card.getAttribute("data-slug") || "";
    var wrap = video.closest(".yl-rv__player-wrap");
    if (wrap) return wrap.getAttribute("data-video-slug") || "";
    return currentPageSlug();
  }

  function exitNativeFullscreen(video) {
    try {
      if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen();
      else if (document.webkitFullscreenElement && document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      }
    } catch (e) {}
    try {
      if (video && video.webkitDisplayingFullscreen && video.webkitExitFullscreen) {
        video.webkitExitFullscreen();
      }
    } catch (e) {}
  }

  function selectDesktop(slug, shouldPlay, skipScroll) {
    var item = playlistBySlug[slug];
    var player = document.getElementById("yl-rv-player");
    var wrap = document.querySelector(".yl-rv__player-wrap");
    var title = document.getElementById("yl-rv-title");
    var engagement = document.querySelector(".yl-rv__desktop .yl-rv__engagement");
    if (!item || !player || !slug) return;

    clearWatchTracking(player);
    pauseAllVideos(player);
    player.pause();
    if (item.poster) player.setAttribute("poster", item.poster);
    else player.removeAttribute("poster");
    player.src = item.src || "";
    player.load();

    if (wrap) {
      wrap.setAttribute("data-video-slug", slug);
      wrap.setAttribute("data-video-duration", item.duration || "0");
      wrap.removeAttribute("data-view-counted");
      if (!skipScroll) wrap.scrollIntoView({ behavior: "smooth", block: "start" });
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
      var expandBtn = engagement.querySelector(".yl-rv__expand-btn");
      if (expandBtn) expandBtn.setAttribute("data-slug", slug);
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
    var item = playlistBySlug[slug];
    if (!card || !item) return;
    var video = card.querySelector(".yl-rv__card-video");
    if (!video) return;

    clearWatchTracking(video);
    pauseAllVideos(video);
    if (item.poster) video.setAttribute("poster", item.poster);
    else video.removeAttribute("poster");
    video.src = item.src || "";
    video.load();
    card.classList.add("is-playing");
    card.removeAttribute("data-view-counted");
    card.setAttribute("data-video-slug", slug);
    card.setAttribute("data-video-duration", item.duration || "0");
    bindWatchTracking(video, card);
    if (!fs.open) card.scrollIntoView({ behavior: "smooth", block: "nearest" });
    if (shouldPlay !== false) tryAutoplay(video);
  }

  function isIOS() {
    return (
      /iPad|iPhone|iPod/.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
    );
  }

  function isAndroid() {
    return /Android/i.test(navigator.userAgent);
  }

  function setThemeColor(color) {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.setAttribute("name", "theme-color");
      document.head.appendChild(meta);
    }
    if (!fs._themeColorPrev) {
      fs._themeColorPrev = meta.getAttribute("content") || "";
    }
    meta.setAttribute("content", color);
  }

  function restoreThemeColor() {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) return;
    meta.setAttribute("content", fs._themeColorPrev || "#ffffff");
  }

  function requestShellFullscreen(el) {
    if (!el) return;
    var req =
      el.requestFullscreen ||
      el.webkitRequestFullscreen ||
      el.webkitRequestFullScreen ||
      el.msRequestFullscreen;
    if (!req) return;
    try {
      var result = req.call(el);
      if (result && typeof result.catch === "function") result.catch(function () {});
    } catch (e) {}
  }

  function exitShellFullscreen() {
    var exit =
      document.exitFullscreen ||
      document.webkitExitFullscreen ||
      document.webkitCancelFullScreen ||
      document.msExitFullscreen;
    if (!exit) return;
    if (
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.msFullscreenElement
    ) {
      try {
        var result = exit.call(document);
        if (result && typeof result.catch === "function") result.catch(function () {});
      } catch (e) {}
    }
  }

  function ensureFullscreen() {
    var existing = document.getElementById("yl-rv-fs");
    if (existing) return existing;

    var el = document.createElement("div");
    el.id = "yl-rv-fs";
    el.className =
      "yl-rv-fs" + (isIOS() ? " yl-rv-fs--ios" : "") + (isAndroid() ? " yl-rv-fs--android" : "");
    el.hidden = true;
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    el.setAttribute("aria-label", "Fullscreen video");

    var closeHtml = isIOS()
      ? '<button type="button" class="yl-rv-fs__close yl-rv-fs__close--done" aria-label="Done">Done</button>'
      : '<button type="button" class="yl-rv-fs__close yl-rv-fs__close--icon" aria-label="Close">×</button>';

    // Important: nav controls sit in an HTML bar UNDER the video element.
    // Overlays on top of <video> often cannot receive taps on iOS/Android.
    el.innerHTML =
      closeHtml +
      '<div class="yl-rv-fs__stage">' +
      '<video id="yl-rv-fs-player" class="yl-rv-fs__player" controls playsinline webkit-playsinline x5-playsinline controlslist="nofullscreen nodownload noremoteplayback" disablepictureinpicture></video>' +
      "</div>" +
      '<div class="yl-rv-fs__bar">' +
      '<button type="button" class="yl-rv-fs__nav yl-rv-fs__nav--prev" aria-label="Previous video">‹ Previous</button>' +
      '<button type="button" class="yl-rv-fs__nav yl-rv-fs__nav--next" aria-label="Next video">Next ›</button>' +
      "</div>";
    document.body.appendChild(el);

    el.querySelector(".yl-rv-fs__close").addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      closeFullscreen();
    });
    el.querySelector(".yl-rv-fs__nav--prev").addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      stepFullscreen(-1);
    });
    el.querySelector(".yl-rv-fs__nav--next").addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      stepFullscreen(1);
    });

    // Swipe on the bar area (reliable) and on the shell background
    function bindSwipeTarget(target) {
      if (!target || target._ylRvSwipeBound) return;
      target._ylRvSwipeBound = true;
      target.addEventListener(
        "touchstart",
        function (event) {
          if (!event.touches || !event.touches.length) return;
          fs.touchActive = true;
          fs.x = event.touches[0].clientX;
          fs.y = event.touches[0].clientY;
        },
        { passive: true }
      );
      target.addEventListener(
        "touchend",
        function (event) {
          if (!fs.touchActive || !event.changedTouches || !event.changedTouches.length) return;
          fs.touchActive = false;
          var dx = event.changedTouches[0].clientX - fs.x;
          var dy = event.changedTouches[0].clientY - fs.y;
          var absX = Math.abs(dx);
          var absY = Math.abs(dy);
          if (Math.max(absX, absY) < 35) return;
          if (absY >= absX) stepFullscreen(dy < 0 ? 1 : -1);
          else stepFullscreen(dx < 0 ? 1 : -1);
        },
        { passive: true }
      );
    }
    bindSwipeTarget(el.querySelector(".yl-rv-fs__bar"));
    bindSwipeTarget(el);

    var player = el.querySelector("#yl-rv-fs-player");
    if (player) {
      player.addEventListener("ended", function () {
        if (!fs.open) return;
        // Advance when a clip finishes
        if (neighborSlug(fs.slug, 1)) stepFullscreen(1);
      });
    }

    return el;
  }

  function loadFullscreenVideo(slug, shouldPlay) {
    var item = playlistBySlug[slug];
    var player = document.getElementById("yl-rv-fs-player");
    var shell = document.getElementById("yl-rv-fs");
    if (!item || !player || !shell) return;

    fs.slug = slug;
    clearWatchTracking(player);
    pauseAllVideos(player);
    player.pause();
    if (item.poster) player.setAttribute("poster", item.poster);
    else player.removeAttribute("poster");
    player.src = item.src || "";
    player.load();
    shell.setAttribute("data-video-slug", slug);
    shell.setAttribute("data-video-duration", item.duration || "0");
    shell.removeAttribute("data-view-counted");
    bindWatchTracking(player, shell);
    if (shouldPlay) tryAutoplay(player);

    if (DESKTOP_MQ.matches) selectDesktop(slug, false, true);
    else {
      var card = document.querySelector('.yl-rv__card[data-slug="' + slug + '"]');
      if (card) {
        document.querySelectorAll(".yl-rv__card.is-playing").forEach(function (c) {
          c.classList.remove("is-playing");
        });
        card.classList.add("is-playing");
      }
    }
  }

  function openFullscreen(slug) {
    loadPlaylist();
    if (!slug || !playlistBySlug[slug]) return;
    if (playlistOrder.length < 1) return;
    var el = ensureFullscreen();
    fs.open = true;
    document.body.classList.add("yl-rv-fs-open");
    if (isIOS()) document.body.classList.add("yl-rv-fs-open--ios");
    if (isAndroid()) document.body.classList.add("yl-rv-fs-open--android");
    el.hidden = false;
    setThemeColor("#000000");
    loadFullscreenVideo(slug, true);
    // Do not call browser requestFullscreen here — on phones it steals gestures
    // and blocks next/previous. The fixed black overlay already fills the screen.
  }

  function closeFullscreen() {
    var el = document.getElementById("yl-rv-fs");
    var player = document.getElementById("yl-rv-fs-player");
    fs.open = false;
    fs.slug = "";
    document.body.classList.remove("yl-rv-fs-open", "yl-rv-fs-open--ios", "yl-rv-fs-open--android");
    restoreThemeColor();
    exitShellFullscreen();
    if (player) {
      clearWatchTracking(player);
      try {
        player.pause();
      } catch (e) {}
      player.removeAttribute("src");
    }
    if (el) el.hidden = true;
  }

  function stepFullscreen(delta) {
    if (!fs.open || fs.locked) return;
    loadPlaylist();
    if (playlistOrder.length < 2) return;
    var current = fs.slug || currentPageSlug() || playlistOrder[0];
    var next = neighborSlug(current, delta);
    if (!next || next === current) return;
    fs.locked = true;
    window.setTimeout(function () {
      fs.locked = false;
    }, 200);
    loadFullscreenVideo(next, true);
  }

  function bindNativeFullscreenRedirect(video) {
    if (!video || video._ylRvFsBound || video.id === "yl-rv-fs-player") return;
    video._ylRvFsBound = true;

    // Hide/disable the browser maximize control where supported.
    try {
      video.setAttribute("controlslist", "nofullscreen nodownload noremoteplayback");
      video.setAttribute("playsinline", "");
      video.setAttribute("webkit-playsinline", "");
      video.disablePictureInPicture = true;
    } catch (e) {}

    function openOursOnly() {
      // Never enter native fullscreen first — that causes: default → then custom.
      openFullscreen(slugFromVideoEl(video));
    }

    // Replace native fullscreen APIs so they open custom directly (no native flash).
    try {
      if (typeof video.webkitEnterFullscreen === "function") {
        video.webkitEnterFullscreen = openOursOnly;
      }
      if (typeof video.webkitEnterFullScreen === "function") {
        video.webkitEnterFullScreen = openOursOnly;
      }
      video.requestFullscreen = function () {
        openOursOnly();
        return Promise.resolve();
      };
      if (video.webkitRequestFullscreen) {
        video.webkitRequestFullscreen = openOursOnly;
      }
      if (video.webkitRequestFullScreen) {
        video.webkitRequestFullScreen = openOursOnly;
      }
    } catch (e) {}

    // If the OS still forces native fullscreen (some iOS builds), cancel it only.
    // Do NOT open custom from these events — that is what showed: native first, custom after exit.
    function cancelNativeOnly() {
      exitNativeFullscreen(video);
      try {
        if (video.webkitDisplayingFullscreen && video.webkitExitFullscreen) {
          video.webkitExitFullscreen();
        }
      } catch (e) {}
    }

    video.addEventListener("fullscreenchange", function () {
      if (document.fullscreenElement === video) cancelNativeOnly();
    });
    video.addEventListener("webkitfullscreenchange", function () {
      if (document.webkitFullscreenElement === video) cancelNativeOnly();
    });
    video.addEventListener("webkitbeginfullscreen", function () {
      cancelNativeOnly();
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
    ensureFullscreen();

    var desktopPlayer = document.getElementById("yl-rv-player");
    var desktopWrap = document.querySelector(".yl-rv__player-wrap");
    if (desktopPlayer && desktopWrap) {
      bindWatchTracking(desktopPlayer, desktopWrap);
      bindNativeFullscreenRedirect(desktopPlayer);
    }
    document.querySelectorAll(".yl-rv__card-video").forEach(bindNativeFullscreenRedirect);

    // If a page video somehow enters browser fullscreen, cancel it only.
    // Custom fullscreen opens only from the Fullscreen button (or patched APIs).
    document.addEventListener("fullscreenchange", function () {
      var node = document.fullscreenElement;
      if (!node) return;
      if (node.id === "yl-rv-fs") return;
      var video = node.tagName === "VIDEO" ? node : node.querySelector && node.querySelector(".yl-rv video, video.yl-rv__player, video.yl-rv__card-video");
      if (!video || !video.closest || !video.closest(".yl-rv")) return;
      if (video.id === "yl-rv-fs-player") return;
      exitNativeFullscreen(video);
    });

    document.addEventListener("keydown", function (event) {
      if (!fs.open) return;
      if (event.key === "Escape") {
        closeFullscreen();
        return;
      }
      if (event.key === "ArrowRight" || event.key === "ArrowUp") {
        event.preventDefault();
        stepFullscreen(1);
      } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
        event.preventDefault();
        stepFullscreen(-1);
      }
    });

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

        var expandBtn = event.target.closest(".yl-rv__expand-btn");
        if (expandBtn) {
          event.preventDefault();
          event.stopPropagation();
          openFullscreen(expandBtn.getAttribute("data-slug") || currentPageSlug());
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

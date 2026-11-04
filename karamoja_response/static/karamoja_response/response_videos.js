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
    chromeTimer: null,
    chromeVisible: true,
  };

  var PLAY_ICON =
    '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true" focusable="false"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>';
  var PAUSE_ICON =
    '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true" focusable="false"><path fill="currentColor" d="M6 5h4v14H6V5zm8 0h4v14h-4V5z"/></svg>';

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
      if (video && typeof video.webkitExitFullscreen === "function") {
        video.webkitExitFullscreen();
      }
    } catch (e) {}
    try {
      if (video && typeof video.webkitExitFullScreen === "function") {
        video.webkitExitFullScreen();
      }
    } catch (e) {}
  }

  function resolveFsSlug(slug, video) {
    loadPlaylist();
    if (slug && playlistBySlug[slug]) return slug;
    var fromVideo = slugFromVideoEl(video);
    if (fromVideo && playlistBySlug[fromVideo]) return fromVideo;
    var page = currentPageSlug();
    if (page && playlistBySlug[page]) return page;
    return playlistOrder[0] || "";
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
    if (wrap) wrap.classList.remove("is-playing");
    if (item.poster) player.setAttribute("poster", item.poster);
    else player.removeAttribute("poster");
    player.src = item.src || "";
    player.load();
    applyPageVideoChrome(player);

    if (wrap) {
      wrap.setAttribute("data-video-slug", slug);
      wrap.setAttribute("data-video-duration", item.duration || "0");
      wrap.removeAttribute("data-view-counted");
      if (!skipScroll) wrap.scrollIntoView({ behavior: "smooth", block: "start" });
      bindWatchTracking(player, wrap);
      var startBtn = wrap.querySelector(".yl-rv__player-start");
      if (startBtn) startBtn.setAttribute("data-slug", slug);
      var fsIcon = wrap.querySelector(".yl-rv__fs-icon");
      if (fsIcon) fsIcon.setAttribute("data-slug", slug);
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
    applyPageVideoChrome(video);
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

  // Phones always expose a native maximize on <video controls>. That layer
  // sits above our custom FS and causes the still-image / double-player bug.
  function isPhonePlayer() {
    return isIOS() || isAndroid();
  }

  function applyPageVideoChrome(video) {
    if (!video || video.id === "yl-rv-fs-player") return;
    hardenVideoAgainstNativeFs(video);
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

    // No native controls — custom play/pause chrome auto-hides after idle.
    var fsVideoAttrs =
      'playsinline webkit-playsinline x5-playsinline controlslist="nofullscreen nodownload noremoteplayback" disablepictureinpicture';

    el.innerHTML =
      closeHtml +
      '<div class="yl-rv-fs__stage">' +
      '<video id="yl-rv-fs-player" class="yl-rv-fs__player" ' +
      fsVideoAttrs +
      "></video>" +
      "</div>" +
      // Chrome sits as a sibling ABOVE the video layer (phones composite <video> over in-stage overlays)
      '<div class="yl-rv-fs__chrome">' +
      '<button type="button" class="yl-rv-fs__toggle" aria-label="Pause">' +
      PAUSE_ICON +
      "</button>" +
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
          revealFsChrome(true);
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
    var toggle = el.querySelector(".yl-rv-fs__toggle");
    if (player) {
      bindFsPlayerNativeBlock(player);
      player.addEventListener("play", function () {
        updateFsToggleIcon(player);
        revealFsChrome(true);
      });
      player.addEventListener("pause", function () {
        updateFsToggleIcon(player);
        revealFsChrome(false);
      });
      player.addEventListener("ended", function () {
        if (!fs.open) return;
        updateFsToggleIcon(player);
        revealFsChrome(false);
        if (neighborSlug(fs.slug, 1)) stepFullscreen(1);
      });
    }
    if (toggle) {
      toggle.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        toggleFsPlayback();
      });
    }
    el.addEventListener("click", function (event) {
      if (!fs.open) return;
      if (event.target.closest(".yl-rv-fs__close, .yl-rv-fs__nav, .yl-rv-fs__toggle")) return;
      // Tap empty stage / video: reveal chrome, or toggle play if chrome already up
      if (!fs.chromeVisible) {
        revealFsChrome(true);
        return;
      }
      toggleFsPlayback();
    });

    return el;
  }

  function clearFsChromeTimer() {
    if (fs.chromeTimer) {
      window.clearTimeout(fs.chromeTimer);
      fs.chromeTimer = null;
    }
  }

  function updateFsToggleIcon(player) {
    var toggle = document.querySelector("#yl-rv-fs .yl-rv-fs__toggle");
    if (!toggle) return;
    var paused = !player || player.paused || player.ended;
    toggle.innerHTML = paused ? PLAY_ICON : PAUSE_ICON;
    toggle.setAttribute("aria-label", paused ? "Play" : "Pause");
    toggle.classList.toggle("is-paused", paused);
    toggle.classList.toggle("is-playing", !paused);
  }

  function revealFsChrome(autoHide) {
    var el = document.getElementById("yl-rv-fs");
    var player = document.getElementById("yl-rv-fs-player");
    if (!el) return;
    fs.chromeVisible = true;
    el.classList.add("yl-rv-fs--chrome-visible");
    el.classList.remove("yl-rv-fs--chrome-hidden");
    updateFsToggleIcon(player);
    clearFsChromeTimer();
    // While paused, keep the play button visible. While playing, show pause then hide after 3s.
    if (autoHide === false || (player && player.paused)) return;
    fs.chromeTimer = window.setTimeout(function () {
      hideFsChrome();
    }, 3000);
  }

  function hideFsChrome() {
    var el = document.getElementById("yl-rv-fs");
    var player = document.getElementById("yl-rv-fs-player");
    clearFsChromeTimer();
    if (!el || !fs.open) return;
    // Keep play button visible while paused
    if (player && player.paused) {
      fs.chromeVisible = true;
      el.classList.add("yl-rv-fs--chrome-visible");
      el.classList.remove("yl-rv-fs--chrome-hidden");
      updateFsToggleIcon(player);
      return;
    }
    fs.chromeVisible = false;
    el.classList.remove("yl-rv-fs--chrome-visible");
    el.classList.add("yl-rv-fs--chrome-hidden");
  }

  function toggleFsPlayback() {
    var player = document.getElementById("yl-rv-fs-player");
    if (!player || !fs.open) return;
    if (player.paused) {
      tryAutoplay(player);
      revealFsChrome(true);
    } else {
      try {
        player.pause();
      } catch (e) {}
      revealFsChrome(false);
    }
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
    updateFsToggleIcon(player);
    revealFsChrome(true);
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

  function syncFsViewport() {
    var el = document.getElementById("yl-rv-fs");
    if (!el || !fs.open) return;
    var vv = window.visualViewport;
    var w = Math.round((vv && vv.width) || window.innerWidth || document.documentElement.clientWidth || 0);
    var h = Math.round((vv && vv.height) || window.innerHeight || document.documentElement.clientHeight || 0);
    var top = Math.round((vv && vv.offsetTop) || 0);
    var left = Math.round((vv && vv.offsetLeft) || 0);
    if (!w || !h) return;
    el.style.setProperty("--yl-rv-vvw", w + "px");
    el.style.setProperty("--yl-rv-vvh", h + "px");
    el.style.setProperty("--yl-rv-vvt", top + "px");
    el.style.setProperty("--yl-rv-vvl", left + "px");
    el.style.top = top + "px";
    el.style.left = left + "px";
    el.style.width = w + "px";
    el.style.height = h + "px";
  }

  function bindFsViewportSync() {
    if (fs._viewportBound) return;
    fs._viewportBound = true;
    var onChange = function () {
      if (!fs.open) return;
      syncFsViewport();
      // iOS often settles layout one frame after rotate
      window.requestAnimationFrame(syncFsViewport);
      window.setTimeout(syncFsViewport, 120);
      window.setTimeout(syncFsViewport, 320);
    };
    window.addEventListener("resize", onChange);
    window.addEventListener("orientationchange", onChange);
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", onChange);
      window.visualViewport.addEventListener("scroll", onChange);
    }
  }

  function clearFsViewportStyles(el) {
    if (!el) return;
    el.style.removeProperty("--yl-rv-vvw");
    el.style.removeProperty("--yl-rv-vvh");
    el.style.removeProperty("--yl-rv-vvt");
    el.style.removeProperty("--yl-rv-vvl");
    el.style.top = "";
    el.style.left = "";
    el.style.width = "";
    el.style.height = "";
  }

  function openFullscreen(slug, sourceVideo) {
    var resolved = resolveFsSlug(slug, sourceVideo);
    if (!resolved) return;
    var el = ensureFullscreen();
    fs.open = true;
    fs.slug = resolved;
    fs._bodyScrollY = window.scrollY || window.pageYOffset || 0;
    document.body.classList.add("yl-rv-fs-open");
    if (isIOS()) document.body.classList.add("yl-rv-fs-open--ios");
    if (isAndroid()) document.body.classList.add("yl-rv-fs-open--android");
    el.hidden = false;
    el.classList.add("is-open");
    setThemeColor("#000000");
    bindFsViewportSync();
    syncFsViewport();
    window.requestAnimationFrame(syncFsViewport);
    // Pause / hide page videos first so native maximize cannot stay visible.
    pauseAllVideos(document.getElementById("yl-rv-fs-player"));
    if (sourceVideo) exitNativeFullscreen(sourceVideo);
    exitNativeFullscreen(null);
    loadFullscreenVideo(resolved, true);
    revealFsChrome(true);
    // Do not call browser requestFullscreen — phones steal gestures.
  }

  function closeFullscreen() {
    var el = document.getElementById("yl-rv-fs");
    var player = document.getElementById("yl-rv-fs-player");
    var scrollY = fs._bodyScrollY || 0;
    clearFsChromeTimer();
    fs.open = false;
    fs.slug = "";
    fs.chromeVisible = true;
    document.body.classList.remove("yl-rv-fs-open", "yl-rv-fs-open--ios", "yl-rv-fs-open--android");
    restoreThemeColor();
    exitShellFullscreen();
    if (player) {
      clearWatchTracking(player);
      try {
        player.pause();
      } catch (e) {}
      player.removeAttribute("src");
      exitNativeFullscreen(player);
    }
    if (el) {
      el.hidden = true;
      el.classList.remove("is-open", "yl-rv-fs--chrome-hidden", "yl-rv-fs--chrome-visible");
      clearFsViewportStyles(el);
    }
    window.scrollTo(0, scrollY);
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

  function hardenVideoAgainstNativeFs(video) {
    if (!video) return;
    try {
      video.setAttribute("playsinline", "");
      video.setAttribute("webkit-playsinline", "");
      video.setAttribute("x5-playsinline", "true");
      video.setAttribute("controlslist", "nofullscreen nodownload noremoteplayback");
      video.disablePictureInPicture = true;
      // Critical: phones always show a native maximize with controls.
      // That native layer sits on top of custom FS — never enable it on page videos.
      if (isPhonePlayer() || video.id !== "yl-rv-fs-player") {
        video.removeAttribute("controls");
      }
      // Desktop page videos also skip controls — play via overlay / Fullscreen button.
      // Only the desktop custom FS player may use native controls.
      if (video.id === "yl-rv-fs-player" && !isPhonePlayer()) {
        video.setAttribute("controls", "");
      }
    } catch (e) {}
  }

  function blockNativeFullscreenApi(video, onAttempt) {
    if (!video) return;
    var handler =
      onAttempt ||
      function () {
        exitNativeFullscreen(video);
      };
    try {
      video.requestFullscreen = function () {
        handler();
        return Promise.resolve();
      };
      if (video.webkitRequestFullscreen) video.webkitRequestFullscreen = handler;
      if (video.webkitRequestFullScreen) video.webkitRequestFullScreen = handler;
      if (typeof video.webkitEnterFullscreen === "function") {
        video.webkitEnterFullscreen = handler;
      }
      if (typeof video.webkitEnterFullScreen === "function") {
        video.webkitEnterFullScreen = handler;
      }
    } catch (e) {}
  }

  function bindFsPlayerNativeBlock(player) {
    if (!player || player._ylRvFsBound) return;
    player._ylRvFsBound = true;
    hardenVideoAgainstNativeFs(player);

    function stayInCustom() {
      exitNativeFullscreen(player);
      window.setTimeout(function () {
        exitNativeFullscreen(player);
      }, 0);
    }

    blockNativeFullscreenApi(player, stayInCustom);
    player.addEventListener("webkitbeginfullscreen", stayInCustom);
    player.addEventListener("fullscreenchange", function () {
      if (document.fullscreenElement === player) stayInCustom();
    });
  }

  function bindNativeFullscreenRedirect(video) {
    if (!video || video._ylRvFsBound) return;
    if (video.id === "yl-rv-fs-player") {
      bindFsPlayerNativeBlock(video);
      return;
    }
    video._ylRvFsBound = true;
    hardenVideoAgainstNativeFs(video);

    // Never open custom under a live native FS session — that is the
    // "default on top, custom after exit" bug. Only dismiss native if it appears.
    function dismissNativeOnly() {
      exitNativeFullscreen(video);
      window.setTimeout(function () {
        exitNativeFullscreen(video);
      }, 0);
    }

    blockNativeFullscreenApi(video, dismissNativeOnly);
    video.addEventListener("fullscreenchange", function () {
      if (document.fullscreenElement === video) dismissNativeOnly();
    });
    video.addEventListener("webkitfullscreenchange", function () {
      if (document.webkitFullscreenElement === video) dismissNativeOnly();
    });
    video.addEventListener("webkitbeginfullscreen", dismissNativeOnly);
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
      applyPageVideoChrome(desktopPlayer);
      bindWatchTracking(desktopPlayer, desktopWrap);
      bindNativeFullscreenRedirect(desktopPlayer);
      if (!desktopPlayer._ylRvPlayUiBound) {
        desktopPlayer._ylRvPlayUiBound = true;
        desktopPlayer.addEventListener("play", function () {
          desktopWrap.classList.add("is-playing");
        });
        desktopPlayer.addEventListener("pause", function () {
          desktopWrap.classList.remove("is-playing");
        });
        desktopPlayer.addEventListener("ended", function () {
          desktopWrap.classList.remove("is-playing");
        });
        desktopPlayer.addEventListener("click", function () {
          if (desktopPlayer.paused) tryAutoplay(desktopPlayer);
          else {
            try {
              desktopPlayer.pause();
            } catch (e) {}
          }
        });
      }
    }
    document.querySelectorAll(".yl-rv__card-video").forEach(function (video) {
      applyPageVideoChrome(video);
      bindNativeFullscreenRedirect(video);
    });
    document.querySelectorAll(".yl-rv__card").forEach(function (card) {
      var video = card.querySelector(".yl-rv__card-video");
      if (!video || video._ylRvPlayUiBound) return;
      video._ylRvPlayUiBound = true;
      video.addEventListener("play", function () {
        card.classList.add("is-playing");
      });
      video.addEventListener("pause", function () {
        card.classList.remove("is-playing");
      });
      video.addEventListener("ended", function () {
        card.classList.remove("is-playing");
      });
      video.addEventListener("click", function () {
        if (video.paused) tryAutoplay(video);
        else {
          try {
            video.pause();
          } catch (e) {}
        }
      });
    });

    document.addEventListener("fullscreenchange", function () {
      var node = document.fullscreenElement || document.webkitFullscreenElement;
      if (!node) return;
      if (node.id === "yl-rv-fs") return;
      var video =
        node.tagName === "VIDEO"
          ? node
          : node.querySelector && node.querySelector(".yl-rv video, #yl-rv-fs-player");
      if (!video) return;
      if (video.id === "yl-rv-fs-player" || (video.closest && video.closest(".yl-rv"))) {
        exitNativeFullscreen(video);
      }
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

        var playerStart = event.target.closest(".yl-rv__player-start");
        if (playerStart) {
          event.preventDefault();
          event.stopPropagation();
          selectDesktop(playerStart.getAttribute("data-slug") || currentPageSlug(), true);
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

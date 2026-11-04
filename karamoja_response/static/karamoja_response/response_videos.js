(function () {
  "use strict";

  var LIKED_KEY = "response_liked_videos";
  var playlistBySlug = {};
  var playlistOrder = [];
  var DESKTOP_MQ = window.matchMedia("(min-width: 900px)");
  var theater = {
    open: false,
    slug: "",
    touchStartX: 0,
    touchStartY: 0,
    touchActive: false,
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

    var slug = wrap.getAttribute("data-video-slug") || wrap.getAttribute("data-slug") || theater.slug;
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
            var theaterViews = document.getElementById("yl-rv-theater-views");
            if (theaterViews && theater.slug === slug) {
              theaterViews.textContent = result.data.views_display;
            }
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
    document.querySelectorAll(".yl-rv video, #yl-rv-theater-player").forEach(function (video) {
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
    player.removeAttribute("src");
    if (item.poster) {
      player.setAttribute("poster", item.poster);
    } else {
      player.removeAttribute("poster");
    }
    player.src = item.src || "";
    player.load();

    if (wrap) {
      wrap.setAttribute("data-video-slug", slug);
      wrap.setAttribute("data-video-duration", item.duration || "0");
      wrap.removeAttribute("data-view-counted");
      if (!skipScroll) wrap.scrollIntoView({ behavior: "smooth", block: "start" });
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
      var maxBtn = engagement.querySelector(".yl-rv__max-btn");
      if (maxBtn) maxBtn.setAttribute("data-slug", slug);
      if (views) views.textContent = item.views || "0";
      if (likes) likes.textContent = item.likes || "0";
    }

    document.querySelectorAll(".yl-rv__thumb").forEach(function (el) {
      var active = el.getAttribute("data-slug") === slug;
      el.classList.toggle("is-active", active);
      el.setAttribute("aria-pressed", active ? "true" : "false");
    });

    bindWatchTracking(player, wrap);
    if (shouldPlay) tryAutoplay(player);
  }

  function playMobileCard(slug) {
    var card = document.querySelector('.yl-rv__card[data-slug="' + slug + '"]');
    if (!card) return;
    var video = card.querySelector(".yl-rv__card-video");
    var item = playlistBySlug[slug];
    if (!video) return;

    pauseAllVideos(video);

    var src = video.getAttribute("src") || video.getAttribute("data-src") || (item && item.src) || "";
    if (!src) return;
    if (!video.getAttribute("src")) {
      video.setAttribute("src", src);
      video.load();
    }

    card.classList.add("is-playing");
    card.removeAttribute("data-view-counted");
    card.setAttribute("data-video-slug", slug);
    bindWatchTracking(video, card);
    card.scrollIntoView({ behavior: "smooth", block: "nearest" });
    tryAutoplay(video);
  }

  function exitNativeFullscreen(video) {
    try {
      if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitFullscreenElement && document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      }
    } catch (e) {}
    try {
      if (video && video.webkitDisplayingFullscreen && video.webkitExitFullscreen) {
        video.webkitExitFullscreen();
      }
    } catch (e) {}
  }

  function slugFromVideoEl(video) {
    if (!video) return currentPageSlug();
    if (video.id === "yl-rv-theater-player") return theater.slug || currentPageSlug();
    var card = video.closest(".yl-rv__card");
    if (card) return card.getAttribute("data-slug") || "";
    var wrap = video.closest(".yl-rv__player-wrap");
    if (wrap) return wrap.getAttribute("data-video-slug") || "";
    return currentPageSlug();
  }

  function bindNativeFullscreenRedirect(video) {
    if (!video || video._ylRvFsBound) return;
    video._ylRvFsBound = true;
    var redirecting = false;

    function redirectFromNative() {
      if (redirecting) return;
      if (theater.open) {
        exitNativeFullscreen(video);
        return;
      }
      if (playlistOrder.length < 1) return;
      redirecting = true;
      var slug = slugFromVideoEl(video);
      exitNativeFullscreen(video);
      window.setTimeout(function () {
        openTheater(slug);
        redirecting = false;
      }, 40);
    }

    video.addEventListener("fullscreenchange", function () {
      if (document.fullscreenElement === video) redirectFromNative();
    });
    video.addEventListener("webkitfullscreenchange", function () {
      if (document.webkitFullscreenElement === video) redirectFromNative();
    });
    // iPhone/iPad native player maximize
    video.addEventListener("webkitbeginfullscreen", function () {
      redirectFromNative();
    });
  }

  function bindSwipeSurface(surface) {
    if (!surface || surface._ylRvSwipeBound) return;
    surface._ylRvSwipeBound = true;

    surface.addEventListener(
      "touchstart",
      function (event) {
        if (!event.touches || !event.touches.length) return;
        theater.touchActive = true;
        theater.touchStartX = event.touches[0].clientX;
        theater.touchStartY = event.touches[0].clientY;
      },
      { passive: true }
    );

    surface.addEventListener(
      "touchend",
      function (event) {
        if (!theater.touchActive || !event.changedTouches || !event.changedTouches.length) return;
        theater.touchActive = false;
        var dx = event.changedTouches[0].clientX - theater.touchStartX;
        var dy = event.changedTouches[0].clientY - theater.touchStartY;
        var absX = Math.abs(dx);
        var absY = Math.abs(dy);
        if (Math.max(absX, absY) < 50) return;
        if (absY >= absX) {
          stepTheater(dy < 0 ? 1 : -1);
        } else {
          stepTheater(dx < 0 ? 1 : -1);
        }
      },
      { passive: true }
    );

    // Desktop drag swipe
    var drag = { active: false, x: 0, y: 0 };
    surface.addEventListener("pointerdown", function (event) {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      drag.active = true;
      drag.x = event.clientX;
      drag.y = event.clientY;
    });
    surface.addEventListener("pointerup", function (event) {
      if (!drag.active) return;
      drag.active = false;
      var dx = event.clientX - drag.x;
      var dy = event.clientY - drag.y;
      var absX = Math.abs(dx);
      var absY = Math.abs(dy);
      if (Math.max(absX, absY) < 60) return;
      if (absY >= absX) stepTheater(dy < 0 ? 1 : -1);
      else stepTheater(dx < 0 ? 1 : -1);
    });
  }

  function ensureTheater() {
    var existing = document.getElementById("yl-rv-theater");
    if (existing) return existing;

    var el = document.createElement("div");
    el.id = "yl-rv-theater";
    el.className = "yl-rv-theater";
    el.hidden = true;
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    el.setAttribute("aria-label", "Video viewer");
    el.innerHTML =
      '<div class="yl-rv-theater__frame">' +
      '<button type="button" class="yl-rv-theater__close" aria-label="Close">×</button>' +
      '<button type="button" class="yl-rv-theater__nav yl-rv-theater__nav--prev" aria-label="Previous video">‹</button>' +
      '<button type="button" class="yl-rv-theater__nav yl-rv-theater__nav--next" aria-label="Next video">›</button>' +
      '<div class="yl-rv-theater__stage">' +
      '<video id="yl-rv-theater-player" class="yl-rv-theater__player" controls playsinline controlslist="nofullscreen nodownload"></video>' +
      '<div class="yl-rv-theater__swipe" aria-hidden="true"></div>' +
      "</div>" +
      '<div class="yl-rv-theater__meta">' +
      '<p class="yl-rv-theater__title" id="yl-rv-theater-title"></p>' +
      '<p class="yl-rv-theater__count"><span id="yl-rv-theater-index">1</span> / <span id="yl-rv-theater-total">1</span> · <span id="yl-rv-theater-views">0</span> views</p>' +
      '<p class="yl-rv-theater__hint">Swipe left/right or tap ‹ › for more videos</p>' +
      "</div></div>";
    document.body.appendChild(el);

    el.querySelector(".yl-rv-theater__close").addEventListener("click", closeTheater);
    el.querySelector(".yl-rv-theater__nav--prev").addEventListener("click", function () {
      stepTheater(-1);
    });
    el.querySelector(".yl-rv-theater__nav--next").addEventListener("click", function () {
      stepTheater(1);
    });

    bindSwipeSurface(el.querySelector(".yl-rv-theater__swipe"));
    bindNativeFullscreenRedirect(el.querySelector("#yl-rv-theater-player"));

    return el;
  }

  function updateTheaterChrome(slug) {
    var item = playlistBySlug[slug];
    var index = playlistIndex(slug);
    var title = document.getElementById("yl-rv-theater-title");
    var indexEl = document.getElementById("yl-rv-theater-index");
    var totalEl = document.getElementById("yl-rv-theater-total");
    var viewsEl = document.getElementById("yl-rv-theater-views");
    var prevBtn = document.querySelector(".yl-rv-theater__nav--prev");
    var nextBtn = document.querySelector(".yl-rv-theater__nav--next");
    if (title) title.textContent = (item && item.title) || "";
    if (indexEl) indexEl.textContent = String(index + 1);
    if (totalEl) totalEl.textContent = String(playlistOrder.length);
    if (viewsEl) viewsEl.textContent = (item && item.views) || "0";
    if (prevBtn) prevBtn.disabled = index <= 0;
    if (nextBtn) nextBtn.disabled = index < 0 || index >= playlistOrder.length - 1;
  }

  function loadTheaterVideo(slug, shouldPlay) {
    var item = playlistBySlug[slug];
    var player = document.getElementById("yl-rv-theater-player");
    var shell = document.getElementById("yl-rv-theater");
    if (!item || !player || !shell) return;

    theater.slug = slug;
    clearWatchTracking(player);
    pauseAllVideos(player);
    player.pause();
    player.removeAttribute("src");
    if (item.poster) player.setAttribute("poster", item.poster);
    else player.removeAttribute("poster");
    player.src = item.src || "";
    player.load();
    shell.setAttribute("data-video-slug", slug);
    shell.setAttribute("data-video-duration", item.duration || "0");
    shell.removeAttribute("data-view-counted");
    updateTheaterChrome(slug);
    bindWatchTracking(player, shell);
    if (shouldPlay) tryAutoplay(player);

    // Keep page players in sync with theater selection
    if (DESKTOP_MQ.matches) {
      selectDesktop(slug, false, true);
    }
  }

  function openTheater(slug) {
    if (!slug || !playlistBySlug[slug] || playlistOrder.length < 1) return;
    var el = ensureTheater();
    theater.open = true;
    document.body.classList.add("yl-rv-theater-open");
    el.hidden = false;
    loadTheaterVideo(slug, true);
  }

  function closeTheater() {
    var el = document.getElementById("yl-rv-theater");
    var player = document.getElementById("yl-rv-theater-player");
    theater.open = false;
    theater.slug = "";
    document.body.classList.remove("yl-rv-theater-open");
    if (player) {
      clearWatchTracking(player);
      try {
        player.pause();
      } catch (e) {}
      player.removeAttribute("src");
    }
    if (el) el.hidden = true;
  }

  function stepTheater(delta) {
    if (!theater.open || !theater.slug) return;
    var next = neighborSlug(theater.slug, delta);
    if (!next) return;
    loadTheaterVideo(next, true);
  }

  function currentPageSlug() {
    if (theater.open && theater.slug) return theater.slug;
    if (DESKTOP_MQ.matches) {
      var wrap = document.querySelector(".yl-rv__player-wrap");
      return (wrap && wrap.getAttribute("data-video-slug")) || playlistOrder[0] || "";
    }
    var playing = document.querySelector(".yl-rv__card.is-playing");
    if (playing) return playing.getAttribute("data-slug") || "";
    return playlistOrder[0] || "";
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
    ensureTheater();

    var desktopPlayer = document.getElementById("yl-rv-player");
    var desktopWrap = document.querySelector(".yl-rv__player-wrap");
    if (desktopPlayer && desktopWrap) {
      bindWatchTracking(desktopPlayer, desktopWrap);
      bindNativeFullscreenRedirect(desktopPlayer);
    }
    document.querySelectorAll(".yl-rv__card-video").forEach(function (video) {
      bindNativeFullscreenRedirect(video);
    });

    // If the page/container goes fullscreen with our video inside, open theater instead.
    function onDocumentFullscreen() {
      var fs =
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.msFullscreenElement;
      if (!fs || theater.open) return;
      var video = fs.matches && fs.matches("video") ? fs : fs.querySelector && fs.querySelector("video");
      if (!video || !video.closest || !video.closest(".yl-rv")) return;
      var slug = slugFromVideoEl(video);
      exitNativeFullscreen(video);
      window.setTimeout(function () {
        openTheater(slug);
      }, 40);
    }
    document.addEventListener("fullscreenchange", onDocumentFullscreen);
    document.addEventListener("webkitfullscreenchange", onDocumentFullscreen);

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

        var maxBtn = event.target.closest(".yl-rv__max-btn");
        if (maxBtn) {
          event.preventDefault();
          event.stopPropagation();
          openTheater(maxBtn.getAttribute("data-slug") || currentPageSlug());
          return;
        }

        var cardStart = event.target.closest(".yl-rv__card-start");
        if (cardStart) {
          event.preventDefault();
          event.stopPropagation();
          playMobileCard(cardStart.getAttribute("data-slug"));
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

    // Double-tap / double-click a playing video opens max view
    document.addEventListener("dblclick", function (event) {
      var video = event.target.closest(".yl-rv__player, .yl-rv__card-video");
      if (!video) return;
      event.preventDefault();
      var card = video.closest(".yl-rv__card");
      var wrap = video.closest(".yl-rv__player-wrap");
      var slug =
        (card && card.getAttribute("data-slug")) ||
        (wrap && wrap.getAttribute("data-video-slug")) ||
        currentPageSlug();
      openTheater(slug);
    });

    document.addEventListener("keydown", function (event) {
      if (!theater.open) return;
      if (event.key === "Escape") {
        closeTheater();
        return;
      }
      if (event.key === "ArrowRight" || event.key === "ArrowUp") {
        event.preventDefault();
        stepTheater(1);
      } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
        event.preventDefault();
        stepTheater(-1);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

(function () {
  "use strict";

  var LIKED_KEY = "response_liked_videos";

  function getCsrfToken() {
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function apiBase() {
    var stage = document.getElementById("yl-rv-stage");
    return (stage && stage.getAttribute("data-api-base")) || "/karamoja-response/api/videos/";
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

  function bindWatchTracking(player, wrap) {
    if (!player || !wrap) return;
    var slug = wrap.getAttribute("data-video-slug");
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
            var viewsEl = document.querySelector(".yl-rv__views");
            if (viewsEl) viewsEl.textContent = result.data.views_display;
            document.querySelectorAll('.yl-rv__thumb[data-slug="' + slug + '"] .yl-rv__thumb-stats').forEach(function (el) {
              var likes = document.querySelector(".yl-rv__likes");
              el.textContent =
                result.data.views_display +
                " views · " +
                ((likes && likes.textContent) || "0") +
                " likes";
            });
          }
        })
        .catch(function () {
          pending = false;
        });
    }

    player.addEventListener("loadedmetadata", function () {
      if (!duration || duration === "0") threshold = viewThreshold(player.duration);
    });
    player.addEventListener("play", function () {
      last = player.currentTime;
    });
    player.addEventListener("seeked", function () {
      last = player.currentTime;
    });
    player.addEventListener("timeupdate", function () {
      var now = player.currentTime || 0;
      var delta = now - last;
      if (delta > 0 && delta < 2.5) watched += delta;
      last = now;
      tryRecord();
    });
  }

  function selectThumb(btn) {
    var player = document.getElementById("yl-rv-player");
    var wrap = document.querySelector(".yl-rv__player-wrap");
    var title = document.getElementById("yl-rv-title");
    var engagement = document.querySelector(".yl-rv__engagement");
    if (!player || !btn) return;

    var slug = btn.getAttribute("data-slug");
    var src = btn.getAttribute("data-src");
    var poster = btn.getAttribute("data-poster") || "";
    if (!slug || !src) return;

    player.pause();
    player.removeAttribute("src");
    player.poster = poster;
    player.src = src;
    player.load();

    if (wrap) {
      wrap.setAttribute("data-video-slug", slug);
      wrap.setAttribute("data-video-duration", btn.getAttribute("data-duration") || "0");
      wrap.removeAttribute("data-view-counted");
    }
    if (title) title.textContent = btn.getAttribute("data-title") || "";
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
        shareBtn.setAttribute("data-share-path", btn.getAttribute("data-share-path") || "");
        shareBtn.setAttribute("data-share-title", btn.getAttribute("data-title") || "");
      }
      if (views) views.textContent = btn.getAttribute("data-views") || "0";
      if (likes) likes.textContent = btn.getAttribute("data-likes") || "0";
    }

    document.querySelectorAll(".yl-rv__thumb").forEach(function (el) {
      var active = el === btn;
      el.classList.toggle("is-active", active);
      el.setAttribute("aria-pressed", active ? "true" : "false");
    });

    bindWatchTracking(player, wrap);
  }

  function init() {
    var player = document.getElementById("yl-rv-player");
    var wrap = document.querySelector(".yl-rv__player-wrap");
    if (!player) return;

    bindWatchTracking(player, wrap);

    var initialSlug = wrap && wrap.getAttribute("data-video-slug");
    if (initialSlug && readLiked().indexOf(initialSlug) !== -1) {
      setLikeUi(initialSlug, true);
    }

    document.addEventListener("click", function (event) {
      var likeBtn = event.target.closest(".yl-rv__like-btn");
      if (likeBtn) {
        event.preventDefault();
        likeVideo(likeBtn.getAttribute("data-video-slug"));
        return;
      }
      var shareBtn = event.target.closest(".yl-rv__share-btn");
      if (shareBtn) {
        event.preventDefault();
        shareVideo(shareBtn);
        return;
      }
      var thumb = event.target.closest(".yl-rv__thumb");
      if (thumb) {
        event.preventDefault();
        selectThumb(thumb);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

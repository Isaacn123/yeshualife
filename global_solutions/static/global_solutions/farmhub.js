(function () {
  "use strict";

  var LIKED_KEY = "farmhub_liked_videos";

  function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) {
      return meta.content;
    }
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function readLikedSlugs() {
    try {
      var raw = localStorage.getItem(LIKED_KEY);
      if (!raw) {
        return [];
      }
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function saveLikedSlug(slug) {
    var slugs = readLikedSlugs();
    if (slugs.indexOf(slug) === -1) {
      slugs.push(slug);
      localStorage.setItem(LIKED_KEY, JSON.stringify(slugs));
    }
  }

  function isLiked(slug) {
    return readLikedSlugs().indexOf(slug) !== -1;
  }

  function showToast(message) {
    var el = document.getElementById("fh-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "fh-toast";
      el.className = "fh-toast";
      el.setAttribute("role", "status");
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.add("is-visible");
    window.clearTimeout(showToast._timer);
    showToast._timer = window.setTimeout(function () {
      el.classList.remove("is-visible");
    }, 2400);
  }

  function setLikeUi(container, liked, likesDisplay) {
    var btn = container.querySelector(".fh-like-btn");
    var countEl = container.querySelector(".fh-engagement-likes");
    if (btn) {
      btn.classList.toggle("is-liked", liked);
      btn.setAttribute("aria-pressed", liked ? "true" : "false");
      btn.disabled = liked;
    }
    if (countEl && likesDisplay !== undefined) {
      countEl.textContent = likesDisplay;
    }
  }

  function initLikedState() {
    document.querySelectorAll(".fh-engagement[data-video-slug]").forEach(function (container) {
      var slug = container.getAttribute("data-video-slug");
      if (slug && isLiked(slug)) {
        setLikeUi(container, true);
      }
    });
  }

  function likeVideo(slug, container) {
    var btn = container.querySelector(".fh-like-btn");
    if (!slug || !btn || btn.disabled) {
      return;
    }
    btn.disabled = true;

    fetch("/api/videos/" + encodeURIComponent(slug) + "/like/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": getCsrfToken(),
        "Content-Type": "application/json",
      },
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          btn.disabled = false;
          return;
        }
        saveLikedSlug(slug);
        document.querySelectorAll('.fh-engagement[data-video-slug="' + slug + '"]').forEach(function (el) {
          setLikeUi(el, true, result.data.likes_display);
        });
      })
      .catch(function () {
        btn.disabled = false;
      });
  }

  function shareVideo(btn) {
    var path = btn.getAttribute("data-share-path") || "";
    var title = btn.getAttribute("data-share-title") || document.title;
    var url = new URL(path, window.location.origin).href;

    if (navigator.share) {
      navigator.share({ title: title, url: url }).catch(function () {});
      return;
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(function () {
        showToast("Link copied to clipboard");
      });
      return;
    }

    window.prompt("Copy this link:", url);
  }

  function onClick(event) {
    var likeBtn = event.target.closest(".fh-like-btn");
    if (likeBtn) {
      event.preventDefault();
      event.stopPropagation();
      var container = likeBtn.closest(".fh-engagement");
      var slug = likeBtn.getAttribute("data-video-slug") || (container && container.getAttribute("data-video-slug"));
      if (container && slug) {
        likeVideo(slug, container);
      }
      return;
    }

    var shareBtn = event.target.closest(".fh-share-btn");
    if (shareBtn) {
      event.preventDefault();
      event.stopPropagation();
      shareVideo(shareBtn);
    }
  }

  document.addEventListener("DOMContentLoaded", initLikedState);
  document.addEventListener("click", onClick);
})();

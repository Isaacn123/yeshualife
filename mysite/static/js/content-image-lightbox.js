(function () {
  "use strict";

  var CONTENT_IMAGE_SELECTOR = [
    ".blog-content-section img:not(.image-blog-main)",
    ".fh-video-desc img",
    "main img.richtext-image:not(.image-blog-main)",
  ].join(",");

  var CONTENT_EMBED_SELECTOR = [
    ".blog-content-section .responsive-object",
    ".yl-article__video .responsive-object",
    ".fh-video-desc .responsive-object",
  ].join(",");

  var CONTENT_VIDEO_SELECTOR = [
    ".blog-content-section video",
    ".yl-article__video video",
    ".fh-video-desc video",
  ].join(",");

  var CONTENT_IFRAME_SELECTOR = [
    ".blog-content-section iframe",
    ".yl-article__video iframe",
    ".fh-video-desc iframe",
  ].join(",");

  function getFullImageUrl(img) {
    var parentLink = img.closest("a");
    if (parentLink) {
      var href = parentLink.getAttribute("href");
      if (href && (/\/media\//.test(href) || /\.(jpe?g|png|gif|webp|avif)(\?|$)/i.test(href))) {
        return href;
      }
    }
    return img.currentSrc || img.src;
  }

  function getCaption(el) {
    if (!el) {
      return "";
    }
    return (
      el.getAttribute("alt") ||
      el.getAttribute("title") ||
      el.getAttribute("aria-label") ||
      ""
    ).trim();
  }

  function withAutoplay(url) {
    if (!url) {
      return url;
    }
    if (/[?&]autoplay=1/.test(url)) {
      return url;
    }
    return url + (url.indexOf("?") === -1 ? "?" : "&") + "autoplay=1";
  }

  function isInlinePlayableEmbed(iframe) {
    var src = (iframe.getAttribute("src") || "").toLowerCase();
    return (
      /\/global-solutions\/embed\//.test(src) ||
      /\/farmhub\/embed\//.test(src) ||
      /youtube\.com\/embed\//.test(src) ||
      /youtube-nocookie\.com\/embed\//.test(src) ||
      /youtu\.be\//.test(src) ||
      /player\.vimeo\.com\//.test(src)
    );
  }

  function ensureEmbedReferrerPolicy(iframe) {
    if (!iframe) {
      return;
    }
    var src = (iframe.getAttribute("src") || "").toLowerCase();
    if (
      /youtube\.com\/embed\//.test(src) ||
      /youtube-nocookie\.com\/embed\//.test(src) ||
      /player\.vimeo\.com\//.test(src)
    ) {
      iframe.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
      // Help YouTube receive origin context when opened from lightbox too.
      if (!iframe.getAttribute("allow")) {
        iframe.setAttribute(
          "allow",
          "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        );
      }
    }
  }

  function markInlineEmbed(container, iframe) {
    container.classList.add("yl-inline-embed");
    iframe.classList.add("yl-inline-embed__iframe");
  }

  function initContentMediaLightbox() {
    var modalEl = document.getElementById("contentImageLightbox");
    if (!modalEl || !window.bootstrap || !window.bootstrap.Modal) {
      return;
    }

    var modalImg = modalEl.querySelector(".content-image-lightbox__img");
    var modalIframe = modalEl.querySelector(".content-image-lightbox__iframe");
    var modalVideo = modalEl.querySelector(".content-image-lightbox__video");
    var modalIframeWrap = modalEl.querySelector(".content-image-lightbox__iframe-wrap");
    var modalVideoWrap = modalEl.querySelector(".content-image-lightbox__video-wrap");
    var modalCaption = modalEl.querySelector(".content-image-lightbox__caption");
    var modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);

    function hideAllMedia() {
      if (modalImg) {
        modalImg.hidden = true;
        modalImg.removeAttribute("src");
      }
      if (modalIframe) {
        modalIframe.hidden = true;
        modalIframe.removeAttribute("src");
      }
      if (modalIframeWrap) {
        modalIframeWrap.hidden = true;
      }
      if (modalVideo) {
        modalVideo.hidden = true;
        modalVideo.pause();
        modalVideo.removeAttribute("src");
        modalVideo.removeAttribute("poster");
      }
      if (modalVideoWrap) {
        modalVideoWrap.hidden = true;
      }
    }

    function setCaption(text) {
      if (!modalCaption) {
        return;
      }
      var caption = (text || "").trim();
      modalCaption.textContent = caption;
      modalCaption.hidden = !caption;
    }

    function openImagePreview(img) {
      if (!modalImg) {
        return;
      }
      hideAllMedia();
      modalImg.src = getFullImageUrl(img);
      modalImg.alt = getCaption(img);
      modalImg.hidden = false;
      setCaption(getCaption(img));
      modal.show();
    }

    function openIframePreview(iframe) {
      if (!modalIframe || !modalIframeWrap) {
        return;
      }
      var src = iframe.getAttribute("src");
      if (!src) {
        return;
      }
      hideAllMedia();
      ensureEmbedReferrerPolicy(modalIframe);
      modalIframe.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
      modalIframe.src = withAutoplay(src);
      modalIframe.title = getCaption(iframe) || "Video preview";
      modalIframe.hidden = false;
      modalIframeWrap.hidden = false;
      setCaption(getCaption(iframe));
      modal.show();
    }

    function openVideoPreview(video) {
      if (!modalVideo || !modalVideoWrap) {
        return;
      }
      var src = video.currentSrc || video.getAttribute("src");
      if (!src && video.querySelector("source")) {
        src = video.querySelector("source").getAttribute("src");
      }
      if (!src) {
        return;
      }
      hideAllMedia();
      modalVideo.src = src;
      if (video.getAttribute("poster")) {
        modalVideo.setAttribute("poster", video.getAttribute("poster"));
      }
      modalVideo.hidden = false;
      modalVideoWrap.hidden = false;
      setCaption(getCaption(video));
      modal.show();
      modalVideo.play().catch(function () {
        /* autoplay may be blocked until user interacts */
      });
    }

    function bindClickable(el, handler, label) {
      if (!el || el.dataset.lightboxBound === "true") {
        return;
      }
      el.dataset.lightboxBound = "true";
      el.classList.add("content-lightbox-media");
      el.setAttribute("role", "button");
      el.setAttribute("tabindex", "0");
      el.setAttribute("aria-label", label);

      var activate = function (event) {
        if (event) {
          event.preventDefault();
          event.stopPropagation();
        }
        handler(el);
      };

      el.addEventListener("click", activate);
      el.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          activate(event);
        }
      });
    }

    document.querySelectorAll(CONTENT_IMAGE_SELECTOR).forEach(function (img) {
      bindClickable(img, openImagePreview, getCaption(img) || "View image preview");

      var parentLink = img.closest("a");
      if (parentLink && parentLink.dataset.lightboxBound !== "true") {
        parentLink.dataset.lightboxBound = "true";
        parentLink.addEventListener("click", function (event) {
          event.preventDefault();
          openImagePreview(img);
        });
      }
    });

    document.querySelectorAll(CONTENT_EMBED_SELECTOR).forEach(function (container) {
      var iframe = container.querySelector("iframe");
      if (!iframe) {
        return;
      }
      ensureEmbedReferrerPolicy(iframe);
      if (isInlinePlayableEmbed(iframe)) {
        markInlineEmbed(container, iframe);
        return;
      }
      bindClickable(container, function () {
        openIframePreview(iframe);
      }, getCaption(iframe) || "View video preview");
    });

    document.querySelectorAll(CONTENT_IFRAME_SELECTOR).forEach(function (iframe) {
      ensureEmbedReferrerPolicy(iframe);
      if (iframe.closest(".responsive-object") || iframe.closest(".content-lightbox-iframe-host")) {
        return;
      }
      if (isInlinePlayableEmbed(iframe)) {
        markInlineEmbed(iframe.parentElement || iframe, iframe);
        return;
      }

      var host = document.createElement("div");
      host.className = "content-lightbox-iframe-host";
      iframe.parentNode.insertBefore(host, iframe);
      host.appendChild(iframe);

      bindClickable(host, function () {
        openIframePreview(iframe);
      }, getCaption(iframe) || "View video preview");
    });

    document.querySelectorAll(CONTENT_VIDEO_SELECTOR).forEach(function (video) {
      if (video.closest(".fh-video-player-wrap") || video.closest(".fh-similar-clips")) {
        return;
      }
      bindClickable(video, openVideoPreview, getCaption(video) || "View video preview");
    });

    modalEl.addEventListener("hidden.bs.modal", hideAllMedia);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initContentMediaLightbox);
  } else {
    initContentMediaLightbox();
  }
})();

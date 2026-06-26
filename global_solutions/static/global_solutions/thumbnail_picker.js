(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function csrfToken() {
    var name = "csrftoken=";
    var parts = document.cookie.split(";");
    for (var i = 0; i < parts.length; i++) {
      var c = parts[i].trim();
      if (c.indexOf(name) === 0) return decodeURIComponent(c.substring(name.length));
    }
    return "";
  }

  async function postForm(url, data) {
    var body = new URLSearchParams();
    Object.keys(data).forEach(function (k) {
      body.append(k, data[k]);
    });
    var resp = await fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken() },
      body: body,
      credentials: "same-origin",
    });
    var text = await resp.text();
    var json = {};
    try {
      if (text) json = JSON.parse(text);
    } catch (e) {
      json = {};
    }
    if (!resp.ok) {
      var msg = (json && json.error) || ("Request failed: " + resp.status);
      if (json && json.detail) msg += " — " + json.detail;
      if (json && json.ffmpeg) msg += " (ffmpeg: " + json.ffmpeg + ")";
      throw new Error(msg);
    }
    return json;
  }

  async function getJson(url) {
    var resp = await fetch(url, { credentials: "same-origin" });
    var json = await resp.json();
    if (!resp.ok) {
      throw new Error((json && json.error) || ("Request failed: " + resp.status));
    }
    return json;
  }

  async function uploadImage(url, file) {
    var body = new FormData();
    body.append("image", file);
    var resp = await fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken() },
      body: body,
      credentials: "same-origin",
    });
    var json = await resp.json();
    if (!resp.ok) {
      throw new Error((json && json.error) || ("Upload failed: " + resp.status));
    }
    return json;
  }

  function expandUrls(map, videoId) {
    if (window.expandVideoApiUrlMap) {
      return window.expandVideoApiUrlMap(map, videoId);
    }
    return map;
  }

  function parseApiUrls() {
    var el = $("gs-video-api-urls");
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  function setStatus(section, text) {
    var el = section.querySelector(".gsu-thumbnail-status");
    if (el) el.textContent = text;
  }

  function selectedKey(section) {
    return section.getAttribute("data-selected-key") || "";
  }

  function markSelected(section, b2Key) {
    section.setAttribute("data-selected-key", b2Key || "");
    section.querySelectorAll(".gsu-thumbnail-option").forEach(function (btn) {
      var key = btn.getAttribute("data-b2-key") || "";
      btn.classList.toggle("is-selected", key && key === b2Key);
    });
  }

  function updateCurrentPoster(section, url) {
    var wrap = section.querySelector(".gsu-thumbnail-current");
    if (!wrap) return;
    if (!url) {
      wrap.innerHTML = "<strong>Current thumbnail:</strong> none yet";
      return;
    }
    wrap.innerHTML =
      "<strong>Current thumbnail:</strong>" +
      '<img src="' + url + "?t=" + Date.now() + '" alt="Current video thumbnail">';
  }

  function renderOptions(section, data) {
    var grid = section.querySelector(".gsu-thumbnail-options");
    if (!grid) return;
    grid.innerHTML = "";

    var items = (data.candidates || []).slice();
    if (data.custom) items.push(data.custom);

    if (!items.length) {
      grid.innerHTML = '<p class="help">No thumbnails yet. Click “Generate 3 options”.</p>';
      return;
    }

    var activeUrl = data.poster_url || "";
    items.forEach(function (item) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "gsu-thumbnail-option";
      btn.setAttribute("data-b2-key", item.b2_key);
      if (item.url === activeUrl) {
        btn.classList.add("is-selected");
        section.setAttribute("data-selected-key", item.b2_key);
      }
      btn.innerHTML =
        '<img src="' + item.url + "?t=" + Date.now() + '" alt="">' +
        "<span>" + (item.label || "Thumbnail") + "</span>";
      btn.addEventListener("click", function () {
        selectThumbnail(section, item.b2_key);
      });
      grid.appendChild(btn);
    });
  }

  async function selectThumbnail(section, b2Key) {
    var urls = section._gsUrls;
    if (!urls || !urls.thumbnails_select) return;
    setStatus(section, "Saving thumbnail…");
    try {
      var data = await postForm(urls.thumbnails_select, { b2_key: b2Key });
      markSelected(section, b2Key);
      updateCurrentPoster(section, data.poster_url);
      setStatus(section, "Thumbnail saved. It will appear on the public site immediately.");
    } catch (e) {
      setStatus(section, "Error: " + (e.message || String(e)));
    }
  }

  async function loadThumbnails(section) {
    var urls = section._gsUrls;
    if (!urls || !urls.thumbnails) return;
    setStatus(section, "Loading thumbnails…");
    var data = await getJson(urls.thumbnails);
    var video = section.querySelector(".gsu-thumbnail-preview-video");
    if (video && data.playback_url) {
      video.src = data.playback_url;
    }
    updateCurrentPoster(section, data.poster_url);
    renderOptions(section, data);
    setStatus(section, "Pick a thumbnail or upload your own image.");
  }

  async function generateThumbnails(section) {
    var urls = section._gsUrls;
    if (!urls || !urls.thumbnails_generate) return;
    setStatus(section, "Generating 3 thumbnails from the video…");
    var data = await postForm(urls.thumbnails_generate, {});
    var video = section.querySelector(".gsu-thumbnail-preview-video");
    if (video && data.playback_url) {
      video.src = data.playback_url;
    }
    updateCurrentPoster(section, data.poster_url);
    renderOptions(section, data);
    setStatus(section, "Choose the thumbnail you want, or upload a custom image.");
  }

  function wireControls(section) {
    var regen = section.querySelector(".gsu-thumbnail-regenerate");
    if (regen && !regen._gsBound) {
      regen._gsBound = true;
      regen.addEventListener("click", function () {
        generateThumbnails(section).catch(function (e) {
          setStatus(section, "Error: " + (e.message || String(e)));
        });
      });
    }

    var customInput = section.querySelector(".gsu-thumbnail-custom-input");
    if (customInput && !customInput._gsBound) {
      customInput._gsBound = true;
      customInput.addEventListener("change", function () {
        var file = customInput.files && customInput.files[0];
        if (!file) return;
        var urls = section._gsUrls;
        if (!urls || !urls.thumbnails_upload) return;
        setStatus(section, "Uploading custom thumbnail…");
        uploadImage(urls.thumbnails_upload, file)
          .then(function (data) {
            updateCurrentPoster(section, data.poster_url);
            renderOptions(section, data);
            if (data.custom) {
              markSelected(section, data.custom.b2_key);
            }
            setStatus(section, "Custom thumbnail saved.");
            customInput.value = "";
          })
          .catch(function (e) {
            setStatus(section, "Error: " + (e.message || String(e)));
          });
      });
    }
  }

  function initSection(section, urls) {
    if (!section || !urls) return;
    section.hidden = false;
    section._gsUrls = urls;
    wireControls(section);
    loadThumbnails(section).catch(function (e) {
      setStatus(section, "Error: " + (e.message || String(e)));
    });
  }

  function bootstrapFromUpload(urls, uploadData) {
    var section = $("gsu-thumbnail-section");
    if (!section) return;
    initSection(section, urls);
    if (uploadData && uploadData.candidates && uploadData.candidates.length) {
      updateCurrentPoster(section, uploadData.poster_url);
      renderOptions(section, {
        poster_url: uploadData.poster_url,
        candidates: uploadData.candidates,
        custom: null,
      });
      if (uploadData.playback_url) {
        var video = section.querySelector(".gsu-thumbnail-preview-video");
        if (video) video.src = uploadData.playback_url;
      }
      setStatus(section, "Upload complete. Choose a thumbnail below.");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var section = $("gsu-thumbnail-section");
    if (!section || section.hidden) return;
    var snippetRoot = document.getElementById("gs-snippet-root");
    var videoId = snippetRoot && snippetRoot.getAttribute("data-video-id");
    if (!videoId) return;
    var tpl = parseApiUrls();
    var urls = expandUrls(tpl, videoId);
    initSection(section, urls);
  });

  window.GsThumbnailPicker = {
    init: initSection,
    bootstrapFromUpload: bootstrapFromUpload,
  };
})();

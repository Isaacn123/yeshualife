(function () {
  "use strict";

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
    Object.keys(data || {}).forEach(function (k) {
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
      throw new Error((json && json.error) || ("Request failed: " + resp.status));
    }
    return json;
  }

  function parseApiUrls(block) {
    var el = block.querySelector(".yl-rv-api-json");
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  function setStatus(block, text, isError) {
    var el = block.querySelector(".gs-similar-status");
    if (el) {
      el.textContent = text;
      el.classList.toggle("gs-similar-status--error", !!isError);
    }
  }

  function setProgress(block, pct) {
    var bar = block.querySelector(".gs-similar-progress__bar");
    if (bar) bar.style.width = pct + "%";
  }

  async function uploadMultipart(file, urls, block) {
    setStatus(block, "Creating multipart upload…");
    var create = await postForm(urls.b2_create, {
      filename: file.name,
      content_type: file.type || "video/mp4",
    });
    var uploadId = create.upload_id;
    var partSize = 10 * 1024 * 1024;
    var totalParts = Math.ceil(file.size / partSize) || 1;
    var parts = [];

    for (var part = 1; part <= totalParts; part++) {
      var start = (part - 1) * partSize;
      var end = Math.min(start + partSize, file.size);
      var blob = file.slice(start, end);
      setStatus(block, "Uploading part " + part + " / " + totalParts + "…");
      var presign = await postForm(urls.b2_part_url, {
        upload_id: uploadId,
        part_number: String(part),
      });
      var put = await fetch(presign.url, { method: "PUT", body: blob });
      if (!put.ok) throw new Error("Part upload failed: " + put.status);
      var etag = put.headers.get("ETag") || put.headers.get("etag");
      if (!etag) throw new Error("Missing ETag from part upload.");
      parts.push({ PartNumber: part, ETag: etag });
      setProgress(block, Math.round((part / totalParts) * 100));
    }

    setStatus(block, "Completing upload…");
    return postForm(urls.b2_complete, {
      upload_id: uploadId,
      parts: JSON.stringify(parts),
      size_bytes: String(file.size),
    });
  }

  async function syncTitle(block) {
    var metaUrl = block.getAttribute("data-meta-url");
    var titleEl = block.querySelector(".yl-rv-title");
    if (!metaUrl || !titleEl) return;
    var title = (titleEl.value || "").trim();
    if (!title) return;
    await postForm(metaUrl, { title: title });
  }

  function initThumbnail(block, urls, complete) {
    var section = block.querySelector(".yl-rv-thumbs");
    if (!section || !window.GsThumbnailPicker) return;
    section.hidden = false;
    if (complete && window.GsThumbnailPicker.bootstrapSection) {
      window.GsThumbnailPicker.bootstrapSection(section, urls, complete);
      return;
    }
    window.GsThumbnailPicker.init(section, urls);
  }

  async function uploadBlock(block) {
    var urls = parseApiUrls(block);
    var fileInput = block.querySelector(".yl-rv-file");
    if (!urls || !fileInput || !fileInput.files || !fileInput.files.length) {
      throw new Error("Choose a video file first.");
    }
    var uploadBtn = block.querySelector(".yl-rv-upload");
    if (uploadBtn) uploadBtn.disabled = true;
    try {
      await syncTitle(block);
      var complete = await uploadMultipart(fileInput.files[0], urls, block);
      setStatus(block, "Upload complete. Choose a thumbnail below.", false);
      if (uploadBtn) uploadBtn.textContent = "Replace video on B2";
      initThumbnail(block, urls, complete);
    } finally {
      if (uploadBtn) uploadBtn.disabled = false;
    }
  }

  function removeBlock(block) {
    if (!window.confirm("Delete this video?")) return Promise.resolve(false);
    var deleteUrl = block.getAttribute("data-delete-url");
    if (!deleteUrl) {
      block.remove();
      return Promise.resolve(true);
    }
    return postForm(deleteUrl, {})
      .then(function () {
        block.remove();
        return true;
      })
      .catch(function (e) {
        setStatus(block, "Delete failed: " + (e.message || String(e)), true);
        return false;
      });
  }

  function listBlocks() {
    return Array.prototype.slice.call(document.querySelectorAll("#yl-rv-video-list .yl-rv-block"));
  }

  async function persistOrder() {
    var blocks = listBlocks();
    for (var i = 0; i < blocks.length; i++) {
      var metaUrl = blocks[i].getAttribute("data-meta-url");
      if (!metaUrl) continue;
      await postForm(metaUrl, { sort_order: String(i + 1) });
    }
  }

  async function moveBlock(block, direction) {
    var blocks = listBlocks();
    var index = blocks.indexOf(block);
    if (index < 0) return;
    var swapWith = direction < 0 ? blocks[index - 1] : blocks[index + 1];
    if (!swapWith) return;
    if (direction < 0) {
      block.parentNode.insertBefore(block, swapWith);
    } else {
      block.parentNode.insertBefore(swapWith, block);
    }
    try {
      await persistOrder();
      setStatus(block, "Order updated. Reload the public page to see the new sequence.", false);
    } catch (e) {
      setStatus(block, "Could not save order: " + (e.message || String(e)), true);
    }
  }

  function wireBlock(block) {
    if (!block || block._ylRvBound) return;
    block._ylRvBound = true;

    var uploadBtn = block.querySelector(".yl-rv-upload");
    if (uploadBtn) {
      uploadBtn.addEventListener("click", function () {
        uploadBlock(block).catch(function (e) {
          setStatus(block, "Error: " + (e.message || String(e)), true);
        });
      });
    }

    var deleteBtn = block.querySelector(".yl-rv-delete");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", function () {
        removeBlock(block);
      });
    }

    var upBtn = block.querySelector(".yl-rv-move-up");
    if (upBtn) {
      upBtn.addEventListener("click", function () {
        moveBlock(block, -1);
      });
    }

    var downBtn = block.querySelector(".yl-rv-move-down");
    if (downBtn) {
      downBtn.addEventListener("click", function () {
        moveBlock(block, 1);
      });
    }

    var titleEl = block.querySelector(".yl-rv-title");
    if (titleEl) {
      titleEl.addEventListener("change", function () {
        syncTitle(block).catch(function () {});
      });
    }

    var urls = parseApiUrls(block);
    var section = block.querySelector(".yl-rv-thumbs");
    if (urls && section && !section.hidden && window.GsThumbnailPicker) {
      window.GsThumbnailPicker.init(section, urls);
    }
  }

  function buildBlockHtml(video) {
    var urlsJson = JSON.stringify(video.api_urls || {});
    var deleteUrl = (video.api_urls && video.api_urls.delete) || "";
    var metaUrl = (video.api_urls && video.api_urls.meta) || "";
    return (
      '<div class="gs-similar-block yl-rv-block" data-video-id="' +
      video.id +
      '" data-delete-url="' +
      deleteUrl +
      '" data-meta-url="' +
      metaUrl +
      '">' +
      '<script type="application/json" class="yl-rv-api-json">' +
      urlsJson +
      "<\/script>" +
      '<div class="gs-similar-block__head">' +
      '<div class="yl-rv-block__title-row" style="display:flex;gap:0.5rem;align-items:flex-end;flex-wrap:wrap;">' +
      '<div style="flex:1;min-width:12rem;">' +
      '<label class="w-field__label">Video title</label>' +
      '<input type="text" class="w-field__input yl-rv-title" maxlength="200" value="' +
      String(video.title || "").replace(/"/g, "&quot;") +
      '">' +
      "</div>" +
      '<div class="yl-rv-block__order" style="display:flex;gap:0.35rem;">' +
      '<button type="button" class="button button-secondary yl-rv-move-up" title="Move up">↑</button>' +
      '<button type="button" class="button button-secondary yl-rv-move-down" title="Move down">↓</button>' +
      "</div></div>" +
      '<p class="gs-similar-stats help">0 views · 0 likes · Status: draft</p>' +
      "</div>" +
      '<div class="gs-similar-block__upload">' +
      '<label class="w-field__label">Video file</label>' +
      '<input type="file" class="w-field__input yl-rv-file" accept="video/*">' +
      '<div class="gs-similar-block__upload-actions">' +
      '<button type="button" class="button yl-rv-upload">Upload to B2</button>' +
      '<button type="button" class="button button-secondary no yl-rv-delete">Delete</button>' +
      "</div>" +
      '<div class="gs-similar-progress"><div class="gs-similar-progress__bar"></div></div>' +
      '<div class="gs-similar-status help">No video yet.</div>' +
      "</div>" +
      '<div class="gsu-thumbnail-section yl-rv-thumbs" hidden>' +
      '<h4 class="gsu-thumbnail-section__title">Video thumbnail</h4>' +
      '<div class="gsu-thumbnail-layout">' +
      '<div><video class="gsu-thumbnail-preview-video" controls playsinline preload="metadata"></video>' +
      '<div class="gsu-thumbnail-current"><strong>Current thumbnail:</strong></div></div>' +
      '<div><div class="gsu-thumbnail-options"></div>' +
      '<div class="gsu-thumbnail-actions"><button type="button" class="button button-secondary gsu-thumbnail-regenerate">Generate 3 options</button></div>' +
      '<label class="gsu-thumbnail-custom">Or upload your own image' +
      '<input class="gsu-thumbnail-custom-input" type="file" accept="image/jpeg,image/png,image/webp"></label>' +
      '<div class="gsu-thumbnail-status help"></div></div></div></div></div>'
    );
  }

  function addVideo() {
    var root = document.getElementById("yl-rv-admin-root");
    if (!root) return;
    var createUrl = root.getAttribute("data-create-url");
    if (!createUrl) return;
    var btn = document.getElementById("yl-rv-add-video");
    if (btn) btn.disabled = true;
    postForm(createUrl, { title: "Untitled video" })
      .then(function (data) {
        var empty = document.getElementById("yl-rv-empty");
        if (empty) empty.remove();
        var list = document.getElementById("yl-rv-video-list");
        if (!list || !data.video) return;
        var wrap = document.createElement("div");
        wrap.innerHTML = buildBlockHtml(data.video);
        var block = wrap.firstElementChild;
        list.appendChild(block);
        wireBlock(block);
      })
      .catch(function (e) {
        window.alert("Could not add video: " + (e.message || String(e)));
      })
      .finally(function () {
        if (btn) btn.disabled = false;
      });
  }

  function init() {
    document.querySelectorAll(".yl-rv-block").forEach(wireBlock);
    var addBtn = document.getElementById("yl-rv-add-video");
    if (addBtn) addBtn.addEventListener("click", addVideo);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

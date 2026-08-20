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
    var el = block.querySelector(".gs-similar-api-json");
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
    block.classList.toggle("gs-similar-block--error", !!isError);
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
    var totalParts = Math.ceil(file.size / partSize);
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
    var titleEl = block.querySelector(".gs-similar-title");
    if (!metaUrl || !titleEl) return;
    var title = (titleEl.value || "").trim();
    if (!title) return;
    await postForm(metaUrl, { title: title });
  }

  function initThumbnail(block, urls, complete) {
    var section = block.querySelector(".gs-similar-thumbs");
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
    var fileInput = block.querySelector(".gs-similar-file");
    if (!urls || !fileInput || !fileInput.files || !fileInput.files.length) {
      throw new Error("Choose a video file first.");
    }
    var uploadBtn = block.querySelector(".gs-similar-upload");
    if (uploadBtn) uploadBtn.disabled = true;
    try {
      await syncTitle(block);
      var complete = await uploadMultipart(fileInput.files[0], urls, block);
      setStatus(block, "Upload complete. Choose a thumbnail below.", false);
      initThumbnail(block, urls, complete);
    } finally {
      if (uploadBtn) uploadBtn.disabled = false;
    }
  }

  function removeBlock(block) {
    if (!window.confirm("Delete this similar clip? This cannot be undone.")) {
      return Promise.resolve(false);
    }
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

  function wireBlock(block) {
    if (!block || block._gsSimilarBound) return;
    block._gsSimilarBound = true;

    var uploadBtn = block.querySelector(".gs-similar-upload");
    if (uploadBtn) {
      uploadBtn.addEventListener("click", function () {
        uploadBlock(block).catch(function (e) {
          setStatus(block, "Error: " + (e.message || String(e)), true);
        });
      });
    }

    var deleteBtn = block.querySelector(".gs-similar-delete");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", function () {
        removeBlock(block);
      });
    }

    var legacyRemoveBtn = block.querySelector(".gs-similar-remove");
    if (legacyRemoveBtn) {
      legacyRemoveBtn.addEventListener("click", function () {
        removeBlock(block);
      });
    }

    var titleEl = block.querySelector(".gs-similar-title");
    if (titleEl) {
      titleEl.addEventListener("change", function () {
        syncTitle(block).catch(function () {});
      });
    }

    var urls = parseApiUrls(block);
    var section = block.querySelector(".gs-similar-thumbs");
    if (urls && section && !section.hidden && window.GsThumbnailPicker) {
      window.GsThumbnailPicker.init(section, urls);
    }
  }

  function buildBlockFromTemplate(videoId, title, apiUrlsJson, deleteUrl, metaUrl) {
    var wrap = document.createElement("div");
    wrap.className = "gs-similar-block";
    wrap.setAttribute("data-video-id", videoId);
    wrap.setAttribute("data-delete-url", deleteUrl);
    wrap.setAttribute("data-meta-url", metaUrl);

    wrap.innerHTML =
      '<script type="application/json" class="gs-similar-api-json">' + apiUrlsJson + "<\/script>" +
      '<div class="gs-similar-block__head">' +
      '<label class="w-field__label">Clip title</label>' +
      '<input type="text" class="w-field__input gs-similar-title" maxlength="200" value="' + (title || "").replace(/"/g, "&quot;") + '">' +
      "</div>" +
      '<div class="gs-similar-block__upload">' +
      '<label class="w-field__label">Video file</label>' +
      '<input type="file" class="w-field__input gs-similar-file" accept="video/*">' +
      '<div class="gs-similar-block__upload-actions">' +
      '<button type="button" class="button gs-similar-upload">Upload to B2</button>' +
      '<button type="button" class="button button-secondary no gs-similar-delete">Delete clip</button>' +
      "</div>" +
      '<div class="gs-similar-progress"><div class="gs-similar-progress__bar"></div></div>' +
      '<div class="gs-similar-status help">No file yet</div>' +
      "</div>" +
      '<div class="gsu-thumbnail-section gs-similar-thumbs" hidden>' +
      '<h4 class="gsu-thumbnail-section__title">Thumbnail</h4>' +
      '<div class="gsu-thumbnail-layout">' +
      '<div><video class="gsu-thumbnail-preview-video" controls playsinline preload="metadata"></video>' +
      '<div class="gsu-thumbnail-current"><strong>Current thumbnail:</strong></div></div>' +
      '<div><div class="gsu-thumbnail-options"></div>' +
      '<div class="gsu-thumbnail-actions"><button type="button" class="button button-secondary gsu-thumbnail-regenerate">Generate 3 options</button></div>' +
      '<label class="gsu-thumbnail-custom">Or upload your own image<input class="gsu-thumbnail-custom-input" type="file" accept="image/jpeg,image/png,image/webp"></label>' +
      '<div class="gsu-thumbnail-status help"></div></div></div></div>';

    return wrap;
  }

  function defaultApiUrls(videoId) {
    var base = "/global-solutions/api/videos/" + videoId;
    return {
      meta: base + "/meta/",
      b2_create: base + "/b2/multipart/create/",
      b2_part_url: base + "/b2/multipart/part-url/",
      b2_complete: base + "/b2/multipart/complete/",
      thumbnails: base + "/thumbnails/",
      thumbnails_generate: base + "/thumbnails/generate/",
      thumbnails_select: base + "/thumbnails/select/",
      thumbnails_upload: base + "/thumbnails/upload/",
    };
  }

  document.addEventListener("DOMContentLoaded", function () {
    var list = document.getElementById("gs-similar-list");
    var addBtn = document.getElementById("gs-similar-add");
    if (!list || !addBtn) return;

    list.querySelectorAll(".gs-similar-block").forEach(wireBlock);

    addBtn.addEventListener("click", function () {
      var createUrl = list.getAttribute("data-create-url");
      if (!createUrl) return;
      addBtn.disabled = true;
      postForm(createUrl, {})
        .then(function (data) {
          var videoId = data.video_id;
          var urls = defaultApiUrls(videoId);
          var block = buildBlockFromTemplate(
            videoId,
            data.title || "",
            JSON.stringify(urls),
            "/global-solutions/api/videos/" + videoId + "/similar/delete/",
            "/global-solutions/api/videos/" + videoId + "/similar/meta/"
          );
          list.appendChild(block);
          wireBlock(block);
        })
        .catch(function (e) {
          window.alert(e.message || String(e));
        })
        .finally(function () {
          addBtn.disabled = false;
        });
    });
  });
})();

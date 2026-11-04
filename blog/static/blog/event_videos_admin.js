(function () {
  "use strict";

  function csrfToken() {
    var parts = document.cookie.split(";");
    for (var i = 0; i < parts.length; i++) {
      var c = parts[i].trim();
      if (c.indexOf("csrftoken=") === 0) return decodeURIComponent(c.substring(10));
    }
    return "";
  }

  function urlsFor(clipId) {
    var base = "/events/api/videos/" + clipId;
    return {
      meta: base + "/meta/",
      remove: base + "/delete/",
      create: base + "/r2/multipart/create/",
      part: base + "/r2/multipart/part-url/",
      complete: base + "/r2/multipart/complete/",
    };
  }

  async function postForm(url, data) {
    var body = new URLSearchParams();
    Object.keys(data || {}).forEach(function (key) {
      body.append(key, data[key]);
    });
    var resp = await fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken() },
      body: body,
      credentials: "same-origin",
    });
    var text = await resp.text();
    var trimmed = (text || "").trim();
    if (trimmed.charAt(0) === "<") {
      throw new Error(
        "The server returned an HTML error page instead of a result. Use this R2 upload button. The document field above cannot take a large video."
      );
    }
    var json = {};
    try {
      if (trimmed) json = JSON.parse(trimmed);
    } catch (e) {
      json = {};
    }
    if (!resp.ok) {
      throw new Error((json && json.error) || ("Upload failed (" + resp.status + ")."));
    }
    return json;
  }

  function setStatus(block, text, isError) {
    var el = block.querySelector(".yl-event-clip__status");
    if (!el) return;
    el.textContent = text;
    el.style.color = isError ? "#b00020" : "";
  }

  function setProgress(block, pct) {
    var bar = block.querySelector(".yl-event-clip__bar");
    if (bar) bar.style.width = pct + "%";
  }

  async function uploadClip(block) {
    var clipId = block.getAttribute("data-clip-id");
    var fileInput = block.querySelector(".yl-event-clip__file");
    if (!clipId || !fileInput || !fileInput.files || !fileInput.files.length) {
      throw new Error("Choose a video file first.");
    }
    var file = fileInput.files[0];
    var urls = urlsFor(clipId);
    var titleEl = block.querySelector(".yl-event-clip__title");
    if (titleEl && titleEl.value.trim()) {
      await postForm(urls.meta, { title: titleEl.value.trim() });
    }
    setStatus(block, "Starting upload to R2…", false);
    var created = await postForm(urls.create, {
      filename: file.name,
      content_type: file.type || "video/mp4",
    });
    var uploadId = created.upload_id;
    var partSize = 10 * 1024 * 1024;
    var total = Math.max(1, Math.ceil(file.size / partSize));
    var parts = [];
    for (var part = 1; part <= total; part++) {
      var start = (part - 1) * partSize;
      var end = Math.min(start + partSize, file.size);
      setStatus(block, "Uploading part " + part + " of " + total + "…", false);
      var presign = await postForm(urls.part, {
        upload_id: uploadId,
        part_number: String(part),
      });
      var put = await fetch(presign.url, { method: "PUT", body: file.slice(start, end) });
      if (!put.ok) {
        throw new Error("R2 rejected part " + part + " (" + put.status + ").");
      }
      var etag = put.headers.get("ETag") || put.headers.get("etag") || "";
      parts.push({ PartNumber: part, ETag: etag });
      setProgress(block, Math.round((part / total) * 100));
    }
    setStatus(block, "Finishing upload…", false);
    await postForm(urls.complete, {
      upload_id: uploadId,
      parts: JSON.stringify(parts),
      size_bytes: String(file.size),
    });
    setStatus(block, "Uploaded to R2.", false);
    var button = block.querySelector(".yl-event-clip__upload");
    if (button) button.textContent = "Replace on R2";
  }

  function buildBlock(data) {
    var block = document.createElement("div");
    block.className = "yl-event-clip";
    block.setAttribute("data-clip-id", data.id);
    block.setAttribute("data-primary", data.is_primary ? "1" : "0");
    var label = data.is_primary ? "Main video" : "Similar video";
    var removeLabel = data.is_primary ? "Clear video" : "Delete";
    block.innerHTML =
      '<label class="w-field__label">' + label + "</label>" +
      '<input type="text" class="w-field__input yl-event-clip__title" maxlength="200" value="' +
      String(data.title || "").replace(/"/g, "&quot;") + '">' +
      '<input type="file" class="w-field__input yl-event-clip__file" accept="video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov">' +
      '<div class="yl-event-clip__actions">' +
      '<button type="button" class="button yl-event-clip__upload">Upload to R2</button>' +
      '<button type="button" class="button button-secondary no yl-event-clip__delete">' + removeLabel + "</button>" +
      "</div>" +
      '<div class="yl-event-clip__progress"><div class="yl-event-clip__bar"></div></div>' +
      '<p class="help yl-event-clip__status">No video yet.</p>';
    return block;
  }

  function wire(block) {
    var uploadBtn = block.querySelector(".yl-event-clip__upload");
    if (uploadBtn) {
      uploadBtn.addEventListener("click", function () {
        uploadBtn.disabled = true;
        uploadClip(block)
          .catch(function (error) {
            setStatus(block, error.message || String(error), true);
          })
          .finally(function () {
            uploadBtn.disabled = false;
          });
      });
    }
    var deleteBtn = block.querySelector(".yl-event-clip__delete");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", function () {
        var clipId = block.getAttribute("data-clip-id");
        var primary = block.getAttribute("data-primary") === "1";
        if (!window.confirm(primary ? "Clear this video?" : "Delete this similar video?")) return;
        postForm(urlsFor(clipId).remove, {})
          .then(function () {
            if (primary) {
              setStatus(block, "No video yet.", false);
              setProgress(block, 0);
            } else {
              block.remove();
            }
          })
          .catch(function (error) {
            setStatus(block, error.message || String(error), true);
          });
      });
    }
  }

  function createClip(list, kind) {
    return postForm(list.getAttribute("data-create-url"), { kind: kind }).then(function (data) {
      var existing = list.querySelector('[data-clip-id="' + data.id + '"]');
      if (existing) {
        existing.scrollIntoView({ block: "center" });
        return existing;
      }
      var block = buildBlock(data);
      list.appendChild(block);
      wire(block);
      return block;
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var list = document.getElementById("yl-event-videos");
    if (!list) return;
    list.querySelectorAll(".yl-event-clip").forEach(wire);

    var mainBtn = document.getElementById("yl-event-upload-main");
    if (mainBtn) {
      mainBtn.addEventListener("click", function () {
        var existing = list.querySelector('[data-primary="1"]');
        if (existing) {
          existing.scrollIntoView({ block: "center" });
          var file = existing.querySelector(".yl-event-clip__file");
          if (file) file.focus();
          return;
        }
        mainBtn.disabled = true;
        createClip(list, "main")
          .catch(function (error) { window.alert(error.message || String(error)); })
          .finally(function () { mainBtn.disabled = false; });
      });
    }

    var addBtn = document.getElementById("yl-event-add-similar");
    if (addBtn) {
      addBtn.addEventListener("click", function () {
        addBtn.disabled = true;
        createClip(list, "similar")
          .catch(function (error) { window.alert(error.message || String(error)); })
          .finally(function () { addBtn.disabled = false; });
      });
    }
  });
})();

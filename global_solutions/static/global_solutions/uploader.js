(function () {
  function $(id) { return document.getElementById(id); }

  function setStatus(text) {
    var el = $("gsu-status");
    if (el) el.textContent = text;
  }

  function setProgress(pct) {
    var bar = $("gsu-progress");
    if (bar) bar.style.width = pct + "%";
  }

  function bytesToSize(bytes) {
    if (!bytes && bytes !== 0) return "";
    var units = ["B", "KB", "MB", "GB", "TB"];
    var i = 0;
    var num = bytes;
    while (num >= 1024 && i < units.length - 1) { num = num / 1024; i++; }
    return (Math.round(num * 10) / 10) + " " + units[i];
  }

  function baseName(filename) {
    var name = filename || "";
    name = name.split("/").pop().split("\\").pop();
    var idx = name.lastIndexOf(".");
    if (idx > 0) name = name.substring(0, idx);
    return name;
  }

  function ensureFilesContainer() {
    return $("gsu-files");
  }

  function renderFileRow(file) {
    var wrap = ensureFilesContainer();
    if (!wrap) return null;
    var row = document.createElement("div");
    row.className = "gsu-file-row";
    row.dataset.filename = file.name;

    var top = document.createElement("div");
    top.className = "gsu-file-top";

    var name = document.createElement("div");
    name.className = "gsu-file-name";
    name.textContent = file.name;

    var meta = document.createElement("div");
    meta.className = "gsu-file-meta";
    meta.textContent = bytesToSize(file.size);

    top.appendChild(name);
    top.appendChild(meta);

    var status = document.createElement("div");
    status.className = "gsu-file-status";
    status.textContent = "Queued";

    row.appendChild(top);
    row.appendChild(status);
    wrap.appendChild(row);
    return row;
  }

  function setRowStatus(row, text) {
    if (!row) return;
    var el = row.querySelector(".gsu-file-status");
    if (el) el.textContent = text;
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

  /** Fallback when ``#gs-video-api-urls`` is missing (older templates). */
  function defaultVideoApiUrls(videoId) {
    var base = "/global-solutions/api/videos/" + videoId;
    return {
      create: "/global-solutions/api/videos/create/",
      meta: base + "/meta/",
      b2_create: base + "/b2/multipart/create/",
      b2_part_url: base + "/b2/multipart/part-url/",
      b2_complete: base + "/b2/multipart/complete/",
      process: base + "/process/start/",
    };
  }

  function parseVideoApiUrlsJson() {
    var el = $("gs-video-api-urls");
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  /**
   * Expand Django ``json_script`` map: if it contains ``_placeholder`` UUID, swap in ``videoId``.
   * Snippet maps from the server have no placeholder and are returned as-is.
   */
  function expandVideoApiUrlMap(map, videoId) {
    if (!map) return defaultVideoApiUrls(videoId);
    var ph = map._placeholder;
    if (!ph) return map;
    var out = {};
    Object.keys(map).forEach(function (k) {
      if (k === "_placeholder") return;
      var v = map[k];
      out[k] = typeof v === "string" ? v.split(ph).join(videoId) : v;
    });
    return out;
  }

  async function postForm(url, data) {
    var body = new URLSearchParams();
    Object.keys(data).forEach(function (k) { body.append(k, data[k]); });
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
      try {
        if (resp.url) msg += " — " + resp.url;
      } catch (e2) { /* ignore */ }
      if (resp.status === 404 && !(json && json.error)) {
        msg +=
          " If this persists after deploy, open GET /global-solutions/api/ok/ while logged in as staff " +
          "(should return JSON). If that 404s too, nginx is not sending /global-solutions/ to Django.";
      }
      throw new Error(msg);
    }
    return json;
  }

  async function uploadMultipart(file, urls, onPartProgress) {
    setStatus("Creating multipart upload...");
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

      setStatus("Uploading part " + part + " / " + totalParts + " (" + Math.round((end / file.size) * 100) + "%) ...");
      var presign = await postForm(urls.b2_part_url, {
        upload_id: uploadId,
        part_number: String(part),
      });

      var put = await fetch(presign.url, { method: "PUT", body: blob });
      if (!put.ok) throw new Error("Part upload failed: " + put.status);

      var etag = put.headers.get("ETag") || put.headers.get("etag");
      if (!etag) throw new Error("Missing ETag from part upload response.");
      parts.push({ PartNumber: part, ETag: etag });

      var pct = Math.round((part / totalParts) * 100);
      setProgress(pct);
      if (onPartProgress) onPartProgress(pct, part, totalParts);
    }

    setStatus("Completing upload...");
    await postForm(urls.b2_complete, {
      upload_id: uploadId,
      parts: JSON.stringify(parts),
      size_bytes: String(file.size),
    });

    setStatus("Upload complete. You can mark for processing.");
    return true;
  }

  function snippetFormValue(name) {
    var el = document.querySelector("[name=\"" + name + "\"]");
    if (!el) return "";
    return (el.value || "").trim();
  }

  async function syncSnippetMeta(urls) {
    var category = snippetFormValue("category");
    var title = snippetFormValue("title");
    var description = snippetFormValue("description");
    if (!title) throw new Error("Enter a title in the Details section above (you can save the form after upload if you prefer).");
    if (!category) throw new Error("Choose a Category in the Details section.");
    await postForm(urls.meta, {
      category: category,
      title: title,
      description: description,
    });
  }

  function initSnippet(snippetRoot) {
    var uploadBtn = $("gsu-upload-btn");
    var processBtn = $("gsu-process-btn");
    if (!uploadBtn || !processBtn) return;

    var currentVideoId = snippetRoot.getAttribute("data-video-id");
    if (!currentVideoId) return;

    uploadBtn.addEventListener("click", async function () {
      try {
        var filesList = $("gsu-file").files;
        if (!filesList || !filesList.length) throw new Error("Select a video file to upload.");

        var tpl = parseVideoApiUrlsJson();
        var urls = expandVideoApiUrlMap(tpl, currentVideoId);

        uploadBtn.disabled = true;
        processBtn.disabled = true;
        setProgress(0);
        setStatus("Syncing title and type from this form…");

        await syncSnippetMeta(urls);

        var file = filesList[0];
        setStatus("Uploading…");
        await uploadMultipart(file, urls, function (pct) {
          setStatus("Uploading… " + pct + "%");
        });

        setStatus("Upload complete. Reloading…");
        window.location.reload();
      } catch (e) {
        setStatus("Error: " + (e && e.message ? e.message : String(e)));
      } finally {
        uploadBtn.disabled = false;
      }
    });

    processBtn.addEventListener("click", async function () {
      if (!currentVideoId) return;
      try {
        var tpl = parseVideoApiUrlsJson();
        var urls = expandVideoApiUrlMap(tpl, currentVideoId);
        processBtn.disabled = true;
        setStatus("Marking for processing…");
        await postForm(urls.process, {});
        setStatus("Marked for processing. Reloading…");
        window.location.reload();
      } catch (e) {
        setStatus("Error: " + (e && e.message ? e.message : String(e)));
      } finally {
        processBtn.disabled = false;
      }
    });
  }

  function initStandalone() {
    var uploadBtn = $("gsu-upload-btn");
    var processBtn = $("gsu-process-btn");
    if (!uploadBtn || !processBtn) return;

    var clearBtn = $("gsu-clear-btn");
    var currentVideoId = null;
    var urlTpl = parseVideoApiUrlsJson();

    uploadBtn.addEventListener("click", async function () {
      try {
        var categoryEl = $("gsu-category");
        var titleEl = $("gsu-title");
        var descEl = $("gsu-description");
        if (!categoryEl || !titleEl) return;

        var category = categoryEl.value;
        if (!category) throw new Error("Choose a category.");
        var titleBase = titleEl.value.trim();
        var description = descEl ? descEl.value.trim() : "";
        var filesList = $("gsu-file").files;
        var files = [];
        for (var i = 0; i < filesList.length; i++) files.push(filesList[i]);

        if (!files.length) throw new Error("Select one or more video files to upload.");

        uploadBtn.disabled = true;
        processBtn.disabled = true;
        setProgress(0);
        setStatus("Preparing uploads...");

        var wrap = ensureFilesContainer();
        if (wrap) wrap.innerHTML = "";
        var rows = files.map(renderFileRow);

        var createUrl = (urlTpl && urlTpl.create) ? urlTpl.create : defaultVideoApiUrls("00000000-0000-0000-0000-000000000000").create;

        for (var idx = 0; idx < files.length; idx++) {
          var file = files[idx];
          var row = rows[idx];
          var derived = baseName(file.name);
          var title = titleBase ? (files.length > 1 ? (titleBase + " - " + derived) : titleBase) : derived;

          setRowStatus(row, "Creating video record...");
          setStatus("Creating video record (" + (idx + 1) + " / " + files.length + ") ...");
          var created = await postForm(createUrl, {
            category: category,
            title: title,
            description: description,
          });
          currentVideoId = created.video_id;

          var urls = expandVideoApiUrlMap(urlTpl, currentVideoId);

          setRowStatus(row, "Uploading...");
          await uploadMultipart(file, urls, function (pct) {
            setRowStatus(row, "Uploading... " + pct + "%");
          });
          setRowStatus(row, "Uploaded. Ready to mark PROCESSING.");
        }

        processBtn.disabled = false;
        setStatus("All uploads complete. You can mark the last upload for processing.");
      } catch (e) {
        setStatus("Error: " + (e && e.message ? e.message : String(e)));
      } finally {
        uploadBtn.disabled = false;
      }
    });

    processBtn.addEventListener("click", async function () {
      if (!currentVideoId) return;
      try {
        var urls = expandVideoApiUrlMap(urlTpl, currentVideoId);
        processBtn.disabled = true;
        setStatus("Marking for processing...");
        await postForm(urls.process, {});
        setStatus("Marked PROCESSING. It will be processed automatically.");
      } catch (e) {
        setStatus("Error: " + (e && e.message ? e.message : String(e)));
      } finally {
        processBtn.disabled = false;
      }
    });

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        var wrap = ensureFilesContainer();
        if (wrap) wrap.innerHTML = "";
        setProgress(0);
        setStatus("Ready.");
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var snippetRoot = document.getElementById("gs-snippet-root");
    if (snippetRoot && snippetRoot.getAttribute("data-video-id")) {
      initSnippet(snippetRoot);
      return;
    }
    initStandalone();
  });
})();

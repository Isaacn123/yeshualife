(function () {
  function $(id) { return document.getElementById(id); }

  function setStatus(text) { $("gsu-status").textContent = text; }
  function setProgress(pct) { $("gsu-progress").style.width = pct + "%"; }

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
    // Remove path fragments just in case
    name = name.split("/").pop().split("\\").pop();
    // Remove extension
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

  async function postForm(url, data) {
    var body = new URLSearchParams();
    Object.keys(data).forEach(function (k) { body.append(k, data[k]); });
    var resp = await fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken() },
      body: body,
      credentials: "same-origin",
    });
    var json = await resp.json().catch(function () { return {}; });
    if (!resp.ok) throw new Error(json.error || ("Request failed: " + resp.status));
    return json;
  }

  async function uploadMultipart(videoId, file, onPartProgress) {
    setStatus("Creating multipart upload...");
    var create = await postForm("/global-solutions/api/videos/" + videoId + "/b2/multipart/create/", {
      filename: file.name,
      content_type: file.type || "video/mp4",
    });

    var uploadId = create.upload_id;
    var partSize = 10 * 1024 * 1024; // 10MB
    var totalParts = Math.ceil(file.size / partSize);
    var parts = [];

    for (var part = 1; part <= totalParts; part++) {
      var start = (part - 1) * partSize;
      var end = Math.min(start + partSize, file.size);
      var blob = file.slice(start, end);

      setStatus("Uploading part " + part + " / " + totalParts + " (" + Math.round((end / file.size) * 100) + "%) ...");
      var presign = await postForm("/global-solutions/api/videos/" + videoId + "/b2/multipart/part-url/", {
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
    await postForm("/global-solutions/api/videos/" + videoId + "/b2/multipart/complete/", {
      upload_id: uploadId,
      parts: JSON.stringify(parts),
      size_bytes: String(file.size),
    });

    setStatus("Upload complete. You can now mark for processing.");
    return true;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var uploadBtn = $("gsu-upload-btn");
    var processBtn = $("gsu-process-btn");
    var clearBtn = $("gsu-clear-btn");
    var currentVideoId = null;

    uploadBtn.addEventListener("click", async function () {
      try {
        var kind = $("gsu-kind").value;
        var titleBase = $("gsu-title").value.trim();
        var description = $("gsu-description").value.trim();
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

        for (var idx = 0; idx < files.length; idx++) {
          var file = files[idx];
          var row = rows[idx];
          var derived = baseName(file.name);
          var title = titleBase ? (files.length > 1 ? (titleBase + " - " + derived) : titleBase) : derived;

          setRowStatus(row, "Creating video record...");
          setStatus("Creating video record (" + (idx + 1) + " / " + files.length + ") ...");
          var created = await postForm("/global-solutions/api/videos/create/", {
            kind: kind,
            title: title,
            description: description,
          });
          currentVideoId = created.video_id;

          setRowStatus(row, "Uploading...");
          await uploadMultipart(currentVideoId, file, function (pct) {
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
        processBtn.disabled = true;
        setStatus("Marking for processing...");
        await postForm("/global-solutions/api/videos/" + currentVideoId + "/process/start/", {});
        setStatus("Marked PROCESSING. Run: python manage.py process_global_solutions_videos");
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
  });
})();


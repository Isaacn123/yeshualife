(function () {
  function $(id) { return document.getElementById(id); }

  function setStatus(text) { $("gsu-status").textContent = text; }
  function setProgress(pct) { $("gsu-progress").style.width = pct + "%"; }

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

  async function uploadMultipart(videoId, file) {
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

      setProgress(Math.round((part / totalParts) * 100));
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
    var currentVideoId = null;

    uploadBtn.addEventListener("click", async function () {
      try {
        var kind = $("gsu-kind").value;
        var title = $("gsu-title").value.trim();
        var description = $("gsu-description").value.trim();
        var file = $("gsu-file").files[0];

        if (!title) throw new Error("Title is required.");
        if (!file) throw new Error("Select a video file to upload.");

        uploadBtn.disabled = true;
        processBtn.disabled = true;
        setProgress(0);

        setStatus("Creating video record...");
        var created = await postForm("/global-solutions/api/videos/create/", {
          kind: kind,
          title: title,
          description: description,
        });
        currentVideoId = created.video_id;

        await uploadMultipart(currentVideoId, file);
        processBtn.disabled = false;
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
  });
})();


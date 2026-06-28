/* Status page JS — subscribes to the SSE stream and updates the UI. */

(function () {
  "use strict";

  var stepList = document.getElementById("step-list");
  var progressBar = document.getElementById("progress-bar");
  var progressLabel = document.getElementById("progress-label");
  var logPanel = document.getElementById("log-panel");
  var errorPanel = document.getElementById("error-panel");
  var errorMessage = document.getElementById("error-message");
  var errorDetail = document.getElementById("error-detail");
  var successPanel = document.getElementById("success-panel");

  var stepOrder = [
    "validate_inputs",
    "connect_database",
    "save_configuration",
    "write_env_file",
    "install_dependencies",
    "download_plugins",
    "generate_session",
    "start_bot",
  ];

  function setStepState(stepId, state) {
    var li = stepList.querySelector('li[data-step="' + stepId + '"]');
    if (!li) return;
    li.classList.remove("active", "done", "failed");
    if (state) li.classList.add(state);
  }

  function addLog(text, kind) {
    if (!text) return;
    var line = document.createElement("div");
    line.className = "log-line " + (kind || "");
    line.textContent = text;
    logPanel.appendChild(line);
    logPanel.scrollTop = logPanel.scrollHeight;
  }

  function handleEvent(event) {
    var stepId = event.step;
    var idx = stepOrder.indexOf(stepId);

    if (event.type === "step") {
      // Mark previous steps done
      if (idx > 0) {
        for (var i = 0; i < idx; i++) setStepState(stepOrder[i], "done");
      }
      setStepState(stepId, "active");
      progressBar.style.width = event.progress + "%";
      progressLabel.textContent = event.title + " — " + (event.message || "");
    } else if (event.type === "log") {
      // Only print "$ <title>" for actual subprocess commands (step
      // == "subprocess"). For bot stdout lines we set title="" so
      // this branch is skipped and only the message is shown.
      if (event.step === "subprocess" && event.title) {
        addLog("$ " + event.title, "cmd");
      }
      if (event.message) {
        // Bot stdout lines (step == "start_bot") get default styling;
        // subprocess stdout gets no special kind; everything else is "ok".
        var kind = event.step === "subprocess" ? "" : "ok";
        addLog(event.message, kind);
      }
    } else if (event.type === "completed") {
      for (var j = 0; j < stepOrder.length; j++) setStepState(stepOrder[j], "done");
      progressBar.style.width = "100%";
      progressLabel.textContent = "Deployment completed.";
      if (successPanel) successPanel.classList.remove("hidden");
      source.close();
    } else if (event.type === "failed") {
      setStepState(stepId, "failed");
      progressBar.style.width = event.progress + "%";
      progressLabel.textContent = "Failed: " + event.title;
      if (errorMessage) errorMessage.textContent = event.message || "Unknown error.";
      if (errorDetail) errorDetail.textContent = event.detail || "";
      if (errorPanel) errorPanel.classList.remove("hidden");
      source.close();
    }
  }

  // Retry button
  var btnRetry = document.getElementById("btn-retry");
  if (btnRetry) {
    btnRetry.addEventListener("click", function () {
      btnRetry.disabled = true;
      btnRetry.textContent = "Restarting...";
      fetch("/api/retry", { method: "POST" })
        .then(function () { window.location.href = "/review"; })
        .catch(function () { btnRetry.disabled = false; btnRetry.textContent = "↻ Retry deployment"; });
    });
  }

  // ------------------------------------------------------------------
  // Copy full log button
  // ------------------------------------------------------------------
  // Collects every log line (plus the error message + detail if the
  // deployment failed) into a single text block and copies it to the
  // clipboard. Falls back to a textarea + execCommand('copy') if the
  // async Clipboard API isn't available (older browsers, HTTP on HF).
  var btnCopyLog = document.getElementById("btn-copy-log");
  if (btnCopyLog) {
    btnCopyLog.addEventListener("click", function () {
      var parts = [];

      // 1. Step status summary
      var steps = stepList ? stepList.querySelectorAll("li") : [];
      if (steps.length > 0) {
        parts.push("=== Deployment Steps ===");
        steps.forEach(function (li) {
          var name = li.textContent.trim();
          var state = li.classList.contains("done") ? "[DONE]"
                    : li.classList.contains("active") ? "[ACTIVE]"
                    : li.classList.contains("failed") ? "[FAILED]"
                    : "[PENDING]";
          parts.push(state + " " + name);
        });
        parts.push("");
      }

      // 2. Progress label
      if (progressLabel) {
        parts.push("=== Status ===");
        parts.push(progressLabel.textContent);
        parts.push("");
      }

      // 3. Full log panel
      if (logPanel) {
        parts.push("=== Deployment Log ===");
        var lines = logPanel.querySelectorAll(".log-line");
        lines.forEach(function (line) {
          parts.push(line.textContent);
        });
        parts.push("");
      }

      // 4. Error details (if failed)
      var errMsg = document.getElementById("error-message");
      var errDetail = document.getElementById("error-detail");
      if (errMsg && errMsg.textContent) {
        parts.push("=== Error Message ===");
        parts.push(errMsg.textContent);
        parts.push("");
      }
      if (errDetail && errDetail.textContent) {
        parts.push("=== Error Detail ===");
        parts.push(errDetail.textContent);
        parts.push("");
      }

      var fullText = parts.join("\n");
      copyToClipboard(fullText, btnCopyLog);
    });
  }

  function copyToClipboard(text, button) {
    // Primary: async Clipboard API (requires HTTPS or localhost).
    // Fallback: hidden textarea + execCommand('copy') (works everywhere).
    var originalText = button.textContent;
    function showSuccess() {
      button.textContent = "✓ Copied!";
      button.classList.add("btn-success");
      setTimeout(function () {
        button.textContent = originalText;
        button.classList.remove("btn-success");
      }, 2000);
    }
    function showFailure() {
      button.textContent = "✗ Copy failed";
      setTimeout(function () { button.textContent = originalText; }, 2000);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(showSuccess, function () {
        // Fallback to execCommand
        if (fallbackCopy(text)) showSuccess();
        else showFailure();
      });
    } else {
      if (fallbackCopy(text)) showSuccess();
      else showFailure();
    }
  }

  function fallbackCopy(text) {
    try {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      textarea.style.top = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      var ok = document.execCommand("copy");
      document.body.removeChild(textarea);
      return ok;
    } catch (e) {
      return false;
    }
  }

  // Connect SSE
  var source = new EventSource("/status/stream");
  source.onmessage = function (e) {
    if (!e.data || e.data.charAt(0) === ":") return;  // keepalive
    try {
      var event = JSON.parse(e.data);
      handleEvent(event);
    } catch (err) {
      console.error("Bad SSE payload:", e.data, err);
    }
  };
  source.onerror = function () {
    addLog("[Connection to wizard lost. If the bot is running, you can close this window.]", "err");
  };
})();

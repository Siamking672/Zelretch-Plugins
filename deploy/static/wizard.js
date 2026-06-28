/* Wizard JS — small helpers used on every page. */

(function () {
  "use strict";

  // Helper: show an alert message in a target element.
  window.showAlert = function (target, message, kind) {
    if (!target) return;
    target.className = "alert alert-" + (kind || "info");
    target.innerHTML = message;
    target.classList.remove("hidden");
  };

  window.hideAlert = function (target) {
    if (target) target.classList.add("hidden");
  };

  // On the review page, wire up the Deploy button.
  var deployBtn = document.getElementById("btn-deploy");
  if (deployBtn && window.__ZELRETCH_REVIEW__) {
    deployBtn.addEventListener("click", function () {
      deployBtn.disabled = true;
      deployBtn.textContent = "Starting...";
      fetch("/api/deploy", { method: "POST" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            window.location.href = "/status";
          } else {
            deployBtn.disabled = false;
            deployBtn.textContent = "⚡ Deploy";
            var err = document.getElementById("deploy-error");
            window.showAlert(err, "<strong>Failed to start deployment:</strong> " + (data.error || "Unknown error"), "error");
          }
        })
        .catch(function (err) {
          deployBtn.disabled = false;
          deployBtn.textContent = "⚡ Deploy";
          var errEl = document.getElementById("deploy-error");
          window.showAlert(errEl, "<strong>Network error:</strong> " + err, "error");
        });
    });
  }
})();

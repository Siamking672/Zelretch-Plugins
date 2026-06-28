/* Interactive userbot-session creation flow.
 *
 * Three AJAX calls against the wizard backend:
 *   1. POST /api/session/start   -> { session_id }
 *   2. POST /api/session/verify  -> { session_string } | { needs_password: true }
 *   3. POST /api/session/password-> { session_string }
 *
 * The resulting session string is injected into the SESSION_STRING
 * textarea so the form submit picks it up.
 */

(function () {
  "use strict";

  var form = document.getElementById("userbot-form");
  if (!form) return;

  var btnSend = document.getElementById("btn-send-otp");
  var btnVerify = document.getElementById("btn-verify-otp");
  var btnSubmitPassword = document.getElementById("btn-submit-password");
  var otpInput = document.getElementById("OTP");
  var phoneInput = document.getElementById("PHONE");
  var apiIdInput = document.getElementById("OTP_API_ID");
  var apiHashInput = document.getElementById("OTP_API_HASH");
  var passwordField = document.getElementById("password-field");
  var passwordInput = document.getElementById("PASSWORD");
  var statusEl = document.getElementById("otp-status");
  var sessionTextarea = document.getElementById("SESSION_STRING");

  var currentSessionId = null;

  function setOtpStatus(message, kind) {
    window.showAlert(statusEl, message, kind || "info");
  }

  function post(url, data) {
    var body = new URLSearchParams();
    Object.keys(data).forEach(function (k) {
      if (data[k] !== null && data[k] !== undefined) body.append(k, data[k]);
    });
    return fetch(url, { method: "POST", body: body }).then(function (r) {
      return r.json().then(function (j) { return { ok: r.ok, json: j }; });
    });
  }

  /* ----------------------------------------------------------------
   * Step 1: send OTP
   * ---------------------------------------------------------------- */
  if (btnSend) {
    btnSend.addEventListener("click", function () {
      var phone = (phoneInput.value || "").trim();
      var apiId = (apiIdInput.value || "").trim();
      var apiHash = (apiHashInput.value || "").trim();
      if (!phone || !apiId || !apiHash) {
        setOtpStatus("Phone number, API ID, and API hash are all required to send an OTP.", "error");
        return;
      }
      btnSend.disabled = true;
      btnSend.textContent = "Sending...";
      setOtpStatus("Sending OTP to " + phone + "...", "info");

      post("/api/session/start", { API_ID: apiId, API_HASH: apiHash, PHONE: phone })
        .then(function (resp) {
          btnSend.disabled = false;
          btnSend.textContent = "Resend OTP";
          if (resp.ok && resp.json.ok) {
            currentSessionId = resp.json.session_id;
            otpInput.disabled = false;
            btnVerify.disabled = false;
            setOtpStatus("✓ " + (resp.json.message || "OTP sent. Enter the code below."), "success");
          } else {
            setOtpStatus("✗ " + (resp.json.error || "Failed to send OTP."), "error");
          }
        })
        .catch(function (err) {
          btnSend.disabled = false;
          btnSend.textContent = "Send OTP";
          setOtpStatus("✗ Network error: " + err, "error");
        });
    });
  }

  /* ----------------------------------------------------------------
   * Step 2: verify OTP
   * ---------------------------------------------------------------- */
  if (btnVerify) {
    btnVerify.addEventListener("click", function () {
      var otp = (otpInput.value || "").trim();
      if (!otp) {
        setOtpStatus("Enter the OTP first.", "error");
        return;
      }
      if (!currentSessionId) {
        setOtpStatus("Send the OTP first.", "error");
        return;
      }
      btnVerify.disabled = true;
      btnVerify.textContent = "Verifying...";
      setOtpStatus("Verifying OTP...", "info");

      post("/api/session/verify", { session_id: currentSessionId, OTP: otp })
        .then(function (resp) {
          btnVerify.disabled = false;
          btnVerify.textContent = "Verify OTP";
          if (resp.ok && resp.json.ok) {
            if (resp.json.session_string) {
              sessionTextarea.value = resp.json.session_string;
              setOtpStatus("✓ Session created. The session string has been filled in above. Click <strong>Save &amp; Continue</strong>.", "success");
            } else if (resp.json.needs_password) {
              passwordField.classList.remove("hidden");
              // Focus the password input so the user can type immediately.
              if (passwordInput) passwordInput.focus();
              setOtpStatus("Two-step verification password required. Enter it below and click <strong>Submit Password</strong>.", "info");
            } else {
              setOtpStatus(resp.json.message || "Verified, but no session string returned.", "error");
            }
          } else {
            setOtpStatus("✗ " + (resp.json.error || "OTP verification failed."), "error");
          }
        })
        .catch(function (err) {
          btnVerify.disabled = false;
          btnVerify.textContent = "Verify OTP";
          setOtpStatus("✗ Network error: " + err, "error");
        });
    });
  }

  /* ----------------------------------------------------------------
   * Step 3: submit 2FA password (shared handler)
   *
   * Used by both:
   *   - Pressing Enter inside the password input
   *   - Clicking the explicit "Submit Password" button
   * ---------------------------------------------------------------- */
  function submitPassword() {
    var password = (passwordInput.value || "").trim();
    if (!password) {
      setOtpStatus("Enter your two-step verification password first.", "error");
      if (passwordInput) passwordInput.focus();
      return;
    }
    if (!currentSessionId) {
      setOtpStatus("Session expired. Please send the OTP again.", "error");
      return;
    }

    // Disable the button + input while we submit.
    if (btnSubmitPassword) {
      btnSubmitPassword.disabled = true;
      btnSubmitPassword.textContent = "Verifying...";
    }
    if (passwordInput) passwordInput.disabled = true;
    setOtpStatus("Verifying password...", "info");

    post("/api/session/password", { session_id: currentSessionId, PASSWORD: password })
      .then(function (resp) {
        if (resp.ok && resp.json.ok && resp.json.session_string) {
          sessionTextarea.value = resp.json.session_string;
          setOtpStatus("✓ Session created. The session string has been filled in above. Click <strong>Save &amp; Continue</strong>.", "success");
          passwordField.classList.add("hidden");
        } else {
          // Re-enable the input + button so the user can retry.
          if (passwordInput) passwordInput.disabled = false;
          if (btnSubmitPassword) {
            btnSubmitPassword.disabled = false;
            btnSubmitPassword.textContent = "Submit Password";
          }
          setOtpStatus("✗ " + (resp.json.error || "Password verification failed."), "error");
          if (passwordInput) {
            passwordInput.value = "";
            passwordInput.focus();
          }
        }
      })
      .catch(function (err) {
        if (passwordInput) passwordInput.disabled = false;
        if (btnSubmitPassword) {
          btnSubmitPassword.disabled = false;
          btnSubmitPassword.textContent = "Submit Password";
        }
        setOtpStatus("✗ Network error: " + err, "error");
      });
  }

  // Enter key inside the password input -> submit
  if (passwordInput) {
    passwordInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        submitPassword();
      }
    });
  }

  // Button click -> submit
  if (btnSubmitPassword) {
    btnSubmitPassword.addEventListener("click", submitPassword);
  }
})();

(function () {
  "use strict";

  var root = document.getElementById("coach-chat");
  if (!root) return;

  var messagesEl = document.getElementById("coach-messages");
  var form = document.getElementById("coach-form");
  var input = document.getElementById("coach-input");
  var sendBtn = document.getElementById("coach-send");
  var suggestionsEl = document.getElementById("coach-suggestions");
  var biomarkers = {};

  try {
    biomarkers = JSON.parse(root.dataset.biomarkers || "{}");
  } catch (_err) {
    biomarkers = {};
  }

  var busy = false;

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatMessage(text) {
    return escapeHtml(text).replace(/\n/g, "<br>");
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setBusy(nextBusy) {
    busy = nextBusy;
    sendBtn.disabled = nextBusy;
    input.disabled = nextBusy;
  }

  function appendMessage(role, text) {
    var wrapper = document.createElement("div");
    wrapper.className =
      "coach-message " +
      (role === "user" ? "coach-message-user" : "coach-message-assistant");

    var avatar = document.createElement("div");
    avatar.className = "coach-message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = role === "user" ? "You" : "HP";

    var bubble = document.createElement("div");
    bubble.className = "coach-message-bubble";
    bubble.innerHTML = "<p>" + formatMessage(text) + "</p>";

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
  }

  function appendTypingIndicator() {
    var wrapper = document.createElement("div");
    wrapper.className = "coach-message coach-message-assistant coach-message-typing";
    wrapper.setAttribute("aria-busy", "true");

    var avatar = document.createElement("div");
    avatar.className = "coach-message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "HP";

    var bubble = document.createElement("div");
    bubble.className = "coach-message-bubble";
    bubble.innerHTML =
      '<span class="coach-typing-dots" aria-label="Coach is typing">' +
      '<span></span><span></span><span></span></span>';

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
  }

  function hideSuggestions() {
    if (suggestionsEl) {
      suggestionsEl.classList.add("hidden");
    }
  }

  function extractErrorMessage(payload, status) {
    if (payload && typeof payload.detail === "string") {
      return payload.detail;
    }
    if (payload && Array.isArray(payload.detail)) {
      return payload.detail.map(function (item) {
        return item.msg || String(item);
      }).join(" ");
    }
    if (status === 503) {
      return "The wellness coach is temporarily unavailable. Please try again shortly.";
    }
    return "Something went wrong. Please try again.";
  }

  async function sendMessage(text) {
    var trimmed = text.trim();
    if (!trimmed || busy) return;

    hideSuggestions();
    appendMessage("user", trimmed);
    input.value = "";
    setBusy(true);

    var typingEl = appendTypingIndicator();

    try {
      var response = await fetch("/api/v1/privacy/coach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          biomarkers: biomarkers,
          user_facing: true,
        }),
      });

      var payload = null;
      try {
        payload = await response.json();
      } catch (_jsonErr) {
        payload = null;
      }

      typingEl.remove();

      if (!response.ok) {
        appendMessage("assistant", extractErrorMessage(payload, response.status));
        return;
      }

      var reply = (payload && payload.response) || "I could not generate a response right now.";
      appendMessage("assistant", reply);
    } catch (_networkErr) {
      typingEl.remove();
      appendMessage(
        "assistant",
        "Could not reach the coach service. Check your connection and try again."
      );
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    sendMessage(input.value);
  });

  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(input.value);
    }
  });

  if (suggestionsEl) {
    suggestionsEl.addEventListener("click", function (event) {
      var chip = event.target.closest("[data-prompt]");
      if (!chip) return;
      sendMessage(chip.getAttribute("data-prompt") || "");
    });
  }

  input.focus();
})();

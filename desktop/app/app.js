const invoke = window.__TAURI__?.core?.invoke;

const state = {
  session: null,
  settings: {
    serverUrl: "http://127.0.0.1:8080",
    hasSavedSession: false,
    theme: "dark",
  },
};

const els = {
  statusBanner: document.getElementById("statusBanner"),
  sessionMeta: document.getElementById("sessionMeta"),
  loginPanel: document.getElementById("loginPanel"),
  messagesPanel: document.getElementById("messagesPanel"),
  connectionForm: document.getElementById("connectionForm"),
  loginForm: document.getElementById("loginForm"),
  messageForm: document.getElementById("messageForm"),
  serverUrl: document.getElementById("serverUrl"),
  username: document.getElementById("username"),
  password: document.getElementById("password"),
  messageBody: document.getElementById("messageBody"),
  messageList: document.getElementById("messageList"),
  saveServerButton: document.getElementById("saveServerButton"),
  resumeButton: document.getElementById("resumeButton"),
  loginButton: document.getElementById("loginButton"),
  refreshButton: document.getElementById("refreshButton"),
  logoutButton: document.getElementById("logoutButton"),
  postButton: document.getElementById("postButton"),
  themeToggle: document.getElementById("themeToggle"),
  themeValue: document.getElementById("themeValue"),
};

function setBanner(message, type = "success") {
  if (!message) {
    els.statusBanner.className = "status-banner hidden";
    els.statusBanner.textContent = "";
    return;
  }
  els.statusBanner.className = `status-banner ${type}`;
  els.statusBanner.textContent = message;
}

function setBusy(button, busy) {
  button.disabled = busy;
}

function normalizeTheme(theme) {
  return theme === "light" ? "light" : "dark";
}

function applyTheme(theme) {
  const normalized = normalizeTheme(theme);
  document.documentElement.dataset.theme = normalized;
  els.themeToggle.checked = normalized === "dark";
  els.themeValue.textContent = normalized === "dark" ? "Dark" : "Light";
  state.settings.theme = normalized;
}

function renderSession() {
  const authenticated = Boolean(state.session?.authenticated);
  els.loginPanel.classList.toggle("hidden", authenticated);
  els.messagesPanel.classList.toggle("hidden", !authenticated);

  if (authenticated) {
    const user = state.session.user;
    els.sessionMeta.classList.remove("hidden");
    els.sessionMeta.textContent = `${user.displayName} (@${user.username})`;
  } else {
    els.sessionMeta.classList.add("hidden");
    els.sessionMeta.textContent = "";
  }

  els.serverUrl.value = state.settings.serverUrl || "http://127.0.0.1:8080";
  applyTheme(state.settings.theme);
}

function renderMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0) {
    els.messageList.innerHTML =
      '<div class="empty-state">No messages yet. Post the first one from this desktop app.</div>';
    return;
  }

  const cards = messages
    .map(
      (message) => `
        <article class="message-card">
          <div class="message-meta">
            <strong>${escapeHtml(message.authorDisplayName)}</strong>
            <span>${new Date(message.createdAt).toLocaleString()}</span>
          </div>
          <p>${escapeHtml(message.body)}</p>
        </article>
      `
    )
    .join("");

  els.messageList.innerHTML = cards;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function loadSettings() {
  const response = await invoke("load_settings");
  state.settings = response;
  applyTheme(response.theme);
  renderSession();
}

async function saveServerUrl() {
  const serverUrl = els.serverUrl.value.trim();
  const response = await invoke("save_server_url", { serverUrl });
  state.settings = response;
  applyTheme(response.theme);
  state.session = {
    authenticated: false,
    serverUrl: response.serverUrl,
    user: null,
  };
  renderSession();
  renderMessages([]);
  setBanner("Saved server URL. Sign in again against that server.", "success");
}

async function saveTheme(theme) {
  const response = await invoke("save_theme", { theme });
  state.settings = response;
  applyTheme(response.theme);
  renderSession();
  setBanner(`Saved ${response.theme} theme preference.`, "success");
}

async function resumeSession() {
  const session = await invoke("resume_session");
  state.session = session;
  renderSession();
  if (session.authenticated) {
    await refreshMessages();
    setBanner("Restored saved session.", "success");
  } else {
    setBanner("No active saved session was found.", "error");
  }
}

async function login(event) {
  event.preventDefault();
  setBusy(els.loginButton, true);
  try {
    const session = await invoke("login", {
      serverUrl: els.serverUrl.value.trim(),
      username: els.username.value.trim(),
      password: els.password.value,
    });
    state.session = session;
    state.settings.serverUrl = els.serverUrl.value.trim();
    els.password.value = "";
    renderSession();
    await refreshMessages();
    setBanner("Signed in successfully.", "success");
  } catch (error) {
    setBanner(String(error), "error");
  } finally {
    setBusy(els.loginButton, false);
  }
}

async function refreshMessages() {
  if (!state.session?.authenticated) {
    return;
  }
  setBusy(els.refreshButton, true);
  try {
    const messages = await invoke("list_messages");
    renderMessages(messages);
  } catch (error) {
    setBanner(String(error), "error");
  } finally {
    setBusy(els.refreshButton, false);
  }
}

async function postMessage(event) {
  event.preventDefault();
  setBusy(els.postButton, true);
  try {
    await invoke("post_message", { body: els.messageBody.value.trim() });
    els.messageBody.value = "";
    await refreshMessages();
    setBanner("Posted message.", "success");
  } catch (error) {
    setBanner(String(error), "error");
  } finally {
    setBusy(els.postButton, false);
  }
}

async function logout() {
  setBusy(els.logoutButton, true);
  try {
    await invoke("logout");
    state.session = { authenticated: false, serverUrl: state.settings.serverUrl, user: null };
    renderSession();
    renderMessages([]);
    setBanner("Signed out and cleared the saved session.", "success");
  } catch (error) {
    setBanner(String(error), "error");
  } finally {
    setBusy(els.logoutButton, false);
  }
}

async function bootstrap() {
  applyTheme(state.settings.theme);

  if (!invoke) {
    setBanner(
      "The Tauri API is unavailable. Start this UI through `cargo tauri dev` or a packaged build.",
      "error"
    );
    return;
  }

  try {
    await loadSettings();
    const session = await invoke("resume_session");
    state.session = session;
    renderSession();
    if (session.authenticated) {
      await refreshMessages();
    } else {
      renderMessages([]);
    }
  } catch (error) {
    setBanner(String(error), "error");
  }
}

els.saveServerButton.addEventListener("click", async () => {
  try {
    await saveServerUrl();
  } catch (error) {
    setBanner(String(error), "error");
  }
});

els.resumeButton.addEventListener("click", async () => {
  try {
    await resumeSession();
  } catch (error) {
    setBanner(String(error), "error");
  }
});

els.themeToggle.addEventListener("change", async () => {
  const previousTheme = state.settings.theme || "dark";
  const nextTheme = els.themeToggle.checked ? "dark" : "light";
  applyTheme(nextTheme);
  try {
    await saveTheme(nextTheme);
  } catch (error) {
    applyTheme(previousTheme);
    setBanner(String(error), "error");
  }
});

els.loginForm.addEventListener("submit", login);
els.messageForm.addEventListener("submit", postMessage);
els.refreshButton.addEventListener("click", refreshMessages);
els.logoutButton.addEventListener("click", logout);

bootstrap();

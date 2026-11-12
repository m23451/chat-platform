/*
 * Live Chat frontend.
 *
 * Endpoints (same origin, routed by the gateway / NGINX):
 *   GET  /api/messages?limit=50&before=<id>   history, newest first
 *   POST /api/messages  {author, text}         send a message
 *   WS   /api/message-ws                       server pushes each new message as JSON
 *
 * Order on load: open the WebSocket FIRST, then load history, and de-duplicate
 * by id - so no message sent in between is lost or shown twice.
 */
(() => {
  "use strict";

  const API = "/api/messages";
  const WS_PATH = "/api/message-ws";
  const PAGE_SIZE = 50;
  const MAX_LEN = 500;
  const PING_MS = 25000;          // keep idle connections alive through the gateway
  const MAX_BACKOFF_MS = 15000;

  const $ = (id) => document.getElementById(id);
  const el = {
    scroller: $("scroller"), list: $("messages"), empty: $("empty"), older: $("older"),
    status: $("status"), statusText: $("status-text"), error: $("error"),
    form: $("composer"), name: $("name"), text: $("text"), send: $("send"), counter: $("counter"),
  };

  const seen = new Set();          // message ids already on screen
  let oldestId = null;
  let socket = null;
  let pingTimer = null;
  let retries = 0;
  let sending = false;

  // ---------- Small helpers ----------
  const store = {
    get(key) { try { return localStorage.getItem(key); } catch { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* storage unavailable */ } },
  };

  function setStatus(state, text) {
    el.status.dataset.state = state;
    el.statusText.textContent = text;
  }

  function showError(text) {
    el.error.textContent = text;
    el.error.hidden = !text;
  }

  function nearBottom() {
    const s = el.scroller;
    return s.scrollHeight - s.scrollTop - s.clientHeight < 80;
  }

  function scrollToBottom() {
    el.scroller.scrollTop = el.scroller.scrollHeight;
  }

  function formatTime(iso) {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    const sameDay = d.toDateString() === new Date().toDateString();
    return sameDay
      ? d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : d.toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  }

  // ---------- Rendering ----------
  // Built with textContent only, never innerHTML, so user text can't inject HTML or scripts.
  function renderMessage(m) {
    const li = document.createElement("li");
    li.className = "msg";
    li.dataset.id = m.id;
    if (m.author && m.author === el.name.value.trim()) li.classList.add("mine");

    const head = document.createElement("div");
    head.className = "head";
    const author = document.createElement("span");
    author.className = "author";
    author.textContent = m.author || "anonymous";
    const time = document.createElement("time");
    time.dateTime = m.createdAt || "";
    time.textContent = formatTime(m.createdAt);
    head.append(author, time);

    const body = document.createElement("div");
    body.className = "body";
    body.textContent = m.text;

    li.append(head, body);
    return li;
  }

  function isValid(m) {
    return m && m.id != null && typeof m.text === "string";
  }

  function trackOldest(id) {
    if (oldestId === null || id < oldestId) oldestId = id;
  }

  // A live message: append at the bottom.
  function addNewest(m) {
    if (!isValid(m) || seen.has(m.id)) return;
    const stick = nearBottom();
    seen.add(m.id);
    trackOldest(m.id);
    el.list.append(renderMessage(m));
    el.empty.hidden = true;
    if (stick) scrollToBottom();
  }

  // A page of history (API returns newest first): insert above what's shown, keeping position.
  function addOlder(messages) {
    const fresh = messages.filter((m) => isValid(m) && !seen.has(m.id)).reverse();
    if (!fresh.length) return;
    const before = el.scroller.scrollHeight;
    const frag = document.createDocumentFragment();
    for (const m of fresh) {
      seen.add(m.id);
      trackOldest(m.id);
      frag.append(renderMessage(m));
    }
    el.list.prepend(frag);
    el.scroller.scrollTop += el.scroller.scrollHeight - before;
  }

  // ---------- History ----------
  async function loadHistory(before) {
    const url = new URL(API, location.origin);
    url.searchParams.set("limit", PAGE_SIZE);
    if (before != null) url.searchParams.set("before", before);

    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`History failed (${res.status})`);
    const page = await res.json();
    if (!Array.isArray(page)) throw new Error("Unexpected history format");

    const first = seen.size === 0;
    addOlder(page);
    el.older.hidden = page.length < PAGE_SIZE;
    if (first) {
      el.empty.textContent = "No messages yet. Say hello!";
      el.empty.hidden = seen.size > 0;
      scrollToBottom();
    }
  }

  el.older.addEventListener("click", async () => {
    el.older.disabled = true;
    try {
      await loadHistory(oldestId);
    } catch (err) {
      showError("Couldn't load older messages. Try again.");
    } finally {
      el.older.disabled = false;
    }
  });

  // ---------- WebSocket ----------
  function connect() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    setStatus("connecting", retries ? "Reconnecting…" : "Connecting…");
    socket = new WebSocket(`${proto}//${location.host}${WS_PATH}`);

    socket.addEventListener("open", async () => {
      retries = 0;
      setStatus("online", "Live");
      clearInterval(pingTimer);
      pingTimer = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send("ping");
      }, PING_MS);

      // Load (or after a reconnect, top up) history now the socket is open.
      try {
        await loadHistory();
        showError("");
      } catch (err) {
        showError("Couldn't load message history.");
        el.empty.textContent = "Couldn't load messages.";
      }
    });

    socket.addEventListener("message", (event) => {
      let data;
      try { data = JSON.parse(event.data); } catch { return; }   // ignore "pong" etc.
      addNewest(data);
    });

    socket.addEventListener("close", () => {
      clearInterval(pingTimer);
      setStatus("offline", "Offline, retrying…");
      // Exponential backoff with jitter, so pods aren't stampeded after a restart.
      const delay = Math.min(MAX_BACKOFF_MS, 1000 * 2 ** retries) * (0.5 + Math.random() / 2);
      retries += 1;
      setTimeout(connect, delay);
    });
  }

  // ---------- Sending ----------
  function updateComposer() {
    const len = el.text.value.length;
    el.counter.textContent = `${len}/${MAX_LEN}`;
    el.counter.classList.toggle("over", len > MAX_LEN);
    el.send.disabled = sending || !el.name.value.trim() || !el.text.value.trim() || len > MAX_LEN;

    // Auto-grow the textarea up to its CSS max-height.
    el.text.style.height = "auto";
    el.text.style.height = `${el.text.scrollHeight}px`;
  }

  async function send(event) {
    event.preventDefault();
    const author = el.name.value.trim();
    const text = el.text.value.trim();
    if (!author || !text || text.length > MAX_LEN || sending) return;

    sending = true;
    updateComposer();
    try {
      const res = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ author, text }),
      });

      if (res.status === 429) throw new Error("You're sending messages too fast. Wait a moment.");
      if (res.status === 400) throw new Error("That message isn't valid (empty or too long).");
      if (res.status === 503) throw new Error("Chat is temporarily unavailable. Try again shortly.");
      if (!res.ok) throw new Error(`Couldn't send (error ${res.status}).`);

      // Show it straight away; the WebSocket copy is skipped because the id is already seen.
      addNewest(await res.json());
      scrollToBottom();
      el.text.value = "";
      showError("");
    } catch (err) {
      showError(err instanceof TypeError ? "Network error. Check your connection." : err.message);
    } finally {
      sending = false;
      updateComposer();
      el.text.focus();
    }
  }

  // Enter sends, Shift+Enter adds a new line.
  el.text.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      el.form.requestSubmit();
    }
  });

  el.text.addEventListener("input", updateComposer);
  el.name.addEventListener("input", () => {
    store.set("chat.name", el.name.value.trim());
    updateComposer();
  });
  el.form.addEventListener("submit", send);

  // ---------- Start ----------
  el.name.value = store.get("chat.name") || "";
  updateComposer();
  connect();
})();

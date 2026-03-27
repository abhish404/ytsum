// ── Background Service Worker ───────────────────────
// Handles summarization in the background so closing the popup doesn't kill it.
// Uses chrome.alarms keepalive + chrome.storage.local for persistence across
// service worker restarts.

const DEFAULT_BACKEND = "http://localhost:8000";
const KEEPALIVE_ALARM = "keepalive";

// In-memory state
let state = {
  status: "idle",       // idle | running | done | error
  videoUrl: null,
  videoTitle: null,
  videoId: null,
  progress: [],         // array of progress message strings
  summary: null,        // final summary markdown
  stats: null,
  metadata: null,
  error: null,
};

// ── State persistence ───────────────────────────────
async function saveState() {
  await chrome.storage.local.set({ summarizerState: state });
}

async function loadState() {
  const data = await chrome.storage.local.get(["summarizerState"]);
  if (data.summarizerState) {
    state = data.summarizerState;
    // If we were "running" but worker restarted, mark as error
    // (the fetch was lost when the worker died)
    if (state.status === "running") {
      state.status = "error";
      state.error = "Service worker restarted — please try again";
      state.progress.push("⚠️ Worker restarted — summarization interrupted");
      await saveState();
    }
  }
}

// Restore state on worker startup
loadState();


// ── Keepalive mechanism ─────────────────────────────
// Chrome MV3 service workers die after ~30s of inactivity.
// We create a periodic alarm to keep the worker alive during summarization.

function startKeepalive() {
  chrome.alarms.create(KEEPALIVE_ALARM, { periodInMinutes: 0.4 }); // every ~25s
}

function stopKeepalive() {
  chrome.alarms.clear(KEEPALIVE_ALARM);
}

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === KEEPALIVE_ALARM) {
    if (state.status !== "running") {
      stopKeepalive();
    }
    // Just responding to the alarm keeps the worker alive
  }
});


// ── Backend URL ─────────────────────────────────────
async function getBackendUrl() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["backendUrl"], (data) => {
      resolve(data.backendUrl || DEFAULT_BACKEND);
    });
  });
}


// ── Notify popup ────────────────────────────────────
function notifyPopup() {
  chrome.runtime.sendMessage({ type: "state_update", state }).catch(() => {
    // Popup not open — that's fine
  });
}


// ── Cookie extraction ───────────────────────────────
function getYouTubeCookies() {
  return new Promise((resolve) => {
    chrome.cookies.getAll({ domain: ".youtube.com" }, (cookies) => {
      resolve(
        (cookies || []).map((c) => ({
          name: c.name,
          value: c.value,
          domain: c.domain,
          path: c.path,
          secure: c.secure,
          expirationDate: c.expirationDate || 0,
        }))
      );
    });
  });
}


// ── Main summarization ──────────────────────────────
async function runSummarization(url, title, videoId) {
  state = {
    status: "running",
    videoUrl: url,
    videoTitle: title,
    videoId: videoId,
    progress: ["🔐 Extracting YouTube cookies..."],
    summary: null,
    stats: null,
    metadata: null,
    error: null,
  };
  await saveState();
  notifyPopup();
  startKeepalive();

  try {
    const cookies = await getYouTubeCookies();
    state.progress.push(`🍪 Got ${cookies.length} cookies`);
    await saveState();
    notifyPopup();

    const backendUrl = await getBackendUrl();
    state.progress.push("📡 Connecting to backend...");
    await saveState();
    notifyPopup();

    const response = await fetch(`${backendUrl}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, cookies }),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    // Parse SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            handleSSEData(data);
            await saveState();
          } catch {}
        }
      }
    }

    // Process remaining buffer
    if (buffer.trim()) {
      for (const line of buffer.split("\n")) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            handleSSEData(data);
          } catch {}
        }
      }
    }

    // If we finished streaming without a final result
    if (state.status === "running") {
      state.status = "done";
      state.progress.push("✅ Complete");
    }
    await saveState();
    notifyPopup();

  } catch (err) {
    state.status = "error";
    state.error = err.message || "Something went wrong";
    state.progress.push(`❌ ${state.error}`);
    await saveState();
    notifyPopup();
  } finally {
    stopKeepalive();
  }
}


function handleSSEData(data) {
  if (data.error) {
    state.status = "error";
    state.error = data.error;
    state.progress.push(`❌ ${data.error}`);
    notifyPopup();
    return;
  }

  if (data.summary) {
    state.status = "done";
    state.summary = data.summary;
    state.stats = data.stats || null;
    state.progress.push("✅ Done!");
    notifyPopup();
    return;
  }

  if (data.message) {
    state.progress.push(data.message);
    if (data.metadata) {
      state.metadata = data.metadata;
    }
    notifyPopup();
  }
}


// ── Message listener ────────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "start_summarize") {
    runSummarization(msg.url, msg.title, msg.videoId);
    sendResponse({ ok: true });
    return;
  }

  if (msg.type === "get_state") {
    sendResponse({ state });
    return;
  }

  if (msg.type === "reset") {
    state = {
      status: "idle",
      videoUrl: null,
      videoTitle: null,
      videoId: null,
      progress: [],
      summary: null,
      stats: null,
      metadata: null,
      error: null,
    };
    saveState();
    sendResponse({ ok: true });
    return;
  }
});

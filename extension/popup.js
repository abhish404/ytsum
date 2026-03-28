// ── Config ──────────────────────────────────────────
const DEFAULT_BACKEND = "http://localhost:8000";

// ── DOM refs ────────────────────────────────────────
const $ = (id) => document.getElementById(id);

const elements = {
  serverStatus:    $("serverStatus"),
  placeholder:     $("placeholder"),
  videoInfo:       $("videoInfo"),
  videoThumb:      $("videoThumb"),
  videoTitle:      $("videoTitle"),
  videoChannel:    $("videoChannel"),
  summarizeBtn:    $("summarizeBtn"),
  stopBtn:         $("stopBtn"),
  newVideoBanner:  $("newVideoBanner"),
  loadNewVideoBtn: $("loadNewVideoBtn"),
  btnText:         document.querySelector(".btn-text"),
  btnLoader:       document.querySelector(".btn-loader"),
  progressSection: $("progressSection"),
  progressFill:    $("progressFill"),
  progressLog:     $("progressLog"),
  resultSection:   $("resultSection"),
  resultContent:   $("resultContent"),
  resultStats:     $("resultStats"),
  copyBtn:         $("copyBtn"),
};

let currentVideoUrl = null;
let currentVideoId = null;
let rawSummaryMd = "";
let tabVideoId = null; // Video ID from the active tab (may differ from summarized video)

// ── Init ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  checkBackendHealth();
  detectYouTubeVideo();

  elements.summarizeBtn.addEventListener("click", onSummarize);
  elements.copyBtn.addEventListener("click", onCopy);
  elements.stopBtn.addEventListener("click", onStop);
  elements.loadNewVideoBtn.addEventListener("click", onLoadNewVideo);
  $("backendUrl").addEventListener("change", saveSettings);

  // Restore state from background worker (in case popup was closed and reopened)
  chrome.runtime.sendMessage({ type: "get_state" }, (response) => {
    if (response?.state) {
      restoreFromState(response.state);
      // checkForVideoChange is now called inside restoreFromState
    }
  });

  // Listen for live updates from background worker
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "state_update") {
      restoreFromState(msg.state);
    }
  });
});


// ── Restore UI from background state ────────────────
function restoreFromState(bgState) {
  if (bgState.status === "idle") return;

  // Show video info if we have it
  if (bgState.videoId) {
    elements.placeholder.style.display = "none";
    elements.videoInfo.style.display = "flex";
    elements.videoThumb.src = `https://img.youtube.com/vi/${bgState.videoId}/mqdefault.jpg`;
    elements.videoTitle.textContent = bgState.videoTitle || "YouTube Video";
    elements.videoChannel.textContent = bgState.status === "running" ? "Summarizing..." : "Ready";
    currentVideoUrl = bgState.videoUrl;
    currentVideoId = bgState.videoId;
  }

  // Show progress
  if (bgState.progress.length > 0) {
    elements.progressSection.style.display = "block";
    elements.progressLog.innerHTML = "";
    for (const msg of bgState.progress) {
      addProgressEntry(msg);
    }
  }

  // Handle status
  if (bgState.status === "running") {
    setLoading(true);
    elements.progressFill.classList.add("indeterminate");
    elements.summarizeBtn.disabled = true;
    elements.stopBtn.style.display = "flex";
    elements.resultSection.style.display = "none";
  } else if (bgState.status === "done" && bgState.summary) {
    setLoading(false);
    elements.progressFill.classList.remove("indeterminate");
    elements.progressFill.style.width = "100%";
    rawSummaryMd = bgState.summary;
    renderResult(bgState.summary, bgState.stats);
    elements.summarizeBtn.disabled = false;
    elements.stopBtn.style.display = "none";
  } else if (bgState.status === "error") {
    setLoading(false);
    elements.progressFill.classList.remove("indeterminate");
    showError(bgState.error || "Something went wrong");
    elements.summarizeBtn.disabled = false;
    elements.stopBtn.style.display = "none";
  }

  // After restoring, always check if the active tab has a different video
  checkForVideoChange(bgState);
}


// ── Settings persistence ────────────────────────────
function loadSettings() {
  chrome.storage?.local?.get(["backendUrl"], (data) => {
    if (data.backendUrl) {
      $("backendUrl").value = data.backendUrl;
    }
  });
}

function saveSettings() {
  const url = $("backendUrl")?.value?.trim() || DEFAULT_BACKEND;
  chrome.storage?.local?.set({ backendUrl: url });
  checkBackendHealth();
}


// ── Health check ────────────────────────────────────
async function checkBackendHealth() {
  const backendUrl = $("backendUrl")?.value?.trim() || DEFAULT_BACKEND;
  try {
    const res = await fetch(`${backendUrl}/health`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      elements.serverStatus.classList.add("online");
      elements.serverStatus.title = "Backend online";
    } else {
      throw new Error();
    }
  } catch {
    elements.serverStatus.classList.remove("online");
    elements.serverStatus.title = "Backend offline";
  }
}


// ── Detect YouTube video from active tab ────────────
function detectYouTubeVideo() {
  chrome.tabs?.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs?.[0];
    if (!tab?.url) return;

    const url = new URL(tab.url);
    const isYouTube = url.hostname.includes("youtube.com") && url.pathname === "/watch";
    const videoId = url.searchParams.get("v");

    if (isYouTube && videoId) {
      currentVideoUrl = tab.url;
      currentVideoId = videoId;

      elements.placeholder.style.display = "none";
      elements.videoInfo.style.display = "flex";
      elements.videoThumb.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
      elements.videoTitle.textContent = tab.title?.replace(" - YouTube", "") || "YouTube Video";
      elements.videoChannel.textContent = "Ready to summarize";
      elements.summarizeBtn.disabled = false;
    }
  });
}


// ── Summarize action — delegates to background worker ──
async function onSummarize() {
  if (!currentVideoUrl) return;

  // Hide the new-video banner if visible
  elements.newVideoBanner.style.display = "none";

  // Reset UI
  setLoading(true);
  elements.progressSection.style.display = "block";
  elements.resultSection.style.display = "none";
  elements.progressLog.innerHTML = "";
  elements.progressFill.style.width = "0%";
  elements.progressFill.classList.add("indeterminate");
  elements.stopBtn.style.display = "flex";
  clearError();

  // Reset background state, then start
  chrome.runtime.sendMessage({ type: "reset" }, () => {
    const title = elements.videoTitle.textContent || "YouTube Video";
    chrome.runtime.sendMessage({
      type: "start_summarize",
      url: currentVideoUrl,
      title: title,
      videoId: currentVideoId,
    });
  });
}


// ── Stop / Cancel summarization ─────────────────────
function onStop() {
  chrome.runtime.sendMessage({ type: "cancel" }, () => {
    // Reset the full UI back to idle
    setLoading(false);
    elements.stopBtn.style.display = "none";
    elements.progressSection.style.display = "none";
    elements.progressFill.classList.remove("indeterminate");
    elements.progressFill.style.width = "0%";
    elements.resultSection.style.display = "none";
    elements.newVideoBanner.style.display = "none";
    clearError();

    // Re-detect whatever video is on the current tab
    detectYouTubeVideo();
  });
}


// ── Check if current tab has a different video ──────
function checkForVideoChange(bgState) {
  if (bgState.status === "idle") return;

  chrome.tabs?.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs?.[0];
    if (!tab?.url) return;

    try {
      const url = new URL(tab.url);
      const isYouTube = url.hostname.includes("youtube.com") && url.pathname === "/watch";
      const videoId = url.searchParams.get("v");

      if (isYouTube && videoId && bgState.videoId && videoId !== bgState.videoId) {
        tabVideoId = videoId;
        // Show the "new video detected" banner
        elements.newVideoBanner.style.display = "flex";
        // Update banner text with the new tab's title
        const bannerTitle = tab.title?.replace(" - YouTube", "") || "New video";
        const bannerSpan = elements.newVideoBanner.querySelector(".banner-content span");
        if (bannerSpan) bannerSpan.textContent = `New video: ${bannerTitle}`;
      } else {
        // Same video or not on YouTube — hide banner
        elements.newVideoBanner.style.display = "none";
      }
    } catch {}
  });
}


// ── Load the new video (cancel old + reset) ─────────
function onLoadNewVideo() {
  chrome.runtime.sendMessage({ type: "cancel" }, () => {
    // Reset UI fully
    setLoading(false);
    elements.stopBtn.style.display = "none";
    elements.progressSection.style.display = "none";
    elements.progressFill.classList.remove("indeterminate");
    elements.progressFill.style.width = "0%";
    elements.resultSection.style.display = "none";
    elements.newVideoBanner.style.display = "none";
    clearError();

    // Detect the new video from the active tab
    detectYouTubeVideo();
  });
}


// ── Markdown → HTML rendering ───────────────────────
function renderMarkdown(md) {
  let html = md
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    .replace(/((?:^\d+\..+\n?)+)/gm, (match) => {
      const items = match.trim().split("\n").map((l) => {
        const text = l.replace(/^\d+\.\s*/, "");
        return `<li>${text}</li>`;
      });
      return `<ol>${items.join("")}</ol>`;
    })
    .replace(/^(?!<[hob\d/lu])((?!<).+)$/gm, "<p>$1</p>")
    .replace(/<\/blockquote>\s*<blockquote>/g, "<br>");

  return html;
}


function renderResult(summaryMd, stats) {
  elements.resultSection.style.display = "block";
  elements.resultContent.innerHTML = renderMarkdown(summaryMd);

  if (stats) {
    elements.resultStats.innerHTML = `
      <span>📝 ${stats.transcript_words?.toLocaleString() || "?"} words</span>
      <span>🧹 ${stats.fillers_removed || 0} fillers</span>
      <span>📄 ${stats.summary_words?.toLocaleString() || "?"} summary words</span>
    `;
  }
}


// ── UI helpers ──────────────────────────────────────
function setLoading(loading) {
  elements.summarizeBtn.disabled = loading;
  elements.btnText.style.display = loading ? "none" : "inline";
  elements.btnLoader.style.display = loading ? "inline-block" : "none";
}

function addProgressEntry(message) {
  elements.progressLog.querySelectorAll(".latest").forEach((el) => el.classList.remove("latest"));

  const entry = document.createElement("div");
  entry.className = "progress-entry latest";
  entry.textContent = message;
  elements.progressLog.appendChild(entry);
  elements.progressLog.scrollTop = elements.progressLog.scrollHeight;
}

function showError(message) {
  clearError();
  const el = document.createElement("div");
  el.className = "error-msg";
  el.id = "errorMsg";
  el.textContent = `❌ ${message}`;
  elements.progressSection.after(el);
}

function clearError() {
  document.getElementById("errorMsg")?.remove();
}

async function onCopy() {
  if (!rawSummaryMd) return;
  try {
    await navigator.clipboard.writeText(rawSummaryMd);
    elements.copyBtn.classList.add("copied");
    elements.copyBtn.querySelector("span").textContent = "Copied!";
    setTimeout(() => {
      elements.copyBtn.classList.remove("copied");
      elements.copyBtn.querySelector("span").textContent = "Copy";
    }, 2000);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = rawSummaryMd;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
}

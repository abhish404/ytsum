// ── Content Script: YouTube Video Seeker ────────────
// Listens for SEEK_VIDEO messages from the popup and seeks the
// YouTube player to the requested timestamp.

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "SEEK_VIDEO") {
    const video = document.querySelector("video");
    if (video) {
      video.currentTime = msg.seconds;
      video.play();
      sendResponse({ ok: true });
    } else {
      sendResponse({ ok: false, error: "No video element found" });
    }
  }
});

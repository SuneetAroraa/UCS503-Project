const API_URL = "http://127.0.0.1:8000/simplify/batch";
const BATCH_SIZE = 5;
const MAX_IN_FLIGHT = 2;
const MIN_WORDS = 8;
const MAX_PROCESSED = 80;
const CACHE_PREFIX = "readable-cache-v2:";
const $ = (id) => document.getElementById(id);
const toggleButton = $("toggleButton");
const modeSelect = $("mode");
const statusElement = $("status");
const resultsElement = $("results");
let busy = false;
let currentTabId = null;
let pageState = null;
let stats = { eligible: 0, processed: 0, changed: 0, unchanged: 0, skipped: 0, kept: 0, fallback: 0 };

function setStatus(message) { statusElement.textContent = message; }
function setBusy(value) { busy = value; toggleButton.disabled = value; modeSelect.disabled = value; }
function showStats() {
  $("blocksResult").textContent = `${stats.processed} of ${stats.eligible} eligible paragraphs processed`;
  $("changedResult").textContent = String(stats.changed);
  $("unchangedResult").textContent = String(stats.unchanged);
  $("skippedResult").textContent = String(stats.skipped);
  $("keptResult").textContent = String(stats.kept);
  $("fallbackResult").textContent = String(stats.fallback);
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length || tabs[0].id == null) throw new Error("No active browser tab found.");
  return tabs[0];
}

async function callPage(command, args = []) {
  await chrome.scripting.executeScript({ target: { tabId: currentTabId }, files: ["content.js"] });
  const result = await chrome.scripting.executeScript({
    target: { tabId: currentTabId },
    func: (name, values) => {
      const api = globalThis.__readablePageControllerV2;
      if (!api || typeof api[name] !== "function") throw new Error("Readable page controller is unavailable.");
      return api[name](...values);
    },
    args: [command, args]
  });
  return result[0]?.result;
}

async function refreshState() {
  const tab = await getActiveTab();
  currentTabId = tab.id;
  pageState = await callPage("state");
  if (pageState.mode) modeSelect.value = pageState.mode;
  toggleButton.textContent = pageState.enabled ? "Turn off simplification" : "Turn on simplification";
  $("highlight").checked = pageState.highlight;
  resultsElement.classList.toggle("hidden", !pageState.states.length);
  if (pageState.states.length) {
    const count = pageState.states.filter((s) => s.changed).length;
    stats = pageState.summary || { eligible: pageState.states.length, processed: pageState.states.length, changed: count, unchanged: pageState.states.length - count, skipped: 0, kept: 0, fallback: 0 };
    showStats();
  }
  setStatus(pageState.enabled ? "Simplification is on for this page." : "Ready to simplify this page.");
}

async function createCacheKey(mode, text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${mode}\n${text}`));
  return `${CACHE_PREFIX}${mode}:${[...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("")}`;
}
async function readCache(key) {
  try { const value = (await chrome.storage.session.get(key))[key]; return value && Date.now() - value.savedAt < 6 * 60 * 60 * 1000 ? value.result : null; } catch { return null; }
}
async function writeCache(key, result) {
  try { await chrome.storage.session.set({ [key]: { savedAt: Date.now(), result } }); } catch { /* Cache is optional. */ }
}
function pause(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function postBatch(texts, mode) {
  let lastError;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await fetch(API_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ texts, mode }) });
      if (response.ok) {
        const data = await response.json();
        if (!Array.isArray(data.results) || data.results.length !== texts.length) throw new Error("The API returned an incomplete batch.");
        return data.results;
      }
      const retryable = response.status === 429 || response.status >= 500;
      const retryAfter = Number(response.headers.get("Retry-After"));
      const errorBody = response.status === 429 ? (await response.text()).toLowerCase() : "";
      const quotaExhausted = /daily quota|quota exhausted|resource exhausted|per day|limit exceeded/.test(errorBody);
      lastError = new Error(quotaExhausted ? "The API quota is exhausted; originals were kept." : `API request failed (${response.status}).`);
      if (quotaExhausted) break;
      if (!retryable || attempt === 2) break;
      await pause(Number.isFinite(retryAfter) && retryAfter > 0 ? Math.min(retryAfter * 1000, 10000) : 600 * 2 ** attempt);
    } catch (error) {
      lastError = error;
      if (attempt === 2) break;
      await pause(600 * 2 ** attempt);
    }
  }
  throw lastError || new Error("Batch request failed.");
}

async function getBatchResults(batch, mode) {
  const resolved = new Array(batch.length);
  const missing = [];
  for (let i = 0; i < batch.length; i++) {
    const key = await createCacheKey(mode, batch[i].text);
    const cached = await readCache(key);
    if (cached) resolved[i] = { result: cached, key, cached: true };
    else missing.push({ index: i, block: batch[i], key });
  }
  if (missing.length) {
    let apiResults;
    try { apiResults = await postBatch(missing.map((item) => item.block.text), mode); }
    catch (error) {
      if (mode === "rules") throw error;
      // The API batch endpoint itself falls back to rules for Gemini errors. This second request
      // only helps if the selected-mode request failed before the backend could return a result.
      try {
        apiResults = await postBatch(missing.map((item) => item.block.text), "rules");
        apiResults.forEach((result) => { result.fallback_used = true; result.fallback_reason = "Selected-mode batch failed; rules were requested."; });
      } catch { throw error; }
    }
    missing.forEach((item, index) => {
      resolved[item.index] = { result: apiResults[index], key: item.key, cached: false };
    });
  }
  await Promise.all(resolved.map(async (item) => {
    if (!item.cached && item.result && (mode === "rules" || !item.result.fallback_used)) await writeCache(item.key, item.result);
  }));
  return resolved;
}

async function enable() {
  const scan = await callPage("scan", [MIN_WORDS]);
  if (!scan?.blocks?.length) {
    stats = { eligible: 0, processed: 0, changed: 0, unchanged: 0, skipped: scan?.skipped || 0, kept: 0, fallback: 0 };
    showStats();
    resultsElement.classList.remove("hidden");
    throw new Error(scan?.error || "No suitable article paragraphs with at least 8 words were found.");
  }
  const blocks = scan.blocks.slice(0, MAX_PROCESSED);
  stats = { eligible: blocks.length, processed: 0, changed: 0, unchanged: 0, skipped: scan.skipped + Math.max(0, scan.blocks.length - blocks.length), kept: 0, fallback: 0 };
  const mode = modeSelect.value;
  const batches = [];
  for (let i = 0; i < blocks.length; i += BATCH_SIZE) batches.push(blocks.slice(i, i + BATCH_SIZE));
  let next = 0;
  const workers = Array.from({ length: Math.min(MAX_IN_FLIGHT, batches.length) }, async () => {
    while (next < batches.length) {
      const batch = batches[next++];
      try {
        const outcomes = await getBatchResults(batch, mode);
        for (let i = 0; i < outcomes.length; i++) {
          const { result } = outcomes[i];
          const text = result?.simplified_text;
          let status = "kept";
          if (typeof text === "string" && text.trim()) {
            const applied = await callPage("apply", [batch[i].id, text]);
            status = applied?.status || "kept";
          }
          if (status === "changed") stats.changed++;
          else if (status === "unchanged") stats.unchanged++;
          else stats.kept++;
          if (result?.fallback_used && status !== "kept") stats.fallback++;
          stats.processed++;
          showStats();
          setStatus(`Processing article: ${stats.processed} of ${stats.eligible} paragraphs; ${stats.changed} changed.`);
        }
      } catch (error) {
        stats.kept += batch.length;
        stats.processed += batch.length;
        showStats();
        console.warn("Readable batch failed; originals kept:", error);
      }
      await callPage("setSummary", [stats, mode]);
    }
  });
  resultsElement.classList.remove("hidden");
  await Promise.all(workers);
  pageState = await callPage("state");
  toggleButton.textContent = "Turn off simplification";
  setStatus(`Done: ${stats.changed} changed, ${stats.unchanged} unchanged, ${stats.skipped} skipped, ${stats.kept} kept original.`);
}

async function disable() {
  const restored = await callPage("restore");
  pageState = await callPage("state");
  toggleButton.textContent = "Turn on simplification";
  resultsElement.classList.add("hidden");
  setStatus(`Original wording, markup, and styles restored in ${restored.count} paragraph(s).`);
}

toggleButton.addEventListener("click", async () => {
  if (busy) return;
  setBusy(true);
  try {
    if (currentTabId == null) await refreshState();
    if (pageState?.enabled) await disable(); else await enable();
  } catch (error) {
    setStatus(error?.message || "This page cannot be modified. Open a normal webpage and try again.");
  } finally { setBusy(false); }
});
$("highlight").addEventListener("change", async (event) => {
  try { await callPage("setHighlight", [event.target.checked]); } catch { /* Unsupported page. */ }
});
modeSelect.addEventListener("change", () => { if (pageState?.enabled) setStatus("Mode changes apply the next time you turn simplification on."); });
refreshState().catch(() => {
  toggleButton.disabled = true;
  setStatus("This page cannot be modified. Open a normal webpage and try again.");
});

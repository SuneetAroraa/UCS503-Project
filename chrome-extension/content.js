(() => {
  const KEY = "__readablePageControllerV2";
  if (globalThis[KEY]) return;

  const records = new WeakMap();
  const states = new Map();
  const BLOCKS = "p, li, blockquote, h1, h2, h3, h4, h5, h6";
  const EXCLUDED = "nav, header, footer, aside, form, table, pre, [role='navigation'], [role='banner'], [role='contentinfo'], [role='complementary'], [contenteditable]:not([contenteditable='false']), [aria-label*='recommend' i], [class*='recommend' i], [id*='recommend' i], [class*='related' i], [id*='related' i], [class*='advert' i], [id*='advert' i], [class*='promo' i], [id*='promo' i]";
  const MAX_BLOCKS = 80;
  let highlightEnabled = true;
  let summary = null;
  let currentMode = "hybrid";

  function visible(el) {
    return el.isConnected && el.getClientRects().length > 0 &&
      getComputedStyle(el).visibility !== "hidden" && getComputedStyle(el).display !== "none";
  }

  function eligible(root) {
    return [...root.querySelectorAll(BLOCKS)].filter((el) => {
      if (el.closest(EXCLUDED) || !visible(el) || el.querySelector(BLOCKS)) return false;
      if (el.querySelector("button, input, select, textarea, img, video, audio, iframe, object, embed, canvas, svg, script, style, [contenteditable]:not([contenteditable='false'])")) return false;
      return el.textContent.trim().length > 0 && !records.has(el);
    });
  }

  function score(root) {
    const nodes = eligible(root);
    const text = nodes.map((el) => el.textContent.trim()).join(" ");
    if (!nodes.length || text.length < 180) return 0;
    const wordCount = (text.match(/[\p{L}\p{N}]+/gu) || []).length;
    const linkText = nodes.reduce((n, el) => n + [...el.querySelectorAll("a")].reduce((a, link) => a + link.textContent.length, 0), 0);
    const linkRatio = text.length ? linkText / text.length : 1;
    return text.length * Math.min(1, wordCount / 40) * Math.max(0.15, 1 - linkRatio * 0.85);
  }

  function findRoot() {
    for (const selector of ["article", "main", "[role='main']"]) {
      const candidates = [...document.querySelectorAll(selector)].filter(visible).map((el) => ({ el, score: score(el) })).sort((a, b) => b.score - a.score);
      if (candidates[0]?.score > 0) return candidates[0].el;
    }
    let best = null;
    let bestScore = 0;
    for (const el of document.querySelectorAll("section, div")) {
      if (el.closest(EXCLUDED) || !visible(el) || el.children.length < 2) continue;
      const value = score(el);
      if (value > bestScore) { best = el; bestScore = value; }
    }
    return best;
  }

  function wordCount(text) { return (text.match(/[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*/gu) || []).length; }

  function plan(el) {
    const tokens = {};
    let counter = 0;
    const parts = [];
    const originalText = el.textContent.trim();
    const originalChildren = [...el.childNodes];
    const originalStyle = el.getAttribute("style");
    const originalClass = el.getAttribute("class");
    for (const child of originalChildren) {
      if (child.nodeType === Node.TEXT_NODE) {
        parts.push(child.nodeValue);
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const token = `[[R${++counter}X]]`;
        tokens[token] = child;
        parts.push(token);
      }
    }
    const apiText = parts.join("").trim();
    return { apiText, tokens, originalText, originalChildren, originalStyle, originalClass };
  }

  function ensureStyle() {
    let style = document.getElementById("readable-page-highlight-style");
    if (!style) {
      style = document.createElement("style");
      style.id = "readable-page-highlight-style";
      style.textContent = ".readable-page-changed{border-inline-start:3px solid rgba(48,101,81,.55)!important;padding-inline-start:8px!important;background-color:rgba(48,101,81,.04)!important}";
      (document.head || document.documentElement).append(style);
    }
  }

  function apply(id, text) {
    const state = states.get(id);
    if (!state || !state.el.isConnected || state.el.textContent.trim() !== state.originalText) return { status: "stale" };
    if (text === state.apiText) return { status: "unchanged" };
    const expected = Object.keys(state.tokens);
    const found = [...text.matchAll(/\[\[R\d+X\]\]/g)].map((m) => m[0]);
    const tokenStarts = [...text.matchAll(/\[\[R/g)].length;
    if (tokenStarts !== found.length || found.length !== expected.length || expected.some((token, i) => found[i] !== token)) return { status: "invalid" };
    records.set(state.el, state);
    const fragment = document.createDocumentFragment();
    let cursor = 0;
    for (const match of text.matchAll(/\[\[R\d+X\]\]/g)) {
      fragment.append(document.createTextNode(text.slice(cursor, match.index)));
      fragment.append(state.tokens[match[0]]);
      cursor = match.index + match[0].length;
    }
    fragment.append(document.createTextNode(text.slice(cursor)));
    state.el.replaceChildren(fragment);
    if (highlightEnabled) {
      ensureStyle();
      state.el.classList.add("readable-page-changed");
    }
    state.changed = true;
    return { status: "changed" };
  }

  function restore() {
    let count = 0;
    for (const [id, state] of states) {
      if (state.changed && state.el.isConnected) {
        state.el.replaceChildren(...state.originalChildren);
        if (state.originalStyle === null) state.el.removeAttribute("style"); else state.el.setAttribute("style", state.originalStyle);
        if (state.originalClass === null) state.el.removeAttribute("class"); else state.el.setAttribute("class", state.originalClass);
        records.delete(state.el);
        count++;
      }
    }
    states.clear();
    summary = null;
    document.getElementById("readable-page-highlight-style")?.remove();
    return { count, enabled: false, states: [] };
  }

  function scan(minWords) {
    const root = findRoot();
    if (!root) return { blocks: [], skipped: 0, eligible: 0, error: "No suitable article content was found." };
    const all = eligible(root);
    const blocks = [];
    let skipped = 0;
    for (const el of all) {
      const originalText = el.textContent.trim();
      if (wordCount(originalText) < minWords) { skipped++; continue; }
      if (blocks.length >= MAX_BLOCKS) { skipped += all.length - blocks.length - skipped; break; }
      const rect = el.getBoundingClientRect();
      const data = plan(el);
      const id = `${Date.now()}-${blocks.length}-${Math.random().toString(36).slice(2)}`;
      const state = { ...data, originalText, el, id, changed: false };
      states.set(id, state);
      blocks.push({ id, text: data.apiText, tokens: Object.keys(data.tokens), visible: rect.bottom > -100 && rect.top < innerHeight + 100, top: rect.top });
    }
    blocks.sort((a, b) => Number(b.visible) - Number(a.visible) || a.top - b.top);
    return { blocks, skipped, eligible: all.length, root: root.tagName.toLowerCase(), capped: all.length > MAX_BLOCKS };
  }

  globalThis[KEY] = {
    state() { return { enabled: states.size > 0, states: [...states.values()].map((s) => ({ id: s.id, changed: s.changed })), highlight: highlightEnabled, summary, mode: currentMode }; },
    scan,
    apply,
    restore,
    setHighlight(value) {
      highlightEnabled = Boolean(value);
      for (const state of states.values()) {
        if (!state.changed) continue;
        if (highlightEnabled) { ensureStyle(); state.el.classList.add("readable-page-changed"); }
        else state.el.classList.remove("readable-page-changed");
      }
      return highlightEnabled;
    },
    setSummary(value, mode) { summary = value; currentMode = mode; return true; }
  };
})();

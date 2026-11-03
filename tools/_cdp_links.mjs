// Print every anchor (text + href) of a page through CDP, for finding download links that innerText cannot show.
//
// Usage: node tools/_cdp_links.mjs <url> [pattern]
// CDP endpoint: 127.0.0.1:${CDP_PORT:-9224}

const url = process.argv[2];
const pattern = process.argv[3] ? new RegExp(process.argv[3], "i") : null;
if (!url) {
  console.error("usage: node tools/_cdp_links.mjs <url> [pattern]");
  process.exit(2);
}
const BASE = `http://127.0.0.1:${process.env.CDP_PORT || 9224}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const created = await fetch(`${BASE}/json/new?${encodeURIComponent(url)}`, { method: "PUT" }).then((r) => r.json());
const ws = new WebSocket(created.webSocketDebuggerUrl);
await new Promise((res, rej) => {
  ws.addEventListener("open", res);
  ws.addEventListener("error", () => rej(new Error("ws error")));
});
let id = 1;
const pending = new Map();
ws.addEventListener("message", (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    const { resolve } = pending.get(m.id);
    pending.delete(m.id);
    resolve(m.result);
  }
});
const send = (method, params = {}) =>
  new Promise((resolve) => {
    const i = id++;
    pending.set(i, { resolve });
    ws.send(JSON.stringify({ id: i, method, params }));
  });
await send("Page.enable");
await sleep(2500);
const r = await send("Runtime.evaluate", {
  expression: "JSON.stringify(Array.from(document.querySelectorAll('a')).map(a => [a.innerText.trim().slice(0,80), a.href]))",
  returnByValue: true,
});
const anchors = JSON.parse(r.result.value || "[]");
for (const [text, href] of anchors) {
  if (!pattern || pattern.test(href) || pattern.test(text)) console.log(`${text}\t${href}`);
}
ws.close();
await fetch(`${BASE}/json/close/${created.id}`).catch(() => {});

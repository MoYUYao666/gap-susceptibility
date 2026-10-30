// Read an existing page from the user's browser over CDP: print its text and save a screenshot.
//
// Usage: node tools/_cdp_read_page.mjs <urlSubstring> [outPng] [maxChars]
// CDP port: $env:CDP_PORT or 9222. Uses the already-open tab (never creates one).

import { writeFileSync } from "node:fs";

const urlSub = (process.argv[2] || "").toLowerCase();
const outPng = process.argv[3] || "local_runs/current_page.png";
const maxChars = Number(process.argv[4] || 12000);
const port = process.env.CDP_PORT || "9222";
const BASE = `http://127.0.0.1:${port}`;

const targets = await fetch(`${BASE}/json/list`).then((r) => r.json());
const pages = targets.filter((t) => t.type === "page");
const page = pages.find((t) => (t.url || "").toLowerCase().includes(urlSub)) ||
  pages.find((t) => (t.title || "").toLowerCase().includes(urlSub)) ||
  pages[0];
if (!page) {
  console.error("no page targets");
  process.exit(2);
}
console.log("TITLE:", page.title);
console.log("URL:", page.url);

const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((res, rej) => {
  ws.addEventListener("open", res);
  ws.addEventListener("error", () => rej(new Error("ws error")));
});
let id = 1;
const pending = new Map();
ws.addEventListener("message", (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    const { resolve, reject } = pending.get(m.id);
    pending.delete(m.id);
    if (m.error) reject(new Error(JSON.stringify(m.error)));
    else resolve(m.result);
  }
});
const send = (method, params = {}) =>
  new Promise((resolve, reject) => {
    const i = id++;
    pending.set(i, { resolve, reject });
    ws.send(JSON.stringify({ id: i, method, params }));
  });

await send("Page.enable");
const r = await send("Runtime.evaluate", {
  expression: "document.body ? document.body.innerText : ''",
  returnByValue: true,
});
const text = r?.result?.value || "";
console.log("--- TEXT (" + text.length + " chars) ---");
console.log(text.slice(0, maxChars));
try {
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  writeFileSync(outPng, Buffer.from(shot.data, "base64"));
  console.log("--- SCREENSHOT:", outPng, "---");
} catch (e) {
  console.log("screenshot failed:", e.message);
}
ws.close();

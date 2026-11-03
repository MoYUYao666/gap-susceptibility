// Read a page from the user's running Edge by talking to the browser-level DevTools WebSocket.
//
// Why not /json/list: this Edge instance exposes only the browser WebSocket (the HTTP endpoints are refused), so the page
// list comes from Target.getTargets and the page itself is reached with a flattened session.
//
// Usage: node tools/_cdp_browser_page.mjs <urlSubstring> [outPng]
// Reads the port and WS path from %LOCALAPPDATA%\Microsoft\Edge\User Data\DevToolsActivePort.

import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const urlSub = (process.argv[2] || "").toLowerCase();
const outPng = process.argv[3] || "local_runs/current_page.png";

const ud = join(process.env.LOCALAPPDATA, "Microsoft", "Edge", "User Data");
const [port, wsPath] = readFileSync(join(ud, "DevToolsActivePort"), "utf8").trim().split(/\r?\n/);
const wsUrl = `ws://127.0.0.1:${port}${wsPath}`;
console.log("browser ws:", wsUrl);

const ws = new WebSocket(wsUrl);
await new Promise((res, rej) => {
  ws.addEventListener("open", res);
  ws.addEventListener("error", () => rej(new Error("browser ws error")));
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
const send = (method, params = {}, sessionId) =>
  new Promise((resolve, reject) => {
    const i = id++;
    const msg = { id: i, method, params };
    if (sessionId) msg.sessionId = sessionId;
    pending.set(i, { resolve, reject });
    ws.send(JSON.stringify(msg));
  });

const { targetInfos } = await send("Target.getTargets");
const pages = targetInfos.filter((t) => t.type === "page");
console.log("open pages:", pages.length);
for (const t of pages) console.log("  -", (t.title || "").slice(0, 60), "|", (t.url || "").slice(0, 100));
const page = pages.find((t) => (t.url || "").toLowerCase().includes(urlSub)) ||
  pages.find((t) => (t.title || "").toLowerCase().includes(urlSub)) || pages[0];
if (!page) {
  console.error("no page found");
  process.exit(2);
}
const { sessionId } = await send("Target.attachToTarget", { targetId: page.targetId, flatten: true });
await send("Page.enable", {}, sessionId);
const r = await send("Runtime.evaluate", {
  expression: "document.body ? document.body.innerText : ''",
  returnByValue: true,
}, sessionId);
const text = r?.result?.value || "";
console.log("TITLE:", page.title);
console.log("URL:", page.url);
console.log("--- TEXT (" + text.length + " chars) ---");
console.log(text.slice(0, 12000));
try {
  const shot = await send("Page.captureScreenshot", { format: "png" }, sessionId);
  writeFileSync(outPng, Buffer.from(shot.data, "base64"));
  console.log("--- SCREENSHOT:", outPng, "---");
} catch (e) {
  console.log("screenshot failed:", e.message);
}
ws.close();

// Minimal CDP text fetcher: open a URL in the debugging browser, wait for load, print the rendered text.
//
// Usage: node tools/_cdp_fetch.mjs <url> [maxChars]
// The debugging browser is whatever listens on 127.0.0.1:9222 (started separately with --remote-debugging-port).
// Output goes to stdout as plain text; the tab is closed afterwards so the user's browser is left untouched.

const url = process.argv[2];
const maxChars = Number(process.argv[3] || 20000);
if (!url) {
  console.error("usage: node tools/_cdp_fetch.mjs <url> [maxChars]");
  process.exit(2);
}

const BASE = `http://127.0.0.1:${process.env.CDP_PORT || 9222}`;

async function createTarget() {
  const r = await fetch(`${BASE}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!r.ok) throw new Error(`new target failed: ${r.status}`);
  return r.json();
}

function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let nextId = 1;
  const pending = new Map();
  ws.addEventListener("message", (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result);
    }
  });
  const ready = new Promise((res, rej) => {
    ws.addEventListener("open", () => res());
    ws.addEventListener("error", (e) => rej(new Error("ws error")));
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { ws, ready, send };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const target = await createTarget();
const { ws, ready, send } = connect(target.webSocketDebuggerUrl);
await ready;
await send("Page.enable");
let text = "";
for (let attempt = 0; attempt < 20; attempt++) {
  await sleep(700);
  const r = await send("Runtime.evaluate", {
    expression: "document.body ? document.body.innerText : ''",
    returnByValue: true,
  });
  text = (r.result && r.result.value) || "";
  if (text.trim().length > 4000) break;
}
console.log(text.slice(0, maxChars));
ws.close();
await fetch(`${BASE}/json/close/${target.id}`).catch(() => {});

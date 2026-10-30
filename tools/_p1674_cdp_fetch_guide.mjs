// CDP one-shot page-text fetcher (Node 24, global WebSocket).
//
// For the CVIU Guide-for-Authors pass: ScienceDirect answers headless clients with 403 (CPE00001),
// while a visible Edge renders the page normally. Usage pattern:
//   1) launch Edge with --remote-debugging-port=9224 --user-data-dir=<temp> "<guide url>"
//   2) node tools/_p1674_cdp_fetch_guide.mjs <url-substring> <outfile> [waitMs]
// The script attaches to an existing page target (creating one only if none matches), waits for the
// body text to settle, and writes title + text to the output file. It does not close the browser.
//
// Env: CDP_BASE (default http://127.0.0.1:9224)

import { writeFileSync } from "node:fs";

const [, , urlPart, outfile, waitArg] = process.argv;
if (!urlPart || !outfile) {
  console.error("usage: node tools/_p1674_cdp_fetch_guide.mjs <url-substring> <outfile> [waitMs]");
  process.exit(2);
}
const base = process.env.CDP_BASE || "http://127.0.0.1:9224";
const waitMs = Number(waitArg || 30000);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function jsonList() {
  const r = await fetch(base + "/json/list");
  if (!r.ok) throw new Error("json/list HTTP " + r.status);
  return r.json();
}

let targets = [];
for (let i = 0; i < 20; i++) {
  try {
    targets = await jsonList();
    if (targets.some((t) => t.type === "page")) break;
  } catch {
    /* browser may still be starting */
  }
  await sleep(700);
}
const pages = targets.filter((t) => t.type === "page");
let tgt = pages.find((t) => (t.url || "").includes(urlPart)) || pages[0];
if (!tgt) {
  console.error("no page target found; targets:", JSON.stringify(targets.map((t) => [t.type, t.url])));
  process.exit(3);
}
console.log("attached to:", tgt.url);

const ws = new WebSocket(tgt.webSocketDebuggerUrl);
let msgId = 0;
const pending = new Map();
ws.addEventListener("message", (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    pending.get(m.id)(m);
    pending.delete(m.id);
  }
});
const send = (method, params = {}) =>
  new Promise((resolve) => {
    const id = ++msgId;
    pending.set(id, resolve);
    ws.send(JSON.stringify({ id, method, params }));
  });

await new Promise((resolve, reject) => {
  ws.addEventListener("open", resolve);
  ws.addEventListener("error", reject);
});
await send("Runtime.enable");

const deadline = Date.now() + waitMs;
let text = "";
let title = "";
let lastLen = -1;
let stable = 0;
while (Date.now() < deadline) {
  await sleep(1500);
  const t = await send("Runtime.evaluate", {
    expression: "document.title + '\\n@@@\\n' + (document.body ? document.body.innerText : '')",
    returnByValue: true,
  });
  const val = t.result?.result?.value || "";
  const cut = String(val).indexOf("\n@@@\n");
  title = cut >= 0 ? String(val).slice(0, cut) : title;
  text = cut >= 0 ? String(val).slice(cut + 5) : String(val);
  if (text.length === lastLen) stable += 1;
  else stable = 0;
  lastLen = text.length;
  if (text.length > 1500 && stable >= 2) break;
}

writeFileSync(
  outfile,
  "URL_PART: " + urlPart + "\nTITLE: " + title + "\nCHARS: " + text.length + "\n\n" + text,
  "utf8",
);
console.log("title:", title);
console.log("chars:", text.length);
console.log("written:", outfile);
ws.close();

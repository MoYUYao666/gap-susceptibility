// Batch CDP page-text fetcher (Node 24, global WebSocket).
//
// Same route as tools/_p1674_cdp_fetch_guide.mjs (visible Edge, ScienceDirect blocks headless with
// 403/CPE00001), but loops over many URLs on ONE tab: navigate -> poll body text until it stops
// growing AND the expected marker appears (or the timeout expires) -> write to file.
//
// Usage: node tools/_p1678_cdp_batch_fetch.mjs <jobs.json>
//   jobs.json = [{"url": "...", "out": "C:/.../x.txt", "expect": "Web of Science Core Collection"}, ...]
// Env: CDP_BASE (default http://127.0.0.1:9227)

import { readFileSync, writeFileSync } from "node:fs";

const jobsPath = process.argv[2];
if (!jobsPath) {
  console.error("usage: node tools/_p1678_cdp_batch_fetch.mjs <jobs.json>");
  process.exit(2);
}
const jobs = JSON.parse(readFileSync(jobsPath, "utf8"));
const base = process.env.CDP_BASE || "http://127.0.0.1:9227";
const PER_JOB_MS = Number(process.env.PER_JOB_MS || 60000);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let targets = [];
for (let i = 0; i < 25; i++) {
  try {
    const r = await fetch(base + "/json/list");
    if (r.ok) {
      targets = await r.json();
      if (targets.some((t) => t.type === "page")) break;
    }
  } catch {
    /* browser still starting */
  }
  await sleep(700);
}
const page = targets.find((t) => t.type === "page");
if (!page) {
  console.error("no page target; targets:", JSON.stringify(targets.map((t) => [t.type, t.url])));
  process.exit(3);
}

const ws = new WebSocket(page.webSocketDebuggerUrl);
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

for (const job of jobs) {
  const label = job.url.slice(0, 110);
  let ok = false;
  let title = "";
  let text = "";
  try {
    await send("Page.navigate", { url: job.url });
    const deadline = Date.now() + PER_JOB_MS;
    let last = -1;
    let stable = 0;
    while (Date.now() < deadline) {
      await sleep(1800);
      const t = await send("Runtime.evaluate", {
        expression: "document.title + '\\n@@@\\n' + (document.body ? document.body.innerText : '')",
        returnByValue: true,
      });
      const val = String(t.result?.result?.value || "");
      const cut = val.indexOf("\n@@@\n");
      title = cut >= 0 ? val.slice(0, cut) : title;
      text = cut >= 0 ? val.slice(cut + 5) : val;
      if (text.length === last) stable += 1;
      else stable = 0;
      last = text.length;
      const hasMarker = !job.expect || text.includes(job.expect);
      if (text.length > 800 && stable >= 1 && hasMarker) {
        ok = true;
        break;
      }
    }
  } catch (err) {
    console.error("navigate error:", String(err));
  }
  writeFileSync(
    job.out,
    "URL: " + job.url + "\nTITLE: " + title + "\nCHARS: " + text.length +
      "\nMARKER: " + (job.expect || "(none)") + " -> " + (ok ? "found" : "NOT found") +
      "\n\n" + text,
    "utf8",
  );
  console.log("%-8s %6d chars  %s", ok ? "OK" : "PARTIAL", text.length, label);
}
ws.close();

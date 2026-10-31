// Evaluate an arbitrary JS expression in a page of the user's running Edge, and print the result.
//
// Usage: node tools/_cdp_eval.mjs "<urlSubstring>" "<jsExpression>" [outJsonFile]
// The expression must evaluate to something JSON-serialisable (wrap it in JSON.stringify yourself if needed).

import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const urlSub = (process.argv[2] || "").toLowerCase();
const expression = process.argv[3] || "document.title";
const outFile = process.argv[4] || "";

const ud = join(process.env.LOCALAPPDATA, "Microsoft", "Edge", "User Data");
const [port, wsPath] = readFileSync(join(ud, "DevToolsActivePort"), "utf8").trim().split(/\r?\n/);
const wsUrl = `ws://127.0.0.1:${port}${wsPath}`;

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
const page = pages.find((t) => (t.url || "").toLowerCase().includes(urlSub)) ||
  pages.find((t) => (t.title || "").toLowerCase().includes(urlSub)) || pages[0];
const { sessionId } = await send("Target.attachToTarget", { targetId: page.targetId, flatten: true });
const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true }, sessionId);
const val = r?.result?.value;
const text = typeof val === "string" ? val : JSON.stringify(val, null, 1);
if (outFile) writeFileSync(outFile, text);
console.log(text);
ws.close();

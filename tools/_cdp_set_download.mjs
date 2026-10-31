// Set the Edge download directory over the browser-level DevTools WebSocket and (optionally) trigger a page command.
//
// Usage (PowerShell):  $env:JOE_DLDIR="D:\...\joe_dl"; $env:JOE_CMD="command('DownloadTmp_...')"; node tools/_cdp_set_download.mjs
// The browser endpoint is read from %LOCALAPPDATA%\Microsoft\Edge\User Data\DevToolsActivePort.

import { readFileSync } from "node:fs";
import { join } from "node:path";

const dlDir = process.env.JOE_DLDIR || "local_runs/joe_dl";
const jsCmd = process.env.JOE_CMD || "";
const pageUrlSub = (process.env.JOE_PAGE || "resubmission").toLowerCase();

const ud = join(process.env.LOCALAPPDATA, "Microsoft", "Edge", "User Data");
const [port, wsPath] = readFileSync(join(ud, "DevToolsActivePort"), "utf8").trim().split(/\r?\n/);
const ws = new WebSocket(`ws://127.0.0.1:${port}${wsPath}`);
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

await send("Browser.setDownloadBehavior", { behavior: "allow", downloadPath: dlDir });
console.log("download dir:", dlDir);

if (jsCmd) {
  const { targetInfos } = await send("Target.getTargets");
  const pages = targetInfos.filter((t) => t.type === "page");
  const page = pages.find((t) => (t.url || "").toLowerCase().includes(pageUrlSub)) || pages[0];
  const { sessionId } = await send("Target.attachToTarget", { targetId: page.targetId, flatten: true });
  const r = await send("Runtime.evaluate", { expression: jsCmd, returnByValue: true }, sessionId);
  console.log("command result:", JSON.stringify(r?.result?.value));
}
ws.close();

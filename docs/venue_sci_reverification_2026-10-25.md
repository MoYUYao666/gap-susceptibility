# SCIE 收录复核记录（2026-10-25）

> **task-26 交付件**。核实人：agent `p3-stats`。
> 触发：独立审计 `docs/audit_docs_rules_2026-10-25.md` 的 should-fix 项 ——
> `docs/VENUE_SCI_REGISTRY.md` 的 `来源URL` / `核实日期` 两列全部是 `待核`，且文档自述
> "尚未按 §2 用 MJL 逐条复核"。本轮把五条目标刊物的 MJL 核实补齐。
> **日期口径**：全部核实动作发生在 **2026-10-25**（Asia/Shanghai，12:23–12:40 之间）。

---

## 1. 结论（一句话）

**五条目标刊物全部确认 SCIE**（Clarivate Master Journal List 的
`Web of Science Core Collection: Science Citation Index Expanded`）：
Neurocomputing、Pattern Analysis and Applications、Pattern Recognition Letters（P3 与 Commentary 同刊）、
IEEE Journal of Oceanic Engineering。
**没有任何一条是 ESCI-only / Scopus-only**，**本轮没有任何投稿决定需要改变**。

---

## 2. 逐刊结果

| # | 刊物 | ISSN / eISSN | 出版商 | 判定 | MJL 来源 URL（本轮实际访问） | 核实日期 |
|---|---|---|---|---|---|---|
| 1 | Neurocomputing | 0925-2312 / 1872-8286 | Elsevier | **SCIE ✅** | `https://mjl.clarivate.com/search-results?issn=0925-2312&hide_exact_match_fl=true` | 2026-10-25 |
| 2 | Pattern Analysis and Applications | 1433-7541 / 1433-755X | Springer | **SCIE ✅**（+ Springer 第二来源）| `https://mjl.clarivate.com/search-results?issn=1433-7541&hide_exact_match_fl=true` | 2026-10-25 |
| 3 | Pattern Recognition Letters（P3 行）| 0167-8655 / 1872-7344 | Elsevier | **SCIE ✅** | `https://mjl.clarivate.com/search-results?issn=0167-8655&hide_exact_match_fl=true` | 2026-10-25 |
| 4 | IEEE Journal of Oceanic Engineering | 0364-9059 / 1558-1691 | IEEE | **SCIE ✅** | `https://mjl.clarivate.com/search-results?issn=0364-9059&hide_exact_match_fl=true` | 2026-10-25 |
| 5 | Pattern Recognition Letters（Commentary 行）| 0167-8655 / 1872-7344 | Elsevier | **SCIE ✅**（与第 3 行同一刊，一次核实覆盖两行）| 同第 3 行 | 2026-10-25 |

**MJL 页面原文关键行**（逐字摘录，供复核）：

- Neurocomputing：`Exact Match Found` / `Web of Science Core Collection: Science Citation Index Expanded` /
  `Additional Web of Science Indexes: Current Contents Engineering, Computing & Technology | Essential Science Indicators`
- Pattern Analysis and Applications：`Exact Match Found` / `Web of Science Core Collection: Science Citation Index Expanded` /
  同样的 Additional Indexes
- Pattern Recognition Letters：结果标题为 `Journals Relevant To "0167-8655"`（1 条结果，刊名与 ISSN 均匹配）/
  `Web of Science Core Collection: Science Citation Index Expanded`
- IEEE Journal of Oceanic Engineering：结果标题为 `Journals Relevant To "0364-9059"`（1 条结果，刊名与 ISSN 均匹配）/
  `Web of Science Core Collection: Science Citation Index Expanded`

> MJL 的 `View profile page`（含覆盖年份明细）需要免费登录，本轮**未登录**；
> 但搜索结果的 `Web of Science Core Collection` 行本身已是对收录类型的官方陈述，足以按 §2 判定。

---

## 3. 访问路由与阻塞项（如实记录）

| 目标 | 结果 | 说明 |
|---|---|---|
| **Clarivate MJL（mjl.clarivate.com）** | ✅ 成功 | 该站是 JS 单页应用：静态 `web_fetch` 返回 HTTP 200 但**只有页面标题**，无数据 ⇒ 必须走**已登录 Edge 的 CDP 代理**（`web-access` skill，端口 9222）。四刊页面均在浏览器渲染后读到结果卡片。**本轮全部判定都来自这条路由。** |
| **Springer 期刊页（PAA）** | ✅ 成功 | `https://link.springer.com/journal/10044`（说明：`/journal/10489` 是 *Applied Intelligence*，不是 PAA；`/journal/10044` 才是本刊）页面 "Abstracted and indexed in" 段落**逐项列出 `Science Citation Index Expanded (SCIE)`**，作为 PAA 的第二来源。`/journal/10044/abstracting-and-indexing` 子路径返回 404。 |
| **Elsevier A&I 页（Neurocomputing / PRL）** | ❌ 未取得 | `https://www.sciencedirect.com/journal/neurocomputing/about/abstracting-and-indexing`（及 PRL 同路径）**重定向回期刊首页**，页面无 Abstracting & Indexing 列表；`journalinsights.elsevier.com/journals/<issn>` 也已重定向到 ScienceDirect 首页。Elsevier 期刊页只公开展示 CiteScore / Impact Factor，**不含索引数据库清单** ⇒ 这两条**仅由 MJL 一手来源支撑**，未做第二来源交叉。**阻塞类型：无该页面（站点已改版/移除）**。 |
| **IEEE A&I 页（JOE）** | ❌ 未取得 | `https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=48` 与 `https://ieeexplore.ieee.org/xpl/aboutJournal.jsp?punumber=48` 均无 Abstracting & Indexing 列表（只有 Aims & Scope 与指标）。**阻塞类型：无该页面**。同理仅由 MJL 支撑。 |
| **MIAR（第三方旁证）** | ❌ 超时 | `https://miar.ub.edu/issn/0167-8655` 返回 **HTTP 504 / 响应超时**。**阻塞类型：网络**。按 §2，第三方本就只能作旁证，缺失不影响判定。 |
| **LetPub（第三方旁证）** | 未使用 | 避免无谓抓取；第三方旁证非必需（§2 第 4 步：只能作旁证，不能单独作为依据）。 |
| **JCR 分区（quartile）** | ❌ 不可得 | JCR 需订阅登录，公共页面不显示分区 ⇒ **按规则不填分区**；仅在 registry §3.1 记录出版商页面公开展示的 IF/CiteScore，并标注为第三方数据、不用于资格判定。 |

---

## 4. 指标（publisher-displayed，第三方 JCR/CiteScore 数据，仅记录、不用于判定）

| 刊物 | 指标 | 来源页 |
|---|---|---|
| Neurocomputing | Impact Factor **6.7**；CiteScore **10.8** | `https://www.sciencedirect.com/journal/neurocomputing` |
| Pattern Analysis and Applications | Journal Impact Factor **2.6 (2025)**；5-year **2.4 (2025)** | `https://link.springer.com/journal/10044` |
| Pattern Recognition Letters | Impact Factor **3.5**；CiteScore **7.8** | `https://www.sciencedirect.com/journal/pattern-recognition-letters` |
| IEEE Journal of Oceanic Engineering | Impact Factor **5.6**；CiteScore **8.6**；Eigenfactor 0.00504；AIS 1.169 | `https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=48` |

> **不填 JCR 分区**：分区表需登录，公开页面未见；按规则不做推断。
> 上述 IF/CiteScore 是出版社页面公开展示的第三方数据，**仅作记录**。

---

## 5. 对在审/待投稿件的影响

| 稿件 | 目标刊 | 状态 | 影响 |
|---|---|---|---|
| Paper A（`paper合/`）| Neurocomputing | `NEUCOM-D-26-23760` With Editor | **无需改投/改目标**；SCIE 已复核 |
| A1（`paper_a1/`）| Pattern Analysis and Applications | `0a4629f0-…` With editor | 同上 |
| P3（`paper3/paper_ieee/`）| Pattern Recognition Letters | `PRLETTERS-D-26-02671` With Editor | 同上 |
| A23（`paper_a2/`）| IEEE Journal of Oceanic Engineering | `26-0663`（下一版修订准备中）| 同上；**不影响**下一版修订/cover letter 流程 |
| Commentary（`paper_review_prl/`）| Pattern Recognition Letters | `PRLETTERS-D-26-02402` 在审 | 同上；若将来改投备选，仍须对备选刊按 §2 重新 MJL 核实 |

**两条规则层面的后果**：

1. **本表现在构成 §2 要求的留痕**：五条目标刊物均有真实 `来源URL` + `核实日期` + `核实途径`
   （核实人：agent `p3-stats`）。此前审计指出的"待核"缺口已闭合。
2. **下一次投稿/改投前仍须重核**：MJL 收录状态会变化（ESCI→SCIE、SCIE 被移除等都可能发生），
   本记录只证明 **2026-10-25** 的状态。**本记录不覆盖备选/候选刊物**（registry §4 的刊物仍是 `待核`，
   按规则不得在核实前作为投稿目标）。

---

## 6. 复现命令（本机）

```powershell
# 1) 联网前置（共享 CDP 代理；若 Edge 已退出需先启动 Edge，端口 9222）
node "C:\Users\hongr\.agents\skills\web-access\scripts\check-deps.mjs"

# 2) 每刊一次：开后台 tab → 读渲染后的正文（MJL 是 JS SPA，静态 fetch 无数据）
curl -s -X POST --data-raw "https://mjl.clarivate.com/search-results?issn=0925-2312&hide_exact_match_fl=true" http://localhost:3456/new
curl -s -X POST "http://localhost:3456/eval?target=<ID>" -d "document.body.innerText.slice(0,2500)"

# 3) 第二来源（PAA）
curl -s -X POST --data-raw "https://link.springer.com/journal/10044" "http://localhost:3456/navigate?target=<ID>"
```

> 浏览器自动化操作存在账号风控风险（见 `web-access` skill 的提示）；本轮只做**只读浏览**，未登录、未提交任何表单。

---

## 7. 免责/边界

- 本轮**没有编造任何 URL 或日期**：所有 URL 均为实际访问地址，日期为本机系统时间 2026-10-25。
- **没有把"未取得第二来源"写成"已确认"**：Neurocomputing / PRL / IEEE JOE 明确标注"仅 MJL 一手来源"。
- **没有把第三方数据当依据**：IF/CiteScore 仅记录；JCR 分区未取得即留空。
- 本记录**只覆盖 registry §3 的五条目标刊物**，不覆盖 §4 的备选/候选（它们仍是 `待核`）。

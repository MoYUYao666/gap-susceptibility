# -*- coding: utf-8 -*-
r"""从 LetPub 期刊页提取"审稿周期/录用比例"等条目（只读，用于选刊决策留档）。

为什么自己解析：本会话 web_fetch 不可用；且 LetPub 提供的**作者实测审稿周期**是公开渠道里
少数能拿到的时效数据（官方 insights 页需浏览器访问）。

    python tools/_fetch_letpub_stats.py 3563 2513
"""
from __future__ import annotations

import re
import sys
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

KEYS = ["影响因子", "中科院分区", "平均审稿速度", "平均录用比例", "审稿周期", "版面费",
        "是否OA", "年发文量", "自引率", "CiteScore"]


def fetch(jid: str) -> str:
    url = f"https://www.letpub.com.cn/index.php?journalid={jid}&page=journalapp&view=detail"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")


def strip_tags(html: str) -> str:
    t = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", t)


def main() -> int:
    ids = sys.argv[1:] or ["3563", "2513"]
    for jid in ids:
        try:
            text = strip_tags(fetch(jid))
        except Exception as e:
            print(f"  journalid={jid} ❌ {e}")
            continue
        # 期刊名
        m = re.search(r"([A-Z][A-Za-z&\- ]{4,60})\s*\|", text)
        print(f"=== journalid={jid} ===")
        for k in KEYS:
            # 抓关键词后 0–60 字符，且必须含数字或"暂无"
            for mm in re.finditer(re.escape(k) + r"[^。；;]{0,70}", text):
                seg = mm.group(0).strip()
                if re.search(r"\d", seg) and "LetPub" not in seg:
                    print(f"  {k}: {seg[:110]}")
                    break
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

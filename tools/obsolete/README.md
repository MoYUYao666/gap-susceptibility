# 已废弃的一次性审计脚本

这两个脚本是**过去某一轮**写的回归检查，断言直接写死在当时的论文文本上，**已经不适用于当前 revision**，跑出来的 FAIL 是脚本失效而不是论文回归：

| 脚本 | 失效原因 |
|---|---|
| `audit_fix_regression.py` | 断言里包含 `'7.5' not in 全文`（全篇任何位置出现 `7.5` 就判失败 —— 本身不可能通过）、`'budget $128$--$152$' in 全文`（论文措辞已改）、`'0.961'/'175.4'/'0.991' not in 全文`（这些数字在后续小节里合法出现） |
| `audit_fix_regression2.py` | 直接崩：`l23.index('Fifteenth,')` —— limitations 段已重写，`Fifteenth,` 不再存在于该行；另一条断言 `l23.count('at rank 6') == 1` 同样绑定旧文本 |

## 现在用什么

```bash
python tools/ap3_compile_check.py paper_ap3   # 错误/未定义引用/未定义引文/重复标签/Overfull 判定（退出码即门禁）
python tools/audit_mechanics.py               # label 与 \ref 的一致性（unused labels / dangling refs）
```

两个脚本的判定都是**从编译产物与源文本重新计算**的，不绑定具体措辞，因此可以长期使用。

> 保留这两个旧文件只为审计留痕（说明曾检查过什么），**不要**把它们的结果当作当前 revision 的结论。
> 若要复用其中的意图（例如"某旧数字不应再出现"），请改写成对当前文本的检查，并注明对应的 revision。

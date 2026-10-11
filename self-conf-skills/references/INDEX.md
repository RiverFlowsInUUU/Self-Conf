# 文档索引 · 遇到什么问题去哪儿查

> **本文件是 `references/` 这一区的指路标。** 根 [`AGENTS.md`](../../AGENTS.md) 只留指针，
> 详情在这里 —— 这样入口文件不必为了塞下这张表而压缩正文。
>
> **为什么要有索引**：`references/` 共 **11 篇 · 900+ 个节**（合计数百 KB），
> 最大的一节也只有 ~5 KB。**不要整篇读**，按需 grep 定位到节，一次只读 2~5 KB。

---

## 一、怎么搜（先看这个）

```bash
# ① grep 拿行号与节标题 ② 只读那一节
#    （从命中行往上找最近标题，往下读到下一个同级标题）
grep -n "include-all" self-conf-skills/references/profiles/clash.md
```

**关键词要选得具体** —— 泛词会命中几十处，具体词通常 1~5 处（下表都实测过）：

| 想问什么 | 去哪份 | 用这些词（括号是实测命中数） |
|:--|:--|:--|
| mihomo 的组/节点怎么配 | `profiles/clash.md` | `include-all-proxies`(10) · `respect-rules`(7) · `nameserver-policy`(19) |
| Surge 的键怎么配 | `profiles/surge.md` | `policy-regex-filter`(4) · `extended-matching`(16) · `hijack-dns`(17) |
| Egern 的段怎么配 | `profiles/egern.md` | `policy_groups`(5) · `proxy_nameservers`(37) |
| Stash 覆写怎么改 | `profiles/stash.md` | `#!replace`(5) · `direct-nameserver`(3) · `倍率三档`(5) |
| DNS 泄露怎么查 | `dns.md` | `抓包`(1) · `假 IP`(10) · `引导`(11) |
| 规则集怎么选/多重 | `rulesets.md` | `重量`(4) · `体量`(5) · `刷新周期`(6) |
| 改完怎么验证 | `ops.md` | `make_min`(7) · `升号`(7) · `动线`(8) |
| 出问题 | `pitfalls.md` | `假通过`(3) · `广告拦不住`(4) · `拒绝加载`(6) |
| 门禁本身 | `gates.md` | `自查清单`(1) · `判别力`(15) · `注错`(15) |

⚠️ 若 grep 命中 >20 处 ⇒ **关键词太泛**，换更具体的词（或先 grep 标题看目录：
`grep -n "^#\{2,4\} " <file>`）。

---

## 二、任务路由：我要做 X，该读什么、跑什么

| 我要做的事 | 先读 | 然后跑 | 判据会抓什么 |
|:--|:--|:--|:--|
| 改 Surge 的键/组/规则 | `profiles/surge.md` | `make_min.py --apply` | 结构 · DNS · 分流覆盖 |
| 改 Egern 的段 | `profiles/egern.md` | `make_min.py --apply` | 结构 · DNS · 分流覆盖 |
| 改 mihomo 的组/规则/DNS | `profiles/clash.md`（本侧判据清单在 §18.4） | `build_profiles.py` | 脚本↔静态对拍 · 头注数字 |
| 改 Stash 覆写 | `profiles/stash.md` | 三条 Stash 判据 | 结构与引用 · DNS 可达 · 四侧对拍 |
| 改自托管规则集内容 | `rulesets.md` | `build_rules.py` | 生成物新鲜度 · 裸 IP |
| 排查 DNS 泄露 | `dns.md` | 各内核 DNS 审计器 | 14 项分级判据 |
| 排查「配置能加载但不通」 | `pitfalls.md` | — | 多为此文件记录的静默失效类 |
| 加/改一道闸门 | `gates.md` 的自查清单 | 注错验证 | 负样例回归 |
| 发版 / 升版号 | `ops.md` | `release_publish.py` | 一天一版 · Release 断言 |

---

## 三、各篇文档是什么

| 文件 | 管什么 | 什么时候读 |
|:--|:--|:--|
| `profiles/surge.md` | Surge 逐键语义与加固 | 改 Surge 配置 |
| `profiles/egern.md` | Egern 逐段语义与加固 | 改 Egern 配置 |
| `profiles/clash.md` | mihomo 逐键语义（含 mihomo 独有的六个特点） | 改 mihomo 配置 |
| `profiles/stash.md` | Stash 覆写语义 · 与 mihomo 的键映射 · DNS 事故 | 改 Stash 覆写 |
| **`DIFFERENCES.md`** | **四侧机制差异汇总**（谁用 `smart` 谁用 `url-test`、四个键名、DNS 四条分岔、「三内核」的定义） | **把某侧做法搬到另一侧之前** |
| `dns.md` | DNS 原理 · 泄露面 · 四侧语法对照 | 任何 DNS 问题 |
| `rulesets.md` | 规则集的选型、重量、刷新周期 | 增删规则集 |
| `ops.md` | 操作手册：生成链、验证、发版 | 做事之前 |
| `pitfalls.md` | 踩过的坑与「假通过」形态 | 出问题 / 写判据 |
| `gates.md` | 门禁纪律 · 判别力 · 注错三条铁律 | 改判据 |
| `INDEX.md` | 本文件（路由表） | 不知道去哪查时 |

另有 `intent.json`（机读的路由意图 IR，由 `build_ir.py` 生成，**不是人读的文档**）。

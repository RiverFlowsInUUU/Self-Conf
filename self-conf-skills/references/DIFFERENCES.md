# 四侧机制差异总表

> **何时读**：想「把某一侧的做法搬到另一侧」时 —— **先读这里**。
> 本仓大量「看起来不一致」的地方是**刻意的**，机制决定，不是漂移。

> 定位：本文件是**差异的汇总入口**。逐键细节仍在各侧主文档
> （`profiles/surge.md` · `profiles/egern.md` · `profiles/clash.md` · `profiles/stash.md`）。
>
> 目录
> [1 · 一张表看懂四侧](#1--一张表看懂四侧) ·
> [2 · 三条铁律](#2--三条铁律) ·
> [3 · 差异清单（按机制归类）](#3--差异清单按机制归类) ·
> [4 · 谁是「三内核」](#4--谁是三内核) ·
> [5 · 判据如何守这些差异](#5--判据如何守这些差异)

---

## 1 · 一张表看懂四侧

本仓有**三个内核** + **一个客户端**，共**四侧**：

| 侧 | 是什么 | 配置位置 | 有生成链？ |
|:--|:--|:--|:--|
| **Surge** | 内核（商业客户端） | `surge/profiles/*.conf` | 只 `.min` |
| **Egern** | 内核 | `egern/profiles/*.yaml` | 只 `.min` |
| **mihomo** | 内核（Clash.Meta） | `clash/profiles/*.yaml` ← `clash/override/*.js` | ✅ **是** |
| **Stash** | **客户端**（Clash 系，内核是 Clash Premium） | `stash/override/*.stoverride` | ❌ 手工派生 |

### 核心对照

| 维度 | Surge | Egern | mihomo | Stash |
|:--|:--|:--|:--|:--|
| 地区组类型 | `smart` | `smart` | `url-test` | `url-test` |
| 地区组筛选 | `policy-regex-filter` | `policy_regex_filter` | `filter` + `exclude-filter` | `filter`（合并排除词） |
| 订阅来源 | `external` 组 | `external` 组 | `proxy-providers` | 订阅本身（`include-all`） |
| 倍率分档 | `policy-priority`（权重） | `priorities`（权重） | **静态模板有三档** | **有三档**（同静态模板） |
| 组数（分流版） | 23 | 23 | **25** | **25** |
| 规则数（分流版） | 26 | 26 | **27** | **27** |
| DNS 查询路径 | 显式关「跟随出站」 | — | `respect-rules: true`（**走代理**） | **默认直接出站** |
| 直连域名解析器 | —（`forward` 分流） | `forward` → `Domestic-DNS` | `direct-nameserver` | **主 `nameserver`**（无专用键） |
| IPv6 关闭 | 两处（`ipv6`+`ipv6-vif`） | 一处 | 两处（顶层+`dns.ipv6`） | **不写**（官方自动选择） |

⚠️ 差异的**完整逐键对照**见 [`dns.md`](./dns.md) §7（DNS 段四侧）与
各侧主文档；本表只收「最容易照抄错的」。

---

## 2 · 三条铁律

### ① 看起来不一致 ≠ 漂移 —— **先查这里再动手**

本仓专门有一道判据 `check_four_way_sync.py` 对拍四侧意图，但它只守**结构**
（规则序列 / 组 / 规则集键）。它**刻意放行**的差异都登记在该文件顶部的**豁免表**里：

| 豁免项 | 为什么刻意 |
|:--|:--|
| `Airport` 组只在 Surge/Egern | 那是它们的**订阅槽位组**；Clash 系用 `proxy-providers`，没有这个组 |
| `Auto`/`Low Mult.`/`High Mult.` 只在 Clash/Stash | **倍率三档**结构；Surge/Egern 用 `policy-priority` 权重表达同一件事 |
| `surge-ads` 等两条规则去向不同（`surge=REJECT` vs `egern=AD`） | Surge 内置拦截口径直接挂 REJECT；Egern 挂 `AD` 组（面板可切 DIRECT） |

⚠️ **不要为「让判据变绿」往豁免表里塞条目** —— 它是「刻意差异的登记处」，
不是「红线的逃生口」。新增豁免必须写清**为什么刻意**。

### ② 不要「对齐」各侧 —— 机制不同，对齐会改坏

典型：mihomo 侧 `Smart` 的倍率三档**只存在于静态模板**，覆写脚本做不到
（脚本在订阅加载时执行一次，看不到 provider 节点名）⇒ `check_script_sync.py`
把它列为**已知差异**，打印提醒但**不判负**。**不要去"修"它。**

### ③ 「三内核」是内核计数，不含 Stash

见 §4。

---

## 3 · 差异清单（按机制归类）

### 3.1 倍率分档：**权重 vs 三档**（同一意图的两种实现）

| 侧 | 实现 | 为什么 |
|:--|:--|:--|
| Surge / Egern | `smart` 组 + `policy-priority`（正则 : 系数，本仓 `0.15`） | `smart` 类型原生支持权重 |
| mihomo **静态模板** | `url-test` ×3（`Low Mult.` / `Auto` / `High Mult.`） | `url-test` 无权重，用**分档**表达 |
| mihomo **覆写脚本** | **做不到**（只对内联节点按倍率**排序**） | 生成期看不到 provider 节点名 |
| Stash | 同静态模板（三档） | `filter` 是**运行时**求值，能看到节点名 |

⇒ 「为什么脚本做不到」的完整推导见 [`profiles/clash.md`](./profiles/clash.md) §7.2。

### 3.2 节点入组：四个键名，三种机制

| 侧 | 键 | 说明 |
|:--|:--|:--|
| Surge | `include-other-group` | 引用**另一个组**（`Airport`） |
| Egern | `policies` | 成员里直接列 `Airport` |
| mihomo | `include-all` / `include-all-proxies` | 两键分工：后者只收内联 `proxies` |
| Stash | **只有 `include-all`** | = proxies + providers ⇒ mihomo 的两键分工在本侧不存在 |

### 3.3 排除节点：独立键 vs 合进 filter

| 侧 | 做法 |
|:--|:--|
| mihomo | `filter`（正向）+ **`exclude-filter`**（反向）两个独立键 |
| Stash | **无 `exclude-filter`** ⇒ 排除词写成 `(?!...)` 合进 `filter` |
| Surge / Egern | 正则内联在 `policy-regex-filter` / `policy_regex_filter` 里 |

⚠️ Stash 侧的**刻意副作用**：连「香港 官网」这类含地区词的信息节点也会被排除，
比 mihomo 更严格 —— 是改进而非漂移（信息节点本就不可用）。

### 3.4 DNS：三条独立的分岔（最危险的一类）

| 分岔 | 说明 |
|:--|:--|
| **查询是否走代理** | mihomo `respect-rules: true` **走代理**；Stash **默认直接出站** ⇒ 端点可达性要求相反 |
| 直连域名的解析器 | mihomo 有专用键 `direct-nameserver`；**Stash 没有** ⇒ 由主 `nameserver` 承担 |
| 按域换解析器 | mihomo 用 `rule-set:` 前缀；Stash 只支持精确域名/通配/`geosite:` |

🚨 **这三条曾导致真机事故**（Apple 域名全部 `resolve timeout`）：把 mihomo 的
`nameserver: [https://1.1.1.1/dns-query]` 照抄到 Stash ⇒ 大陆裸直连境外 DoH ⇒ 超时。
完整记录见 [`profiles/stash.md`](./profiles/stash.md) §4 与 [`dns.md`](./dns.md) §7.1。

### 3.5 交付形态：每侧各有几种

| 侧 | 形态 |
|:--|:--|
| Surge / Egern | 完整版 + `.min`（两份） |
| mihomo | 完整版 + `.min` + **覆写脚本**（三种；脚本与静态模板必须对拍一致） |
| Stash | **只有覆写脚本**（`.stoverride`）—— 无完整配置，也读不了 mihomo 的脚本或配置 |

---

## 4 · 谁是「三内核」

**本仓 92 处「三内核」都是内核计数**，指的是 Surge · Egern · mihomo。
**Stash 不是第四个内核** —— 它是 iOS / macOS 上的 Clash 系**客户端**。

⇒ 所以：

- 判据 `KERNS = ('surge', 'egern', 'clash')` —— 遍历内核的工具（如
  `routing_evolution.py` 的历史分析）**不应**把 Stash 算进去。
- 但**意图对拍**必须覆盖 Stash ⇒ `build_ir.py` 用两个常量区分：
  `KERNELS`（三个真内核）与 `SIDES = KERNELS + ('stash',)`（IR 覆盖的四侧）。
- 版本口径、Release 资产（12 件）都只算三内核 —— Stash 覆写**没有版本头注**。

---

## 5 · 判据如何守这些差异

| 判据 | 守什么 |
|:--|:--|
| `check_script_sync.py` | mihomo 脚本 ↔ 静态模板；**倍率三档是登记过的已知差异**，不判负 |
| `check_four_way_sync.py` | 四侧意图同构；**豁免表**登记所有刻意差异（见 §2①） |
| `check_priority_weight.py` | Surge/Egern 的 `smart` 权重口径（S1–S7） |
| `check_ad_caliber.py` | 两版 `AD` 组口径（分流版可放行 / 懒人版单成员） |
| `check_min_pair.py` | 各侧完整版 ↔ `.min`；**三内核版本号同号** |

⚠️ **共同纪律**：差异可以刻意，但不能「没人知道它刻意」——
每一条豁免都必须在此文件或判据的豁免表里写明理由。

# Stash · 覆写语义与加固

> **何时读**：改 `stash/override/*.stoverride`，或想弄明白「为什么 Stash 不能照抄 mihomo」时。
> 本文件是 Stash 侧的**主文档**；指路标在根 [`AGENTS.md`](../../../AGENTS.md) 的
> 「四侧指路标」一节（本仓**没有**嵌套 `AGENTS.md` —— 嵌套入口跨工具行为不一致）。

> 只想赶紧用起来 → 看 [`README`](../../../README.md) 的下载表（Stash 一行是**两份覆写文件**）。
>
> 目录
> [1 · 为什么 Stash 要单独一份](#1--为什么-stash-要单独一份) ·
> [2 · 键映射：mihomo ↔ Stash](#2--键映射mihomo--stash) ·
> [3 · 覆写的三条硬约束](#3--覆写的三条硬约束) ·
> [4 · DNS：端点必须大陆直连可达](#4--dns端点必须大陆直连可达) ·
> [5 · 倍率三档：Stash 强于脚本之处](#5--倍率三档stash-强于脚本之处) ·
> [6 · 与静态模板的关系](#6--与静态模板的关系) ·
> [7 · 判据清单](#7--判据清单)

---

## 1 · 为什么 Stash 要单独一份

**Stash 不是第四个内核。** 它是 iOS / macOS 上的 Clash 系**客户端**
（内核是 Clash Premium），与本仓的三个**内核**（Surge / Egern / mihomo）不是同一层概念。
本仓 92 处「三内核」都指内核计数，与「几个客户端能跑」是两回事。

### 1.1 mihomo 的**脚本**不能直接用

mihomo 的 JS 覆写（`clash/override/my_clash*.js`）由**客户端扩展**提供运行时
（Party / Verge Rev 等暴露 `main(config)` 直接改配置对象）。**Stash 做不到** ——
它的脚本体系（`script` + `script-providers`，见官方〈JavaScript 脚本〉）
是**改写 HTTP 请求/响应**的，与「改配置」无关。两者用途不同，覆写不通用。

### 1.2 mihomo 的**配置文件**也不能直接用 ⚠️

**这条更隐蔽，也更容易踩** —— 它不会报错，只会让网络悄悄坏掉：

把 `clash/profiles/*.yaml` 原样导入 Stash **能加载成功**，但 `respect-rules: true`
是 **mihomo 独有**，Stash 不认识 ⇒ **静默忽略** ⇒ `nameserver: [https://1.1.1.1/dns-query]`
变成**裸直连** ⇒ 大陆网络下解析超时。详见 §4。

⇒ 结论：Stash 侧必须用 `.stoverride` **重写**，不能指望「换个客户端读同一份配置」。

---

## 2 · 键映射：mihomo ↔ Stash

> 原理共用，**键名一律不能照抄**。以下只列 Stash 侧的差异；四侧完整对照见
> [`dns.md`](../dns.md) §7 的表。

| 语义 | mihomo | Stash | 备注 |
|:--|:--|:--|:--|
| DNS 查询路径 | `respect-rules: true` ⇒ 查询**走代理** | **默认「直接出站」，无对应键** | ⭐ 差异的根源，见 §4 |
| 直连域名解析器 | `direct-nameserver`（国内端点） | **无此键** ⇒ 由**主 `nameserver`** 承担 | ⭐ 这两个是同一个东西 |
| DNS 跟随规则 | `respect-rules: true` | 对应物叫 `follow-rule`，官方**不建议**开 | 开了会破坏 CDN 就近解析 |
| 节点入组 | `include-all` / `include-all-proxies`（两键） | **只有 `include-all`** | 见〈覆写的三条硬约束〉 |
| 排除节点 | `exclude-filter`（独立键） | **无此键** | 合进 `filter`，见〈覆写的三条硬约束〉 |
| 按域名换解析器 | `nameserver-policy`（`rule-set:` 前缀） | `nameserver-policy`（**只支持**精确域名 / 通配 / `geosite:`） | 无 `rule-set:` |
| 假 IP 模式 | `enhanced-mode: fake-ip` + `fake-ip-range` | **无此键** —— 默认就是 Fake IP | 不写 |
| DNS 层广告拦截 | `nameserver-policy: rcode://success` | **无 rcode 语法** ⇒ 改由**规则层 AD 组**承担 | 效果等价，发生在连接阶段 |
| IPv6 | 顶层 + `dns.ipv6` **两处**显式关 | 按官方〈IPv6 兼容性〉**自动**选择 | 不写该键 |
| 规则集格式 | `.mrs` 二进制（省内存） | 官方 `format` 只列 `yaml` / `text` | 本仓用 `text`/`yaml` 保守取值 |
| 策略组隐藏 | — | `hidden: true` 可用 | 未见官方正文，但社区广泛使用 |

---

## 3 · 覆写的三条硬约束

### 3.1 ⭐ 数组默认是「**前置插入**」，必须写 `#!replace`

官方〈覆写配置（Override）〉语法参考原文：

> 对于数组类型的同名键，覆写文件的数组会**插入到原数组前面**
> ……若添加注释 `#!replace`，则采用完全覆盖方式合并

⇒ 本目录 4 个顶层数组键**全部**要写 `#!replace`：`proxy-groups` /
`rule-providers` / `rules` / `dns`。

⚠️ **漏写的后果是静默的**：订阅自带的 proxy-groups / rules 会残留在前面，
而规则**自上而下首次命中即生效** ⇒ 你的全部改动被架空，但 Stash 照常启动、
不报任何错。这是本侧**结构上的**第一大坑。

判据：`check_stash_override.py` 判据 ②。

### 3.2 没有 `include-all-proxies`，只有 `include-all`

mihomo 里两个键分工不同：`include-all-proxies` 只收内联 `proxies`，
`include-all` 收 proxies **+** proxy-providers；脚本按订阅形态二选一。
**Stash 只有 `include-all`**（官方〈策略组〉：*"可以通过 include-all: true
引用所有的代理和远程代理集"*）⇒ 本仓统一用它。

**副作用是好的**：`include-all` 天然覆盖 provider 里的节点 ——
mihomo 侧「Smart 组看不到 provider 节点」那个问题，在 Stash 侧不存在。

### 3.3 没有 `exclude-filter` —— 排除词合进 `filter`

mihomo 的 `filter`（正向保留）与 `exclude-filter`（反向排除）是两个独立键。
Stash 只列了 `filter` ⇒ 排除词要写成 `(?!...)` **负向断言合进去**。

⚠️ **刻意的副作用**：mihomo 侧地区组不排除信息节点（`香港 官网` 会落进 `Hong Kong`），
Stash 侧因为把信息词并进了 `filter`，**会排除它** —— 比 mihomo 更严格。
这是改进而非漂移：信息节点本就不可用。

实测（38 个样本、.NET 引擎）：与「`filter` + `exclude-filter` 两键式」**逐样本等价**。

---

## 4 · DNS：端点必须大陆直连可达

### 4.1 官方原文（决定性）

〈内置 DNS 服务〉：

> 「默认情况下，Stash 发出的 DNS 查询均会**直接出站**，而不经由任何代理规则转发。」
> 「所有 DNS 请求将会**直接发送到服务器，不经过任何代理**。」
> （`default-nameserver` 注释）「除 `system` 外，服务器地址必须使用 IP。」

⇒ **Stash 里每一个 DNS 端点都是裸直连发出的**：`nameserver` /
`nameserver-policy` 的值 / `proxy-server-nameserver` 全部如此。

### 4.2 真机事故（2026-10-11）

**症状**：

```
connect error: resolve failed: 46-courier2.push.apple.com (A: resolve timeout…)
connect error: resolve failed: configuration-carry.ls.apple.com (A: resolve timeout…)
```

Apple 天气 / App Store / APNs 全部卡住。

**成因**：主 `nameserver` 从 mihomo 列照抄了 `https://1.1.1.1/dns-query` ——
大陆裸直连境外 DoH 必然超时，所有未被 policy 覆盖的域名全解析不了。
`push.apple.com` / `ls.apple.com` 在 [`apple_system.yaml`](../../../rules/apple_system.yaml)
里走 DIRECT，正落在这条路上。

**变体**：把 `clash/profiles/*.yaml` 原样导入 Stash 同样会坏（见 §1.2）。

### 4.3 正确写法

```yaml
dns: #!replace
  default-nameserver: [223.5.5.5, 119.29.29.29]   # 仅 IP 或 system
  nameserver:                                     # 大陆直连可达 + 加密
    - https://doh.18bit.cn/dns-query
    - https://doh.pub/dns-query
  nameserver-policy:
    'geosite:cn': https://223.5.5.5/dns-query
    'geosite:private': https://223.5.5.5/dns-query
  proxy-server-nameserver:
    - https://doh.18bit.cn/dns-query
    - https://dns.alidns.com/dns-query
```

**端点选型依据**（本仓实测，见 [`egern.md`](./egern.md) 的「实测铁律：国内解析器
不能用来解析境外域名」）：

| 端点 | 解 `www.google.com` 得到 | 能否当主 `nameserver` |
|:--|:--|:--|
| `doh.18bit.cn` | `216.239.38.120`（**真实**） | ✅ 可以 |
| `doh.pub` | 可用 | ✅ 可以 |
| `dns.alidns.com` | `31.13.92.37`（**GFW 污染**） | ❌ 只用于 `nameserver-policy` |
| `1.1.1.1` / `8.8.8.8` | 真实，但**大陆不可直连** | ❌ 见 §4.2 |

### 4.4 与 mihomo 的关系（**别照抄的根源**）

| | mihomo | Stash |
|:--|:--|:--|
| DNS 查询是否走代理 | ✅ `respect-rules: true` | ❌ **默认直接出站** |
| 因此主解析器可写 | 境外 DoH | **必须大陆可达** |
| 直连域名的解析 | `direct-nameserver` 专管 | **主 `nameserver`** 承担 |

**一句话**：mihomo 的 `direct-nameserver`（国内端点）在 Stash 侧**就是主 `nameserver`**；
而 mihomo 的主 `nameserver`（境外、靠 `respect-rules` 走代理）在 Stash 侧**没有对应物**。

---

## 5 · 倍率三档：Stash 强于脚本之处

`routing.stoverride` 的 `Smart` 用**倍率三档**（`Smart` → `Low Mult.` /
`Auto` / `High Mult.`），与静态模板 `clash/profiles/routing.yaml` **完全一致**。

**为什么脚本做不到、Stash 能做到**：

| | 求值时机 | 能看到节点名？ | 结果 |
|:--|:--|:--|:--|
| mihomo 覆写脚本 | **生成期**（订阅加载时执行一次） | ❌ 看不到 provider 里的节点 | 只能对**内联**节点按倍率**排序**；且 `rateOf` 只认 `0.x` 低倍率，抓不到高倍率 |
| 静态模板 / Stash | **运行时**（`filter` 每次筛节点时求值） | ✅ 能 | 按倍率**分档**，语义化 |

档位语义：

| 组 | 语义 |
|:--|:--|
| `Low Mult.` | 倍率 < 1（`0.01` / `0.1` / `0.5`…）· 最省钱，优先 |
| `Auto` | 正常倍率（节点名无倍率标记） |
| `High Mult.` | 倍率 > 1（`1.5倍` / `2倍` / `3.0x`…）· 最贵，兜底 |

⚠️ **对齐的是静态模板，不是脚本** —— 改 `Smart` 结构时以 `routing.yaml` 为准
（`25 组`，而非脚本的 `22 组`；差的 3 个就是这三个子组）。

**两条实现注意**：

- 三个子组都 `hidden: true`（不在面板上让人误选）。该键虽未见于官方〈策略组〉正文，
  但真实 Stash 配置中广泛使用（实测某份社区覆写有 30+ 处 `hidden: true`）。
- 高倍率必须**紧跟倍率单位**（`倍`/`倍率`/`x`/`X`/`*`），否则会把序号
  「香港 09」误判成高倍率。正则见该文件内的注释。

---

## 6 · 与静态模板的关系

```
clash/profiles/routing.yaml   ──（结构基准）──▶  stash/override/routing.stoverride
clash/profiles/lazy.yaml      ──（结构基准）──▶  stash/override/lazy.stoverride
```

**基准是「静态模板」，不是覆写脚本** —— 因为 Stash 的 `filter` 是运行时求值、
能看到节点名，能力上等同静态模板（§5）。

⚠️ 这是本仓**唯一没有生成器**的派生（Stash 读不了 mihomo 的 JS，见〈为什么 Stash 要单独一份〉）⇒
改了静态模板的组/规则/次序**必须手工同步**。

**好消息：漏改会被判据抓住** —— `check_four_way_sync.py` 对拍四侧
（surge · egern · clash · stash），其中 F1 断言 `clash` 与 `stash` 规则**逐字相同**、
F2 断言组**逐字段相同**、F3 断言 rule-provider 键序列相同。

⚠️ 但它对拍的是**结构**（规则序列 / 组 / 规则集键），**不是每一条注释**：
头注数字、散文说明改了没同步，判据看不出。**改结构靠判据，改陈述靠人。**

---

## 7 · 判据清单

```bash
python self-conf-skills/gates/check_stash_override.py  # 结构/引用/正则/规模（8 条注错判红）
python self-conf-skills/gates/check_stash_dns.py       # DNS 端点大陆可达（9 条判红）
python self-conf-skills/gates/check_four_way_sync.py   # 四侧意图对拍（clash ≡ stash）
```

| 判据 | 覆盖 |
|:--|:--|
| `check_stash_override.py` | YAML 语法 · `#!replace` · 正则可编译 · 组引用 · 规则集引用 · 出口策略 · 孤儿 · `behavior`/`format` · 规模 |
| `check_stash_dns.py` | 主 `nameserver` 存在且**大陆可达** · `nameserver-policy` 值同样可达 · `proxy-server-nameserver` 存在且可达 · 端点必须加密 · `default-nameserver` 只能 IP/`system` |
| `check_four_way_sync.py` | 四侧规则逐字相同 · 组逐项相同 · 规则集键序列相同 · 组名差集只含登记的刻意项 · 去向一致 |

**豁免表在 `check_four_way_sync.py` 顶部**（`Airport` 仅 Surge/Egern；
倍率三档仅 Clash/Stash；两条广告规则的去向差异）—— 新增豁免必须写清为什么刻意。

全部判据都已注册进 `verify_all.py`（与 CI 同源）。

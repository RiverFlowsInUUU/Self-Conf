# stash/ · Stash 覆写

**本目录把本仓的分流意图搬到 Stash —— 不是第四个内核。**
Stash 是 iOS / macOS 上的 Clash 系**客户端**（内核是 Clash Premium），
它**不能**运行 mihomo 的 JS 覆写脚本：两者机制完全不同（见下）。
所以本目录用 Stash 自己的 `.stoverride` 语法，重新表达**同一套分流意图**。

**结构基准是「静态模板」（能力强于脚本）**：Stash 的 `filter` 与静态模板一样是
**运行时**求值的，能看到全部节点名 ⇒ 能做到脚本做不到的**倍率分档**。
故 `routing.stoverride` 对齐 `clash/profiles/routing.yaml`（**25 组**），
而不是只排序、做不到分档的覆写脚本（22 组）。

根 [`AGENTS.md`](../AGENTS.md) 的规则仍然适用；这里只写 stash/ 特有的、agent 推不出来的东西。

---

## 唯一真源与派生关系

```
clash/profiles/routing.yaml      ──（结构基准）──▶  stash/override/routing.stoverride
clash/profiles/lazy.yaml         ──（结构基准）──▶  stash/override/lazy.stoverride
```

⚠️ **结构基准是「静态模板」，不是覆写脚本** —— 因为 Stash 的 `filter` 是运行时求值、
能看到节点名，能力上等同静态模板（详见文末「倍率三档」一节）。

⚠️ **规则与组名以静态模板为准，改了必须同步** —— 好消息是**漏改会被抓住**：
`check_four_way_sync.py` 对拍四侧（surge · egern · clash · stash）意图，
其中 F1 断言 `clash` 与 `stash` 的规则**逐字相同**、F2 断言组（name/type/proxies）
**逐项相同**、F3 断言 rule-provider 键序列相同 —— 改了 clash 不改 stash ⇒ **判红**。

⚠️ 但它对拍的是**结构**（规则序列 / 组 / 规则集键），**不是每一条注释**：
头注里的数字、散文说明改了但没同步，判据看不出。**改结构靠判据，改陈述靠人。**

---

## Stash 覆写的三条硬机制（**与 mihomo 完全不同，最容易写错**）

### ① 数组默认是「**前置插入**」，不是替换

官方〈覆写配置（Override）〉语法参考原文：

> 对于数组类型的同名键，覆写文件的数组会**插入到原数组前面**
> ……若添加注释 `#!replace`，则采用完全覆盖方式合并

⇒ **每个数组都必须写 `#!replace`**（本目录 4 个顶层键：`proxy-groups` /
`rule-providers` / `rules` / `dns`）。

⚠️ 漏写的后果是**静默的**：订阅自带的 proxy-groups / rules 会残留在前面，
而规则**自上而下首次命中即生效** ⇒ 你的全部改动被架空，但 Stash 照常启动、
不报任何错。这是本目录第一大坑。

`check_stash_override.py` 判据 ② 专守这一条。

### ② 没有 `include-all-proxies`，只有 `include-all`

mihomo 里 `include-all-proxies`（只收内联 `proxies`）与 `include-all`
（= proxies + providers）是两个键，脚本按订阅形态二选一。
**Stash 只有 `include-all`**（官方〈策略组〉：*"可以通过 include-all: true
引用所有的代理和远程代理集"*）⇒ 本目录统一用它。

### ③ 没有 `exclude-filter`

mihomo 的 `filter`（正向保留）与 `exclude-filter`（反向排除）是两个独立键。
Stash 只列了 `filter` ⇒ 排除词必须写成 `(?!...)` **合进** `filter`。

⚠️ 副作用（**刻意接受**）：mihomo 侧地区组不排除信息节点（`香港 官网` 会落进
`Hong Kong`），而 Stash 侧因为把信息词并进了 `filter`，**会排除它** ——
比 mihomo 更严格。这是改进而非漂移：信息节点本就不可用。
（对照实测见根 [`clash.md`](../self-conf-skills/references/profiles/clash.md) §6.4 与
[`gates.md`](../self-conf-skills/references/gates.md) 的相关实测记录。）

---

## 其它字段差异（照抄 mihomo 会报错）

| 项 | mihomo | Stash |
|:--|:--|:--|
| Fake IP 开关 | `enhanced-mode: fake-ip` + `fake-ip-range` | **没有**，默认就用 Fake IP |
| DNS 跟随规则 | `respect-rules: true` | 叫 `follow-rule`，且官方**不建议**开（会破坏 CDN 就近解析）⇒ 不写 |
| 按域名换解析器 | `nameserver-policy` 用 `rule-set:` 前缀 | 只支持精确域名 / 通配 / `geosite:` 集合，**没有 `rule-set:`** |
| DNS 层广告拦截 | `nameserver-policy: rcode://success` 双层 | **没有 rcode 语法** ⇒ 改由**规则层 AD 组**承担，效果等价（发生在连接阶段而非解析阶段） |
| IPv6 | 显式 `ipv6: false`（顶层 + dns 两处） | 按官方〈IPv6 兼容性〉**自动**选择 ⇒ 不写该键 |
| 规则集格式 | MRS 二进制（省内存） | 官方 `format` 只列 `yaml` / `text`；MRS 支持限 `domain`/`ipcidr`。本目录用 `text`/`yaml` 保守取值 |

---

## 本侧专属判据

```bash
# 本侧结构 / 引用 / 正则 / 规模（八条注错全部实测能判红）
python self-conf-skills/gates/check_stash_override.py
# 四侧意图对拍（含 F1–F3 断言 clash ≡ stash，漏改一处即判红）
python self-conf-skills/gates/check_four_way_sync.py
```

`check_stash_override.py` 覆盖：YAML 语法 · `#!replace` · 正则可编译 · 组引用 ·
规则集引用 · 出口策略 · 孤儿 · behavior·format · 规模。

`check_four_way_sync.py` 覆盖四侧（surge · egern · clash · stash）：规则逐字相同 ·
组逐项相同 · 规则集键序列相同 · 组名差集只含登记的刻意项 · 去向一致。
**豁免表在该文件顶部**（`Airport` 仅 Surge/Egern；倍率三档仅 Clash/Stash；
两条广告规则的去向差异）—— 新增豁免必须写清为什么刻意。

---

## 唯一一处 Stash **强于**脚本的地方：倍率三档

`routing.stoverride` 的 `Smart` 用的是**倍率三档**（`Smart` → `Low Mult.` /
`Auto` / `High Mult.`），与静态模板 `clash/profiles/routing.yaml` **完全一致**
（25 组，而非覆写脚本的 22 组 —— 差的 3 个就是这三个子组）。

**为什么脚本做不到、Stash 能做到**：

| | 求值时机 | 能看到节点名？ | 结果 |
|:--|:--|:--|:--|
| mihomo 覆写脚本 | **生成期**（订阅加载时执行一次） | ❌ 看不到 provider 里的节点 | 只能对**内联**节点按倍率**排序**，且 `rateOf` 只认 `0.x` 低倍率，抓不到高倍率 |
| 静态模板 / Stash | **运行时**（`filter` 每次筛节点时求值） | ✅ 能 | 按倍率**分档**，语义化 |

⇒ 所以本目录**照搬静态模板的三档**，而不是翻译脚本。这是「静态模板能做、脚本做不到」
那件事在 Stash 侧的等价实现 —— 与根 AGENTS.md 记的 `EXPECTED_DIFF`（脚本 vs 模板的
已知差异）互为镜像。

⚠️ **对齐的是静态模板，不是脚本** —— 改 `Smart` 结构时以 `routing.yaml` 为准。
`check_stash_override.py` 已按 25 组断言（不是 22）。

**写这三档时的两条注意**：

- 三个子组都 `hidden: true`（不在面板上让人误选）。该键虽未见于官方〈策略组〉正文，
  但真实 Stash 配置中广泛使用（实测某份社区覆写有 30+ 处 `hidden: true`），可用。
- 信息词（`剩余|流量|到期|…`）合进了 `filter` 的前置 `(?!...)`（Stash 无
  `exclude-filter`）。实测 38 个样本与「`filter` + `exclude-filter` 两键式」**逐样本等价**。

# stash/ · Stash 覆写

**本目录是 `clash/override/*.js` 的派生物 —— 不是第四个内核。**
Stash 是 iOS / macOS 上的 Clash 系**客户端**（内核是 Clash Premium），
它**不能**运行 mihomo 的 JS 覆写脚本：两者机制完全不同（见下）。
所以本目录用 Stash 自己的 `.stoverride` 语法，重新表达**同一套分流意图**。

根 [`AGENTS.md`](../AGENTS.md) 的规则仍然适用；这里只写 stash/ 特有的、agent 推不出来的东西。

---

## 唯一真源与派生关系

```
clash/override/my_clash.js       ─┐
clash/override/my_clash_lazy.js  ─┴──▶  stash/override/routing.stoverride
                                        stash/override/lazy.stoverride
```

⚠️ **改了 JS 的组/规则/次序，就必须同步改这里的 stoverride** ——
两者表达同一套意图。`check_stash_override.py` 守**结构自洽**（引用、正则、规模
与 mihomo 侧同数），但它**没法**替你判断「语义是否也同步了」：
新增一个组、改一条规则的落点，仍需人工对齐两边。

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
python self-conf-skills/gates/check_stash_override.py   # 结构 / 引用 / 正则 / 规模
```

八条注错全部实测能判红（YAML 语法 · `#!replace` · 正则可编译 · 组引用 ·
规则集引用 · 出口策略 · 孤儿 · behavior·format · 规模）。

---

## 一个刻意的能力差（**不要试图"补齐"**）

`my_clash.js` 的 `Smart` 组会按**倍率排序**成员（`rateOf` / `sortedByRate`）——
那是 JS 在运行时读节点名算出来的。**`.stoverride` 是静态文件，算不出节点名**，
故本目录的 `Smart` 成员顺序 = 订阅原顺序。

⇒ 若你依赖「低倍率优先」，两条路：
- 在 Stash 面板里手动排序；
- 或把 `Smart` 改成三档（Low / Auto / High）—— Stash 的 `filter` 支持前瞻断言，
  照搬 `clash/profiles/routing.yaml` 的三档正则即可，**比 JS 脚本还强**
  （静态模板能做而脚本做不到的事，Stash 同样能）。

这与根 AGENTS.md 的「**不要把三内核『对齐』**」是同一条纪律：看起来的不一致，
常是机制决定的。

# stash/ · Stash 覆写

**本目录把本仓的分流意图搬到 Stash —— 不是第四个内核。** Stash 是 iOS / macOS 上的
Clash 系**客户端**（内核 Clash Premium），mihomo 的**脚本与配置都不能直接用**：
JS 覆写跑不了；配置文件也会坏（`respect-rules` 等键被**静默忽略** ⇒ DNS 直连境外
端点 ⇒ 解析超时）。故用 Stash 自己的 `.stoverride` 语法重写同一套分流意图。

根 [`AGENTS.md`](../AGENTS.md) 的规则仍然适用；这里只写**结论与索引** ——
详情（逐键差异、事故记录、实测数据）在
[`references/profiles/stash.md`](../self-conf-skills/references/profiles/stash.md)。

---

## 你想改什么 → 改哪份 → 跑什么

| 你想改 | 改这个 | 然后 |
|:--|:--|:--|
| Stash 的组 / 规则 / DNS | `stash/override/{routing,lazy}.stoverride` | 跑下面三条判据 |
| 改完 clash 的静态模板 | 上面两份**要手工同步**（本仓唯一无生成器的派生） | `check_four_way_sync.py` 会抓漏改 |

⚠️ **改了 `clash/profiles/*.yaml` 的组/规则/次序，必须同步改这里** ——
`check_four_way_sync.py` 对拍四侧（surge · egern · clash · stash），
F1 断言 `clash` 与 `stash` 规则**逐字相同**、F2 断言组**逐字段相同**、
F3 断言 rule-provider 键序列相同 ⇒ 漏改一处即**判红**。

⚠️ 但它对拍的是**结构**（规则序列 / 组 / 规则集键），**不是每一条注释**：
头注数字、散文说明改了没同步，判据看不出。**改结构靠判据，改陈述靠人。**

---

## 三条硬约束（写错会**静默**失效）

| # | 约束 | 漏了会怎样 |
|:--|:--|:--|
| ① | 数组键**必须** `#!replace`（4 个：`proxy-groups`/`rule-providers`/`rules`/`dns`） | 覆写默认是**前置插入**，订阅自带的组/规则残留在前面 ⇒ 改动被架空，**不报错** |
| ② | 只有 `include-all`，**没有** `include-all-proxies` | 写了 mihomo 的键 ⇒ 该组无节点 |
| ③ | **没有** `exclude-filter` ⇒ 排除词写进 `filter` 的 `(?!...)` | 写了 mihomo 的键 ⇒ 排除失效，信息节点混进组 |

⚠️ ②③ 的后果是「键被忽略、配置照常加载」—— Stash 不会报错。
**报错好办，静默才难查**，所以本侧每个坑都配了判据。

---

## 🚨 DNS 端点必须大陆直连可达（真机事故过）

官方〈内置 DNS 服务〉：**「Stash 发出的 DNS 查询均会直接出站，不经任何代理规则转发。」**
⇒ 主 `nameserver` 写境外 DoH（`1.1.1.1`）在大陆**必然超时**。

**这也是「mihomo 配置文件不能直接给 Stash 用」的原因**：mihomo 的
`respect-rules: true` 让 DNS 走代理，所以那侧能写境外端点；**Stash 不认识这个键**，
静默忽略 ⇒ 1.1.1.1 变裸直连。症状是 Apple 天气 / 商店打不开，日志刷
`resolve failed: …push.apple.com (A: resolve timeout…)`。

⭐ **键映射**：mihomo 的 `direct-nameserver`（国内端点）**＝ Stash 的主 `nameserver`**。

正确写法用 `doh.18bit.cn` / `doh.pub`。选型依据（实测：`doh.18bit.cn` 解境外域名
得**真实地址**、`dns.alidns.com` 得**污染 IP**）与完整事故记录 → [`stash.md` §4](../self-conf-skills/references/profiles/stash.md)。

---

## 本侧专属判据

```bash
python self-conf-skills/gates/check_stash_override.py  # 结构/引用/正则/规模（8 条注错判红）
python self-conf-skills/gates/check_stash_dns.py       # DNS 端点大陆可达（9 条判红）
python self-conf-skills/gates/check_four_way_sync.py   # 四侧意图对拍（clash ≡ stash）
```

判据覆盖范围与豁免表 → [`stash.md` §7](../self-conf-skills/references/profiles/stash.md)。

---

## 一个反直觉点：Stash **强于**脚本

`routing.stoverride` 的 `Smart` 用**倍率三档**（`Low Mult.` / `Auto` / `High Mult.`），
与静态模板一致（**25 组**，而非脚本的 22 组）—— 因为 Stash 的 `filter` 是**运行时**
求值、能看到节点名，而 JS 脚本在生成期看不到 provider 节点。

⇒ ⚠️ **对齐的是静态模板，不是脚本**。原因与实现细节 →
[`stash.md` §5](../self-conf-skills/references/profiles/stash.md)。

# self-conf · Agent 指南（唯一入口）

Surge / Egern / mihomo（Clash Meta）**三内核代理配置模板** + **Stash 覆写**。
人类请看 [`README.md`](./README.md)；公开仓安全纪律见 [`SECURITY.md`](./SECURITY.md)。

> 本文件是 AI 操作手册的**唯一真源** —— **任何 AI 工具都读这一份**。
> ⚠️ **本仓不用嵌套 `AGENTS.md`、不建工具专属入口**（`CLAUDE.md` / `.cursorrules` /
> `GEMINI.md` / `copilot-instructions.md`）。原因：嵌套入口**跨工具行为不一致**
> （Codex/Cursor 加载，**Claude Code 不加载**，issue #98796）⇒ 靠它传「就近警告」不可靠；
> 工具专属入口则会被**优先于** `AGENTS.md` 读取，从而屏蔽真源。
> ⇒ 结构是**一个入口 + 指路标**（见下）。谁想加第二入口：先读 `references/gates.md`。

---

## 命令

```bash
python self-conf-skills/gates/verify_all.py          # 门禁唯一入口（与 CI 同源）。绿了才算改完
python self-conf-skills/gates/verify_all.py -v       # 带详细输出
python self-conf-skills/gates/verify_all.py --index  # 列闸门清单（现抓，勿手抄）

python self-conf-skills/run/make_min.py --apply              # 改完完整版后同步 .min
python self-conf-skills/run/clash/build_profiles.py          # 改完 my_clash*.js 后重生成 mihomo profile
python self-conf-skills/run/clash/build_rules.py             # 改完 rules/*.list 后重生成 .yaml
python self-conf-skills/run/build_ir.py                      # 改完任一侧配置后重生成路由意图 IR
python self-conf-skills/run/routing_evolution.py             # 分流意图 git 演变：按需跑，输出机读 JSON
python self-conf-skills/run/repo_state.py                    # 一屏现状：版本 / Release / CI
```

退出码：**0 = 全过 · 1 = 判负 · 2 = 环境不达标（先修环境，别读判据）· 3 = 未验证**。
⚠️ **3 不是绿**（显示 ⚠️，不计入 passed）。**没读到远端真值 = 3；读到了但不过 = 1。**

---

## 边界

**✅ 总是**：改完跑 `verify_all.py`（"我改对了"不算做完，**门禁绿了才算**）；改完整版后同步
`.min`（两份只差注释）；每条配置键的权威解释是**它自己在 profile 里的注释**（写满了理由）。

**⚠️ 先问**：改判据 / 加闸门（先说「原判据错在哪」，再读 `references/gates.md` 自查清单）；
结构性调整（**先补判据**，不靠"再跑一遍"）。

**🚫 从不**：手工编辑生成物（`rules/*.yaml` · `clash/profiles/*.yaml` · `*.min.*` ·
`rules/AI.list` · `references/intent.json`）；为「让门禁变绿」而改判据；
把文档里写的数字当权威（一律现抓）；**把各侧「对齐」**（差异常是刻意的，见下）。

---

## 改动去哪

| 改什么 | 改哪个文件 | ⚠️ 易错 |
|:--|:--|:--|
| Surge 配置 | `surge/profiles/*.conf` | **不是**生成物，直接改 |
| Egern 配置 | `egern/profiles/*.yaml` | **不是**生成物，直接改 |
| mihomo 配置 | `clash/override/my_clash*.js` | ⚠️ **是**生成物 ⇒ 改 JS 再 build |
| **Stash 覆写** | `stash/override/*.stoverride` | ⚠️ 基准是**静态模板**；数组**必须** `#!replace` |
| 远程规则集内容 | `rules/*.list` | ⚠️ `.yaml` 是生成的 |
| **版本号** | ⚠️ **12 处头注**（三内核 × 两产品线 × 完整版/`.min`） | clash 的 4 处要**手改 profile**（头注是保留而非生成的） |

**生成链 / 派生关系**（改左边，跑右边重生成或**手工同步**）：

```
三内核 profiles/*  ──make_min.py──▶ *.min.*（六份）      clash/override/*.js ──build_profiles.py──▶ clash/profiles/*
rules/*.list      ──build_rules.py──▶ rules/*.yaml      ai_sources/*        ──ai_domains_build.py──▶ rules/AI.list
clash/profiles/routing.yaml ──（手工派生）──▶ stash/override/*.stoverride
任一侧现役 profiles（只读） ──build_ir.py──▶ references/intent.json
```

⚠️ **`stash/` 是唯一「没有生成器」的派生**（Stash 跑不了 mihomo 的 JS）⇒ 改了静态模板的
组/规则/次序**必须手工同步**它。**漏改判据会抓**（`check_four_way_sync.py` 对拍四侧），
但**注释与散文不在判据面上 —— 靠人**。完整动线 → [`ops.md`](./self-conf-skills/references/ops.md) §6.2。

---

## 四侧指路标（**本文件不写详情，只指路**）

四侧各有**详情主文档**与**本侧判据**；本文件不再重复它们的内容。

| 侧 | 详情主文档（逐键语义 / 事故 / 实测） | 改哪份 | 本侧判据（改完自查） |
|:--|:--|:--|:--|
| **Surge** | [`references/profiles/surge.md`](./self-conf-skills/references/profiles/surge.md) | `surge/profiles/*.conf` | `gates/surge/check_surge_dns.py` + 全套 |
| **Egern** | [`references/profiles/egern.md`](./self-conf-skills/references/profiles/egern.md) | `egern/profiles/*.yaml` | `gates/egern/check_egern_dns.py` + 全套 |
| **mihomo** | [`references/profiles/clash.md`](./self-conf-skills/references/profiles/clash.md) | `clash/override/my_clash*.js` | `gates/clash/{check_structure,check_script_sync,check_version_header,check_clash_dns}.py` |
| **Stash** | [`references/profiles/stash.md`](./self-conf-skills/references/profiles/stash.md) | `stash/override/*.stoverride` | `gates/{check_stash_override,check_stash_dns,check_four_way_sync}.py` |

**两条跨侧的高频坑**（详情见各自主文档）：

- **mihomo 侧**：⚠️ **直接改 `clash/profiles/*.yaml` 会在下次生成时被覆盖**（本侧最高频错误）；
  改了组数/规则数，**脚本头注里的数字要一起改**（`check_header_numbers.py` 判）。
- **Stash 侧**：⚠️ **mihomo 的脚本与配置都不能直接用**（JS 跑不了；配置文件会让 DNS 坏掉）；
  三条硬约束（数组必须 `#!replace` / 无 `include-all-proxies` / 无 `exclude-filter`）
  写错都**静默失效**。见 [`stash.md`](./self-conf-skills/references/profiles/stash.md) §3–§4。

---

## 内核差异指路标

**要把某一侧的做法搬到另一侧时，先读
[`references/DIFFERENCES.md`](./self-conf-skills/references/DIFFERENCES.md)** ——
四侧机制差异的汇总入口（谁用 `smart` 谁用 `url-test`、为什么有的侧做不到倍率分档、
四条的 DNS 分岔、谁是「三内核」）。

⚠️ **看起来不一致 ≠ 漂移**：本仓大量差异是**刻意的**，机制决定。
`check_four_way_sync.py` 顶部的**豁免表**登记了所有刻意差异（`Airport` 组、倍率三档、
两条广告规则去向）—— **不要为让判据变绿往豁免表塞条目**，它是登记处不是逃生口。

---

## 文档怎么读（**不要整篇读**）

`references/` **11 篇 · 900+ 个节**（最大一节也只 ~5 KB）⇒ 按需 grep 定位到节。

| 要去哪 | 是什么 |
|:--|:--|
| [`references/INDEX.md`](./self-conf-skills/references/INDEX.md) | **路由表**：想问什么→去哪份→用哪个词；我要做 X→读什么跑什么 |
| [`references/DIFFERENCES.md`](./self-conf-skills/references/DIFFERENCES.md) | **四侧差异汇总**（对齐前必读，见上节） |
| [`self-conf-skills/SKILL.md`](./self-conf-skills/SKILL.md) | **Agent Skills 入口**：改动完整流程 / 常见任务步骤 |
| [`gates/probes/README.md`](./self-conf-skills/gates/probes/README.md) | **探针题库**：丢给新 AI 测「文档对读者够不够用」 |

> 📌 **可达性有判据守着**（`check_ai_entry.py` ⑥）：每篇 `.md` 必须能**从本文件沿链接到达**
> —— 新建文档没挂进路由表 ⇒ 判负。（`check_links.py` 只管正向「链接指向的文件在不在」，
> 管不了反向「文件有没人指」；两者互补。）

---

## 两条铁律

1. **🚫 永不浅克隆（`--depth=1` / `--shallow-since`）—— 必须完整克隆。这是原则，不是建议。**
   浅克隆下 `git log` 的日期全退化成 clone 当天，而本仓多处依赖**提交日期**
   ⇒ `check_version_cadence.py` **假红**、`check_releases.py` R6b **静默假绿**。
   已有浅克隆就地补全：`git fetch --unshallow`。（CI 固定 `fetch-depth: 0`，不受影响。）
2. **改动涉及路径 / 编码 / 联网 / git 历史时，等 CI 结果，别只看本地。**
   同理：闸门「跑了没红」时，**先怀疑自己的注错没落在判据扫描面上**，再怀疑判据失灵。

> 完整推导、实测记录与失败形态 → [`gates.md`](./self-conf-skills/references/gates.md) 的「两件事」一节。

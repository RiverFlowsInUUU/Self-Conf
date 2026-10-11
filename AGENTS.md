# self-conf · Agent 指南

Surge / Egern / mihomo（Clash Meta）**三内核代理配置模板**。
人类请看 [`README.md`](./README.md)；公开仓安全纪律见 [`SECURITY.md`](./SECURITY.md)。

> 本文件是 AI 操作手册的**唯一真源**——**任何 AI 工具都读这一份**。
> （`AGENTS.md` 是跨工具开放格式：Codex / Cursor / Copilot / Claude Code / Amp /
> Jules / Windsurf / Zed 等 20+ 工具原生支持。**不要**再建 `CLAUDE.md` /
> `.cursorrules` / `copilot-instructions.md` / `GEMINI.md` —— 工具专属入口会被
> **优先于** `AGENTS.md` 读取（Claude 有 `CLAUDE.md` 时只读它；Gemini CLI 默认只读
> `GEMINI.md`），那是第二份要同步的东西，且会屏蔽真源。本仓只留这一个入口。）
> ⚠️ `clash/` 有独立的生成链，**在那里工作时先读就近的 [`clash/AGENTS.md`](./clash/AGENTS.md)**；
> 改 `clash/profiles/*.yaml` 的组/规则后**必须同步** [`stash/override/*.stoverride`](./stash/AGENTS.md)。

---

## 命令

```bash
python self-conf-skills/gates/verify_all.py          # 门禁唯一入口（与 CI 同源）。绿了才算改完
python self-conf-skills/gates/verify_all.py -v       # 带详细输出
python self-conf-skills/gates/verify_all.py --index  # 列闸门清单（现抓，勿手抄）

python self-conf-skills/run/make_min.py --apply              # 改完完整版后同步 .min
python self-conf-skills/run/clash/build_profiles.py          # 改完 my_clash*.js 后重生成 mihomo profile
python self-conf-skills/run/clash/build_rules.py             # 改完 rules/*.list 后重生成 .yaml
python self-conf-skills/run/build_ir.py                      # 改完三内核任一配置后重生成路由意图 IR（intent.json）
python self-conf-skills/run/routing_evolution.py             # 分流意图 git 演变：按需跑，输出机读 JSON（谁加了/删了/改了去向）
python self-conf-skills/run/repo_state.py                    # 一屏现状：版本 / Release / CI
```

退出码：**0 = 全过 · 1 = 判负 · 2 = 环境不达标（先修环境，别读判据）· 3 = 未验证**。
⚠️ **3 不是绿**（显示 ⚠️，不计入 passed）。**没读到远端真值 = 3；读到了但不过 = 1。**

---

## 边界

**✅ 总是**
- 改完跑 `verify_all.py` —— **"我改对了"不算做完，门禁绿了才算**
- 改完整版后同步 `.min`（两份只差注释，内容必须逐字相同）
- 每条配置键的权威解释是**它自己在 profile 里的注释**（写满了理由）；改键前先读它

**⚠️ 先问**
- 改判据 / 加闸门（先说明「原判据错在哪」，再读 `self-conf-skills/references/gates.md` 的自查清单）
- 结构性调整（先补判据，不靠"再跑一遍"）

**🚫 从不**
- 手工编辑生成物：`rules/*.yaml`（改 `rules/*.list`）、
  `clash/profiles/*.yaml`（改 `clash/override/my_clash*.js`）、`*.min.*`（跑 `make_min.py --apply`）、
  **`rules/AI.list`**（改 `self-conf-skills/run/ai_sources/` 再跑 `ai_domains_build.py`）、
  **`self-conf-skills/references/intent.json`**（改三内核配置后跑 `build_ir.py`）
- 为了「让门禁变绿」而改判据
- 把文档里写的数字当权威（组数/条数一律现抓）
- **把三内核「对齐」** —— 机制不同，看起来的不一致常是刻意的

---

## 改动去哪（**推不出来的部分**）

| 改什么 | 改哪个文件 | ⚠️ 易错 |
|:--|:--|:--|
| Surge 配置 | `surge/profiles/*.conf` | **不是**生成物，直接改 |
| Egern 配置 | `egern/profiles/*.yaml` | **不是**生成物，直接改 |
| mihomo 配置 | `clash/override/my_clash*.js` | ⚠️ **是**生成物 ⇒ 改 JS 再 build |
| **Stash 覆写** | `stash/override/*.stoverride` | ⚠️ 基准是**静态模板** `clash/profiles/routing.yaml`；数组**必须** `#!replace` |
| 远程规则集内容 | `rules/*.list` | ⚠️ `.yaml` 是生成的 |
| **版本号** | ⚠️ **12 处头注**（见下） | 不是 6 处 —— 每份文件都有自己的头注 |

**生成链 / 派生关系**（改左边，跑右边重生成或**手工同步**）：

```
三内核 profiles/*.yaml|conf        ──make_min.py──▶        *.min.*（六份，clash 侧 2026-10-09 起）
clash/override/my_clash*.js        ──build_profiles.py──▶  clash/profiles/*.yaml + *.min.yaml
clash/profiles/routing.yaml         ──（手工派生）──▶        stash/override/*.stoverride
rules/*.list                       ──build_rules.py──▶     rules/*.yaml
self-conf-skills/run/ai_sources/*  ──ai_domains_build.py──▶ rules/AI.list
三内核现役 profiles（只读）          ──build_ir.py──▶        references/intent.json（统一意图 IR，给 AI 读）
```

⚠️ **`stash/` 是唯一「没有生成器」的派生**（Stash 不能跑 mihomo 的 JS）⇒ 改了**静态模板**的
组/规则/次序就**必须手工同步**它；**漏改判据会抓**（`check_four_way_sync.py` 对拍四侧），
但**注释与散文不在判据面上 —— 靠人**。机制与坑见 [`stash/AGENTS.md`](./stash/AGENTS.md)。

⚠️ **`rules/AI.list` 也是生成物**（由 `ai_sources/` 里 10 个来源合并而成）——
改它要改 `self-conf-skills/run/ai_sources/` 下的源文件，再跑
`python self-conf-skills/run/ai_domains_build.py`。
（它的头部注释写明了生成脚本；`rules/*.yaml` 同理。）

⚠️ **版本头注是「生成物」的例外**：`clash/profiles/*.yaml` 虽由脚本生成，
但头注 `#! version=` **是脚本保留而非生成的** ⇒ **升版时要手改 clash 的 profile**
（只改 JS 不会改版本号）。升版共 **12 处**头注：
三内核 × 两产品线 × （完整版 + `.min`）。
Surge / Egern / clash 改完整版后跑 `make_min.py --apply` 都会同步对应的 `.min`（2026-10-09 起六份）；
clash 的 `.min` 跑 `build_profiles.py` 时也会保留头注、重写正文。

**三内核机制差异**（看起来不一致 ≠ 漂移）：地区组 Surge/Egern 用 `smart`、mihomo 用
`url-test`；订阅源前者是 external 组、后者是 `proxy-provider`；倍率分档 mihomo 的
**脚本做不到**（生成期看不到节点名）。`check_script_sync.py` 把这类列为**已知差异**，
打印提醒但不判负 —— **不要去"修"它**。

---

## 文档怎么读（**不要整篇读**）

`self-conf-skills/references/` 共 **10 篇 · 900+ 个节**（最大一节也只 ~5 KB）⇒ 按需 grep 定位到节。
**「想问什么 → 去哪份 → 用哪个词」「我要做 X → 读什么跑什么」两张路由表在
[`references/INDEX.md`](./self-conf-skills/references/INDEX.md)** —— 本文件只留指针，
不再塞表（入口文件的 150 行额度留给全局纪律）。

---

## 两件事：不得浅克隆 · 本地全绿 ≠ 线上能跑

**🚫 永不浅克隆（`--depth=1` / `--shallow-since`）—— 必须完整克隆。这是原则，
不是建议。** 浅克隆下 `git log` 的日期**全退化成 clone 当天**，而本仓多处依赖
**提交日期**（发布 tag = HEAD 提交日；一天一版按提交日期分组）⇒ 两条判据会错，
方向相反，且**都不报错**：

| 判据 | 浅克隆下的表现 | 实测 |
|:--|:--|:--|
| `check_version_cadence.py`（一天一版） | 根提交被当成「当日升号」⇒ **假红** | 2026-10-10：本地报「同日升 2 个号」，完整历史全绿（真实升号 10-08 → 10-10，**不同天**） |
| `check_releases.py` R6b（防漏发） | tag 指向的 commit 不存在 ⇒ `git diff` 抛错，异常被吞 ⇒ **静默判绿** | 同一提交**本地绿、CI 红**（CI 用 `fetch-depth: 0`） |

已有浅克隆就地补全，别重克隆：`git fetch --unshallow`。
（CI 固定 `fetch-depth: 0`，不受此项影响 —— 本条管**本地与人工审查**。）

改动涉及**路径 / 编码 / 联网 / git 历史**时，**等 CI 结果**，别只看本地 —— 这类历史上
都栽过（Linux 上路径探测算错目录；中文 Windows 管道 GBK 崩成退出码 1，而 1 恰是判负码）。

同理：闸门「跑了没红」时，**先怀疑自己的注错没落在判据的扫描面上**，再怀疑判据失灵。

# self-conf · Agent 指南（唯一入口）

Surge / Egern / mihomo 三内核配置模板 + Stash 覆写。
人类看 [`README.md`](./README.md)；安全纪律见 [`SECURITY.md`](./SECURITY.md)。

> **唯一真源**：任何 AI 只读这一份。不建嵌套 `AGENTS.md`、不建 `CLAUDE.md` /
> `.cursorrules` / `GEMINI.md` 等工具专属入口（嵌套加载跨工具不一致，工具专属会屏蔽真源）。
> 理由与分层结构 → [`references/gates.md`](./self-conf-skills/references/gates.md)。

## 命令

```bash
python self-conf-skills/gates/verify_all.py   # 门禁唯一入口（与 CI 同源）。绿了才算改完
python self-conf-skills/run/repo_state.py     # 一屏现状：版本 / Release / CI
```

退出码：0 全过 · 1 判负 · 2 环境不达标 · 3 未验证（**3 不是绿**）。
全部命令 → [`ops.md`](./self-conf-skills/references/ops.md) §6.2。

## 指路标 · 改什么去哪

| 改什么 | 改哪份 | 详情（按需读，勿整篇） |
|:--|:--|:--|
| Surge | `surge/profiles/*.conf` | [`profiles/surge.md`](./self-conf-skills/references/profiles/surge.md) |
| Egern | `egern/profiles/*.yaml` | [`profiles/egern.md`](./self-conf-skills/references/profiles/egern.md) |
| mihomo | `clash/override/clash-*.js` ⚠️ 生成物源头 | [`profiles/clash.md`](./self-conf-skills/references/profiles/clash.md) |
| Stash | `stash/override/stash-*.stoverride` | [`profiles/stash.md`](./self-conf-skills/references/profiles/stash.md) |
| 规则集 | `rules/*.list`（`.yaml` 是生成的） | [`rulesets.md`](./self-conf-skills/references/rulesets.md) |
| 四侧对齐 / 差异 | **先读差异再动手** | [`DIFFERENCES.md`](./self-conf-skills/references/DIFFERENCES.md) |
| 操作动线 / 发版 | — | [`ops.md`](./self-conf-skills/references/ops.md)（§6.0 影响面清单） |
| 判据与闸门 | — | [`gates.md`](./self-conf-skills/references/gates.md) |
| 想问什么→读哪份 | — | [`INDEX.md`](./self-conf-skills/references/INDEX.md)（路由表） |

## 边界

**✅ 总是**：门禁绿了才算改完；改完整版同步 `.min`；键的权威解释是 profile 里的注释；
提交前先过 [`ops.md`](./self-conf-skills/references/ops.md) §6.0 影响面清单（自检三问）。
**⚠️ 先问**：改判据、加闸门、结构性调整（先说原判据错在哪，先补判据）。
**🚫 从不**：手工编辑生成物（`*.min.*` · `clash/profiles/*.yaml` · `rules/*.yaml` ·
`rules/AI.list` · `references/intent.json`）；为门禁变绿而改判据；文档数字当权威（一律现抓）；
**把各侧「对齐」**—— 差异多是刻意的（豁免表在 `check_four_way_sync.py` 顶部，不是逃生口）。

## 两条铁律

1. **🚫 永不浅克隆** —— `git log` 日期会全退化，判据假红假绿。补救：`git fetch --unshallow`。
2. **涉路径 / 编码 / 联网 / git 历史，等 CI 再说**；闸门没红先怀疑注错没落进扫描面。

## Agent Skills

任务级操作步骤 → [`self-conf-skills/SKILL.md`](./self-conf-skills/SKILL.md)；
探针题库 → [`gates/probes/README.md`](./self-conf-skills/gates/probes/README.md)。

> 每篇 `.md` 都必须能从本文件沿链接到达（⑥ 判据）；生成链与派生关系见
> [`INDEX.md`](./self-conf-skills/references/INDEX.md) 与 [`ops.md`](./self-conf-skills/references/ops.md) §6.2。

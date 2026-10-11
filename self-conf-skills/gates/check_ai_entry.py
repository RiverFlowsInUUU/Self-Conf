#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 入口唯一性 —— 保证「换任何 AI 都能读同一份文档」。

⚠️ 2026-10-08 修正（此前做错了）：我原以为「每个 AI 工具的约定文件名都要有一份」，
于是造了 CLAUDE.md / GEMINI.md / .cursorrules / copilot-instructions.md 四份
—— **但它们是同一份内容的副本，只有标题行不同**。那是重复，不是兼容。

⚠️ 2026-10-08 二次修正：曾把 GEMINI.md 当「唯一例外」保留（理由：Gemini CLI 默认
只读它），判定「纯指针即可」。**但保留一个工具专属入口本身就是问题** ——
它会被该工具**优先于** AGENTS.md 读取，于是真源被绕过，且多出一份要同步的东西。
事实核查（各家官方文档 / 源码）：
  · Claude Code：**能直接读 AGENTS.md**（"without adding a CLAUDE.md, an import,
    or a setting"）。且官方明确警告：**仓库里有 CLAUDE.md 时，Claude 只读 CLAUDE.md、
    不读 AGENTS.md**。
  · Cursor：官方文档「AGENTS.md … as an alternative to `.cursor/rules`」，且支持嵌套。
  · GitHub Copilot：「Copilot coding agent now supports AGENTS.md」（2025-08-28）。
  · Gemini CLI：源码 `DEFAULT_CONTEXT_FILENAME = 'GEMINI.md'`，AGENTS.md 不在默认
    `context.fileName` 列表里（issue #28227 仍 open，PR #24913 closed without merge）。
    ⇒ 确实读不到 AGENTS.md，**但那不是「要给它单独建一份」的理由** ——
    正确处置是**不建**：让读不到的工具读不到，而不是为它维护第二份入口。
    想用 Gemini CLI 的人，自己在 `~/.gemini/settings.json` 把 `AGENTS.md` 加进
    `context.fileName` 即可 —— 这是**用户侧的一行配置**，不该由本仓建文件来适配。

⇒ 正确做法：**AGENTS.md 是唯一入口，不做任何工具专属兼容。**
   任何工具专属入口文件（含指针）一律**不应存在** —— 它们要么屏蔽真源，
   要么制造第二份要同步的东西。

本判据守：
  ① AGENTS.md 存在、在根、且**内容充实**（不是空壳）
  ② **不应存在**工具专属入口文件（会被优先读取、从而屏蔽真源）
  ③ 体积与六域纪律（研究：过长只增成本；缺域是第二常见失败模式）
  ④ **不应存在嵌套 AGENTS.md** —— 嵌套入口跨工具行为不一致（Claude Code 不加载，
     issue #98796）⇒ 正确结构是「唯一入口 + 指路标」（2026-10-11 反转，原为「必须存在」）
  ⑤ **入口必须真的指路** —— 必须指向 `references/INDEX.md`（路由表）、
     `references/DIFFERENCES.md`（差异汇总）、`references/profiles/<侧>.md`（各侧详情）
     ⇒ 防它退化成一个「只有纪律、没有去处」的空壳

⚠️ 条目 ④ 与 ⑤ 是一对：**拆掉嵌套入口**的同时，必须保证**唯一入口真的能指到详情**。
   只做 ④ 会让人找不到东西；只做 ⑤ 而不删嵌套，会留下跨工具不一致的第二入口。

退出码：0 = 通过 · 1 = 违规 · 2 = 环境不达标
"""
import io
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

MAIN = "AGENTS.md"
# ⚠️ 2026-10-11：**嵌套 AGENTS.md 全部取消，本表应为空**（曾登记 clash/ 与 stash/ 两份）。
#    为什么取消：**嵌套入口跨工具行为不一致** ——
#      · Codex / Cursor / DSH 会按目录自动加载；
#      · **Claude Code 不加载**（open issue anthropics/claude-code#98796）。
#    ⇒ 用 Claude Code 的 AI 在子目录里工作会**看不到那里的警告**，正是本仓最恨的
#      「静默失效」。而本仓恰恰靠「就近警告」防两件事：mihomo 侧「别直接改
#      profiles/*.yaml」、Stash 侧「数组必须 #!replace」——两者写错都不报错。
#    ⇒ 正确结构：**唯一入口（本文件）+ 指路标**（四侧各指向 references/profiles/<侧>.md，
#      差异指向 references/DIFFERENCES.md）。见根 AGENTS.md 的「四侧指路标」一节。
#    ⚠️ 若将来有人想再加嵌套入口，先读 `references/gates.md` 关于本判据的那一节。
NESTED = []
# 若嵌套入口被重新引入，会同时被这条断言拦下（见 main() 的 NESTED_BANNED 检查）。
NESTED_BANNED = ["clash/AGENTS.md", "stash/AGENTS.md", "surge/AGENTS.md", "egern/AGENTS.md",
                 "rules/AGENTS.md", "icons/AGENTS.md", "releases/AGENTS.md"]

# ⚠️ 这些文件名会被各自工具**优先于 AGENTS.md** 读取 ⇒ 存在即屏蔽真源，视为违规。
#    （Claude Code 官方：有 CLAUDE.md 时只读它，不读 AGENTS.md）
#    ⚠️ GEMINI.md 同属此类：Gemini CLI 默认只读它、不读 AGENTS.md。
#       曾把它当「允许的指针」保留 —— 那是错的：保留即制造第二份入口。
SHADOWS = ["CLAUDE.md", ".cursorrules", ".github/copilot-instructions.md",
           "GEMINI.md", ".gemini/GEMINI.md", "AGENT.md"]

MAIN_MAX_LINES = 150
# ⚠️ 软阈值（2026-10-11 新增）：接近上限时**提醒该拆了**，而不是让人继续压缩。
#    起因：`stash/AGENTS.md` 与根 `AGENTS.md` 都曾顶到 150/150，只能靠删字续命 ——
#    而删字会丢掉「为什么」（本仓最值钱的东西）。正确处置是**分层**：
#      入口（<150 行，只放结论与索引）  →  详情（`references/*.md`，无行数限制）
#    本仓已有先例：`clash/AGENTS.md`（50 行）+ `references/profiles/clash.md`（2500+ 行）。
#    ⇒ 到软阈值时，`check` 提示「把详情移到 references/，入口改指针」。
MAIN_WARN_LINES = 120
SIX_AREAS = {
    "命令": ["verify_all", "python"],
    "测试/门禁": ["门禁", "verify_all", "退出码"],
    "结构": ["self-conf-skills/", "surge/", "profiles"],
    "风格": ["注释", "真源", "生成物"],
    "git/流程": ["CI", "提交", "PR", "发版"],
    "边界": ["从不要", "从不", "红线", "禁止", "🚫"],
}


# ⑥ 文档可达性的豁免（**只豁免「按约定成批产生」的目录**）
#
#    `releases/*.md` 是每个版本一份的发布说明，**逐版累积** ⇒ 若要求每篇都被链接，
#    每发一版都要去改路由表（且旧版本说明本身没有「被谁引用」的语义）。
#    它们的**命名约定**在 `references/ops.md` 里有文档（`releases/<tag>.md`），
#    这满足「读者能找到规则」的要求。
#    ⚠️ 豁免要写在这里**并注明理由** —— 否则它就是「孤儿文档的后门」。
REACH_EXEMPT_DIRS = ("releases/",)


def _md_files():
    """仓库内全部 .md（相对路径，正斜杠；跳过 .git）。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".md"):
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
                out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def _unreachable_docs(main_txt, main_abs):
    """从 MAIN 沿 markdown 链接做 BFS，返回**到不了**的 .md（孤儿文档）。

    为什么自建而不是复用 `check_links.py`：那个判据验的是**正向**（链接指向的文件在不在）；
    本函数验的是**反向**（文件有没有人指）。两者互补，缺了反向就会出现「孤儿文档」——
    文件合法、链接没错，但**没有任何路径能从入口走到它** ⇒ 对读者等于不存在。
    """
    link_re = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    files = set(_md_files())
    graph = {}
    for rel in files:
        abs_p = os.path.join(ROOT, rel.replace("/", os.sep))
        try:
            txt = io.open(abs_p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        base = os.path.dirname(abs_p)
        out = set()
        for m in link_re.finditer(txt):
            tgt = m.group(1).split("#")[0].strip()
            if not tgt or tgt.startswith(("http://", "https://", "mailto:")):
                continue
            p = os.path.normpath(os.path.join(base, tgt))
            try:
                r = os.path.relpath(p, ROOT).replace(os.sep, "/")
            except ValueError:
                continue
            if r in files and r != rel:
                out.add(r)
        graph[rel] = out

    seen, queue = {MAIN}, [MAIN]
    while queue:
        for nxt in graph.get(queue.pop(), ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)

    return [f for f in sorted(files - seen)
            if not f.startswith(REACH_EXEMPT_DIRS)]


def main():
    if not os.path.isfile(os.path.join(ROOT, "surge", "profiles", "routing.conf")):
        print("❌ 不在仓库根 —— 环境不达标")
        return 2

    # ① 真源存在
    bad = []
    mp = os.path.join(ROOT, MAIN)
    if not os.path.isfile(mp):
        print("❌ 缺 %s —— AI 入口不存在" % MAIN)
        return 1
    main_txt = io.open(mp, encoding="utf-8").read()

    # ② 屏蔽真源的工具专属入口
    for name in SHADOWS:
        p = os.path.join(ROOT, name.replace("/", os.sep))
        if os.path.exists(p):
            bad.append("存在 %s —— 该文件会被对应工具**优先于 AGENTS.md** 读取，"
                       "从而屏蔽真源（Claude Code 官方：有 CLAUDE.md 时只读 CLAUDE.md；"
                       "Gemini CLI 同理只读 GEMINI.md）。"
                       "删掉它，让工具直接读 AGENTS.md" % name)

    # ③ 体积与六域
    n_lines = len(main_txt.splitlines())
    if n_lines > MAIN_MAX_LINES:
        bad.append("%s 有 %d 行 > %d 行上限 —— 研究（ETH Zurich arXiv 2602.11988 / "
                   "GitHub 2500 仓）显示：过长的 context file 只增加推理成本，"
                   "不提升成功率" % (MAIN, n_lines, MAIN_MAX_LINES))
    miss = [k for k, kws in SIX_AREAS.items() if not any(w in main_txt for w in kws)]
    if miss:
        bad.append("%s 缺这些核心域：%s（GitHub 2500 仓分析：缺域是第二常见失败模式）"
                   % (MAIN, " / ".join(miss)))
    lines = main_txt.splitlines()
    if "verify_all" not in chr(10).join(lines[:len(lines) // 2]):
        bad.append("%s 的**前半部分**没有可执行命令 —— 研究建议命令放在前部" % MAIN)

    # ④ 嵌套文件：**必须不存在**（2026-10-11 反转，原为「必须存在」）
    #
    #    理由见文件顶部 NESTED 的注释：嵌套入口跨工具行为不一致（Claude Code 不加载）
    #    ⇒ 靠它传「就近警告」是不可靠的。正确结构是「唯一入口 + 指路标」。
    #    ⚠️ 这条断言是**制度性**的：它拦住「下次又有人往子目录里塞 AGENTS.md」。
    for nf in NESTED_BANNED:
        np_ = os.path.join(ROOT, nf.replace("/", os.sep))
        if os.path.exists(np_):
            bad.append("存在嵌套入口 %s —— **本仓不用嵌套 AGENTS.md**。"
                       "嵌套入口跨工具行为不一致（Codex/Cursor 会加载，**Claude Code 不加载**，"
                       "issue #98796）⇒ 用它传警告不可靠，且它会被 150 行上限逼着删字。"
                       "正确做法：把内容并入 `references/profiles/<侧>.md`，"
                       "在根 %s 的「四侧指路标」加一行指向它" % (nf, MAIN))

    # ⑤ 唯一入口必须真的「指路」——防它退化成空壳
    #
    #    ⚠️ 2026-10-11 修正：初版用**字符串包含**（`need in main_txt`），对抗性注错发现
    #      它**有假绿** —— markdown 链接的**显示文本**（`` `references/profiles/stash.md` ``）
    #      本身就含那个字符串，于是「把链接目标改掉、只留文字」仍判绿。
    #      ⇒ 改为检查**链接目标**（从 `](...)` 里取），这才是「真的指路了」。
    #    ⚠️ 与 ⑥ 的分工：⑤ 管「入口**自己**有没有指到关键视图」（结构要求）；
    #      ⑥ 管「全图**是否连通**」（可达性）。⑤ 的项若在别处也被引用，⑥ 不会红 ——
    #      故两条都需要，不是重复。
    targets = set()
    for _m in re.finditer(r"\]\(([^)\s]+)\)", main_txt):
        _t = _m.group(1).split("#")[0].strip()
        if _t and not _t.startswith(("http://", "https://", "mailto:")):
            targets.add(os.path.normpath(os.path.join(ROOT, _t)).replace(os.sep, "/"))
    for need, why in (("references/INDEX.md", "两张路由表（想问什么去哪份 / 我要做 X 读什么）"),
                      ("references/DIFFERENCES.md", "四侧机制差异汇总"),
                      ("references/profiles/stash.md", "Stash 侧详情主文档")):
        abs_need = os.path.normpath(os.path.join(ROOT, "self-conf-skills", need)).replace(os.sep, "/")
        if abs_need not in targets:
            bad.append("%s **没有链接到** `%s` —— 它是%s，入口不指路就退化成了"
                       "「只有纪律、没有去处」（注意：光在文字里提到不算，要真的是链接）"
                       % (MAIN, "self-conf-skills/" + need, why))

    # ⑥ ⭐ 文档可达性：**每一篇 .md 都必须能从 MAIN 沿链接到达**
    #
    #    为什么要有这条（2026-10-11 新增）：
    #      本仓文档已 17 篇、900+ 个节。新建一篇却忘了挂进任何路由表 ⇒ 它就成了
    #      **孤儿**：链接检查（`check_links.py`）只验「链接指向的文件在不在」，
    #      **不验「文件有没有人指」** —— 孤儿文档对读者**不存在**，却不会被任何判据发现。
    #      实测（改造当天）就抓到 3 个：`SKILL.md`（Agent Skills 标准入口，根文件完全没提）、
    #      `gates/probes/README.md`（探针题库）、`releases/v2026-10-10.md`。
    #
    #    ⭐ 这就是「不错过任何一个角落」的机器实现：**加文档时忘了接线路 ⇒ 判负**。
    #      它与 ④/⑤ 合成完整闭环：唯一入口（④）→ 真的指路（⑤）→ 全图连通（⑥）。
    orphans = _unreachable_docs(main_txt, mp)
    if orphans:
        bad.append("有 %d 篇文档**从 %s 沿链接到不了**（孤儿文档 —— 读者找不到它，"
                   "而 check_links.py 只管「链接指向的文件在不在」，不管反向）：%s。"
                   "修法：在 %s 的路由表或某篇被引到的文档里**加一条链接**"
                   "（纯文本提及不算）" % (len(orphans), MAIN, orphans, MAIN))


    print("AI 入口唯一性（唯一真源 %s，不做工具专属兼容）" % MAIN)
    print("-" * 78)
    if bad:
        for b in bad:
            print("  NG %s" % b)
        print("-" * 78)
        print("入口违规 %d 处" % len(bad))
        return 1
    print("  OK %s（%d 行）· 真源唯一" % (MAIN, n_lines))
    if n_lines >= MAIN_WARN_LINES:
        print("     ⚠️ 根文件已 %d 行（软阈值 %d / 硬上限 %d）—— **别再压缩，该分层**："
              "长表 / 详情移到 `self-conf-skills/references/`，根文件只留结论与索引"
              % (n_lines, MAIN_WARN_LINES, MAIN_MAX_LINES))
    print("  OK 无嵌套入口（%d 个位置已查）· 唯一入口 + 指路标"
          % len(NESTED_BANNED))
    print("  OK 无工具专属入口（%d 类已查）· 任一 AI 读同一份 %s"
          % (len(SHADOWS), MAIN))
    print("-" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())

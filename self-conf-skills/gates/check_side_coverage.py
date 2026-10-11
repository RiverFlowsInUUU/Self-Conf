#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四侧覆盖 —— 「加了一侧却漏改别处」必须判负。

为什么要有这一项（2026-10-11 新增）
────────────────────────────────────
用户的原始观察（**真实事故，不是假设**）：
  「有些地方只提供了 Stash 的脚本，但其他相关位置没有补充 Stash 的内容，
    这种修改就是错误的」——加 Stash 那一轮，作者补了脚本，但**多处陈述/表格/判据
    没跟上**，靠肉眼才发现。

而「漏改」的后果分三档，**一档比一档隐蔽**：
  ① 陈述漏了 —— 读者以为只有三侧（可读性）
  ② 表格漏了 —— 对照表少一列，照抄者按错的列去改（误导）
  ③ **判据漏了** —— 最危险：扫描面按扩展名/路径枚举，新形态落在外面 ⇒
     **新配置完全不被检查，而判据照样绿**。
     ⚠️ 本仓实测过：`check_secrets.py` 的扩展名表是 `(.conf,.yaml,.yml)`，
        漏了 `.stoverride` ⇒ 往 Stash 覆写注入假密钥**判绿**。这是安全判据上的洞。

⇒ 本判据把「漏改」变成**机器会叫**，分两层：
   L1 **交付面注册表**（下面 `DELIVERABLES`）是**唯一真源**：四侧各自的
      入口文件、配置形态、是否进 Release 资产、是否有版本头注……
      任何「按侧枚举」的判据都应当从这里取，而不是各写各的一份枚举。
   L2 **一致性断言**：注册表 ↔ 实际文件系统 ↔ 关键文档（README/DIFFERENCES）
      三边对拍。少一侧、多一个未登记的形态，都判负。

⚠️ 加新一侧时要做什么（本判据会逐条检查，漏了会红）：
  1. `DELIVERABLES` 加该侧一条（写清：入口文件、形态、是否 Release 资产、是否有版本）
  2. README 的下载表加一行
  3. `references/DIFFERENCES.md` 的对照表加一列
  4. **所有「按扩展名/路径枚举扫描面」的判据**加该形态
     （本判据会扫 `gates/` 里出现扩展名元组的脚本，提醒你去看）

退出码：0 = 三边一致 · 1 = 有漏改 · 2 = 前置环境不达标。
用法：python self-conf-skills/gates/check_side_coverage.py [仓库根]
"""
import io
import os
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# ══════════════════════════════════════════════════════════════════════════
#  交付面注册表 —— **唯一真源**
# ══════════════════════════════════════════════════════════════════════════
#
#  四侧 = 三个**内核**（Surge/Egern/mihomo）+ 一个**客户端**（Stash）。
#  ⚠️ 字段的含义：
#    is_kernel    —— 是否计入「三内核」口径（版本号、Release 资产、KERNELS 遍历）
#    entry        —— 该侧**交付给用户的入口文件**（真实存在，本判据断言）
#    exts         —— 该侧配置的**文件扩展名**（供「按扩展名枚举」的判据参考）
#    in_release   —— 是否进 Release 的 12 件资产
#    has_version  —— 是否有 `#! version=` 头注（升版时要改）
#    profile      —— 该侧详情主文档（本判据断言它存在且被入口链接）
#    doc_column   —— 在「按侧分列」的文档表里用的列名
DELIVERABLES = {
    "surge": {
        "is_kernel": True, "entry": "surge/profiles/routing.conf",
        "exts": (".conf",), "in_release": True, "has_version": True,
        "profile": "self-conf-skills/references/profiles/surge.md",
        "doc_column": "Surge",
    },
    "egern": {
        "is_kernel": True, "entry": "egern/profiles/routing.yaml",
        "exts": (".yaml",), "in_release": True, "has_version": True,
        "profile": "self-conf-skills/references/profiles/egern.md",
        "doc_column": "Egern",
    },
    "mihomo": {
        "is_kernel": True, "entry": "clash/profiles/routing.yaml",
        "exts": (".yaml",), "in_release": True, "has_version": True,
        "profile": "self-conf-skills/references/profiles/clash.md",
        "doc_column": "mihomo",
    },
    # ⚠️ Stash **不是内核**：它是 iOS/macOS 上的 Clash 系客户端。
    #    它没有完整配置（只发覆写文件）、没有版本头注、不进 Release 资产。
    "stash": {
        "is_kernel": False, "entry": "stash/override/routing.stoverride",
        "exts": (".stoverride",), "in_release": False, "has_version": False,
        "profile": "self-conf-skills/references/profiles/stash.md",
        "doc_column": "Stash",
    },
}

# 判据脚本里「按扩展名枚举扫描面」的写法（本判据会扫出来提醒同步）
EXT_TUPLE = re.compile(r'endswith\(\s*\(([^)]*)\)')

# ══════════════════════════════════════════════════════════════════════════
#  ⚠️ 完整性锚点：**四侧是客观事实，不能只靠注册表自己说**
# ══════════════════════════════════════════════════════════════════════════
#
#  为什么需要它（2026-10-11 对抗性注错发现）：初版只遍历 `DELIVERABLES` **自己的项**
#  ⇒ 把注册表里的 `"stash"` 键改名、或整条删掉，判据**照样绿** ——
#  因为它只检查「注册表提到的文件在不在」，**没有独立真源说"必须恰好这四侧"**。
#  这是**自指判据的通病**：判据与它要守的东西同源 ⇒ 改一处两边一起变，谁也发现不了。
#
#  ⇒ 锚点取自**与注册表无关的事实**：
#     · `stash/override/` 客观存在 ⇒ 注册表必须有 stash 项
#     · 四侧目录都存在 ⇒ 注册表必须恰好覆盖这四侧（不多不少）
REQUIRED_SIDES = ("surge", "egern", "mihomo", "stash")
# 各侧的「客观存在证据」：目录在 ⇒ 这一侧就在（与注册表无关）
SIDE_EVIDENCE = {
    "surge": "surge/profiles",
    "egern": "egern/profiles",
    "mihomo": "clash/profiles",
    "stash": "stash/override",
}
# ⚠️ 下面两张表是**锚点自带**的列名与详情路径 —— 与 `DELIVERABLES` 解耦。
#    为什么解耦：若从 DELIVERABLES 取，「改注册表」就会连锚点一起改掉（自指通病）。
#    ⇒ 加侧时**必须同时改这两张表**（改一处不改另一处会判负，这是刻意的摩擦）。
REQUIRED_COLUMNS = {
    "surge": "Surge", "egern": "Egern", "mihomo": "mihomo", "stash": "Stash",
}
REQUIRED_PROFILES = {
    "surge": "self-conf-skills/references/profiles/surge.md",
    "egern": "self-conf-skills/references/profiles/egern.md",
    "mihomo": "self-conf-skills/references/profiles/clash.md",
    "stash": "self-conf-skills/references/profiles/stash.md",
}


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    root = os.path.abspath(root)
    ok, bad = [], []

    # ── L0：完整性锚点 —— 注册表必须**恰好**覆盖客观存在的四侧 ──────────
    #
    #    ⭐ 这条是「防自指」的关键：删/改注册表里的某一侧 ⇒ 这里判负。
    for side in REQUIRED_SIDES:
        ev = SIDE_EVIDENCE[side]
        if os.path.isdir(os.path.join(root, ev.replace("/", os.sep))):
            if side not in DELIVERABLES:
                bad.append("`%s/` 目录存在 ⇒ **%s 这一侧真实存在**，"
                           "但交付面注册表里没有它（或被改名/删除）—— "
                           "注册表漏登一侧，所有「按它枚举」的检查都会漏掉该侧"
                           % (ev, side))
    extra = [s for s in DELIVERABLES if s not in REQUIRED_SIDES]
    if extra:
        bad.append("注册表里有未被承认的侧：%s（`REQUIRED_SIDES` 是锚点，"
                   "加侧要**同时**改注册表与这里）" % extra)
    if not bad:
        ok.append("完整性锚点通过：注册表恰好覆盖客观存在的 %d 侧" % len(REQUIRED_SIDES))

    # ── L1：注册表 ↔ 文件系统 ────────────────────────────────────────────
    for side, d in sorted(DELIVERABLES.items()):
        for label, rel in (("交付入口", d["entry"]), ("详情主文档", d["profile"])):
            if not os.path.isfile(os.path.join(root, rel.replace("/", os.sep))):
                bad.append("%s 的%s不存在：`%s`（注册表说了它该在）" % (side, label, rel))
    if not bad:
        ok.append("四侧交付入口与详情主文档都存在（%d 侧）" % len(DELIVERABLES))

    # ⚠️ 下面三条一律以 **REQUIRED_SIDES（锚点）** 为准，**不**遍历 DELIVERABLES ——
    #    否则「把某侧从注册表删掉」就能让它们一起消失（自指判据的通病）。
    #    列名与详情路径也取自**锚点表**，与注册表解耦。

    # ── L2a：README 下载表必须四侧齐全 ──────────────────────────────────
    readme = os.path.join(root, "README.md")
    if os.path.isfile(readme):
        txt = io.open(readme, encoding="utf-8").read()
        # 下载表 = 含 "各美其美" 之后、下一个 ## 之前的那段
        m = re.search(r"^## .*各美其美.*?$(.*?)^## ", txt, re.S | re.M)
        table = m.group(1) if m else ""
        miss = [REQUIRED_COLUMNS[c] for c in REQUIRED_SIDES if c not in table]
        if miss:
            bad.append("README 的下载表缺这些侧：%s —— **加了侧就要加行**，"
                       "否则读者以为不存在" % miss)
        else:
            ok.append("README 下载表四侧齐全")
    else:
        bad.append("找不到 README.md")

    # ── L2b：差异汇总表必须四侧齐全 ────────────────────────────────────
    diff = os.path.join(root, "self-conf-skills", "references", "DIFFERENCES.md")
    if os.path.isfile(diff):
        dtxt = io.open(diff, encoding="utf-8").read()
        # 找表头含全部四侧列名（锚点表）的那一行
        header = None
        for line in dtxt.splitlines():
            if line.strip().startswith("|") and \
               all(REQUIRED_COLUMNS[c] in line for c in REQUIRED_SIDES):
                header = line
                break
        if not header:
            bad.append("`references/DIFFERENCES.md` 里找不到**含四侧列**的对照表 —— "
                       "四侧机制差异必须有一张并列表，否则「对齐前先读它」就是空话")
        else:
            ok.append("DIFFERENCES.md 有含四侧列的对照表")
    else:
        bad.append("找不到 references/DIFFERENCES.md")

    # ── L2c：入口（AGENTS.md）必须链接到四侧详情 ────────────────────────
    agents = os.path.join(root, "AGENTS.md")
    if os.path.isfile(agents):
        atxt = io.open(agents, encoding="utf-8").read()
        targets = set()
        for mm in re.finditer(r"\]\(([^)\s]+)\)", atxt):
            t = mm.group(1).split("#")[0].strip()
            if t and not t.startswith(("http://", "https://", "mailto:")):
                targets.add(os.path.normpath(os.path.join(root, t)).replace(os.sep, "/"))
        # 以锚点表为准（不遍历注册表），这样删注册表项也会在这里判负
        miss = [s for s in REQUIRED_SIDES
                if os.path.normpath(os.path.join(root, REQUIRED_PROFILES[s])).replace(os.sep, "/")
                not in targets]
        if miss:
            bad.append("AGENTS.md 未链接到这些侧的详情主文档：%s —— "
                       "入口的指路标必须覆盖每一侧" % miss)
        else:
            ok.append("AGENTS.md 已链接四侧详情主文档")
    else:
        bad.append("找不到 AGENTS.md")

    # ── L2d：⚠️ 扫描面提醒 —— 哪些判据按扩展名枚举 ──────────────────────
    #    这条不判负，只**打印**：加侧时要人工去这些地方同步。
    #    （判负的是 check_secrets.py 自带的「覆盖形态断言」——它在那边守着。）
    all_exts = tuple(e for d in DELIVERABLES.values() for e in d["exts"])
    scanners = []
    gates_dir = os.path.join(root, "self-conf-skills", "gates")
    for dp, dns, fns in os.walk(gates_dir):
        dns[:] = [x for x in dns if not x.startswith(".")]
        for fn in sorted(fns):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            body = io.open(p, encoding="utf-8", errors="replace").read()
            for mm in EXT_TUPLE.finditer(body):
                exts = re.findall(r'"(\.[\w]+)"', mm.group(1))
                if exts:
                    rel = os.path.relpath(p, root).replace(os.sep, "/")
                    missing = [e for e in all_exts if e not in exts
                               and e not in (".yml",)]
                    scanners.append((rel, exts, missing))

    print("四侧覆盖（交付面注册表 ↔ 文件系统 ↔ 关键文档）")
    print("-" * 78)
    for m in ok:
        print("  ✅ %s" % m)
    for m in bad:
        print("  ❌ %s" % m)
    if scanners:
        print("  ℹ️ 按扩展名枚举扫描面的判据（加侧时**逐个人工核对**）：")
        for rel, exts, missing in scanners:
            flag = "  ⚠️ 缺 %s" % missing if missing else ""
            print("     %-56s %s%s" % (rel, exts, flag))
    print("-" * 78)
    if bad:
        print("判负 %d 处 —— 见本文件顶部「加新一侧时要做什么」" % len(bad))
        return 1
    print("通过 %d 项 —— 四侧覆盖完整" % len(ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())

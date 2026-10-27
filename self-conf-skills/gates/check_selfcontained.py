#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自洽性检查 —— 整合仓不得引用原仓的在线资源。

为什么单独要这一项（整合最容易犯的错）：
    把两个仓的文件复制进一个新仓，文件是进来了，但**里面的 URL 还指着原仓**。
    表面上整合成功、门禁全绿，实际上新仓不自洽 —— 把原仓删了，
    图标全挂、规则集全空，而配置还能"正常加载"（远程集拉不到只是静默变空）。

    本仓踩过：整合后共 2511 处 URL 仍指向 Self-Configuration / Clash，
    其中图标 2311 处、规则集 200 处。

判据：
    · 扫描配置与脚本里的 http(s) URL
    · 出现原仓仓库名（Self-Configuration / Clash）即判负
    · 出现姊妹仓**改名前的旧路径**（RiverFlowsInUUU/Jinx）同样判负 ——
      旧路径一直 200（GitHub 内部重定向），留着不报错，只是在赌一条转发
    · 注释里的说明性文字（提及来源）不在扫描范围 —— 那是记录，不是引用
    · 上游第三方（MetaCubeX / blackmatrix7 / TG-Twilight）放行；
      姊妹仓 RFU-Rules 属本账号名下，本就在放行范围（不在上面那张判负表里）

退出码：0 = 自洽 · 1 = 存在外部依赖
用法：python self-conf-skills/gates/check_selfcontained.py [仓库根]
"""

import os
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

# 判负的仓库名 —— 出现即判负（本仓不得有指向它们的在线引用）
#   · Self-Configuration / RiverFlowsInUUU/Clash：2026-10 整合前的原仓，已归档
#   · RiverFlowsInUUU/Jinx：姊妹仓**改名前的旧路径**（2026-10-27 更名为 RFU-Rules）。
#     GitHub 对旧路径持续返回 200（内部重定向）⇒ 用旧地址**不会报错**，
#     只是静默依赖一条随时可能失效的转发（旧名一旦被别的仓占用，转发就断，
#     而规则集拉不到只会**变空**，配置照样"加载成功"）。
#     「还能用、但已不该用」的 URL，注释守不住，只有判据能守。
FORBIDDEN_REPOS = ("Self-Configuration", "RiverFlowsInUUU/Clash", "RiverFlowsInUUU/Jinx")

# 排除：说明性文字（注释里提及来源不算引用）
COMMENT_PREFIX = ("#", "//", ";")

# ⚠️ 2026-10-11：**曾漏 `.stoverride`**（Stash 覆写）—— 本判据是全仓 walk，
#    但扩展名表没有它 ⇒ Stash 配置**完全不进扫描**（实测注入外部仓引用仍判绿）。
#    与 `check_secrets.py` 同一类漏改（见那边的 KNOWN_FORMS 断言）。
#    ⇒ **加新交付形态时必须同步这张表**；`check_side_coverage.py` 会列出所有
#      「按扩展名枚举扫描面」的判据提醒人工核对。
EXTS = (".yaml", ".conf", ".js", ".list", ".txt", ".json", ".yml", ".py", ".stoverride")
# ⚠️ `config_old` 已于 2026-10-08 删除（历史交给 git）；仍列在此处是**防御性**的
#    —— 万一有人重新建了归档目录，它同样不该进扫描面。
SKIP_DIRS = {".git", "__pycache__", "icons", "config_old"}

URL_RE = re.compile(r"https?://[^\s\"'`,)\]]+")


def scan(path):
    hits = []
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except Exception:
        return hits
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # 跳过纯注释行
        if stripped.startswith(COMMENT_PREFIX):
            continue
        for m in URL_RE.finditer(line):
            u = m.group(0).rstrip(".,;")
            for repo in FORBIDDEN_REPOS:
                if repo in u:
                    hits.append((i, u))
                    break
    return hits


def main():
    print("自洽性检查 —— 整合仓不得引用原仓在线资源")
    print("-" * 78)
    bad = []

    # ⭐ 覆盖形态断言（2026-10-11 新增）：每一种**已知交付形态**都至少要扫到一个文件。
    #
    #    为什么要有它：本判据曾因 `EXTS` 漏 `.stoverride` 而**完全跳过 Stash 配置**
    #    （实测注入外部仓引用仍判绿）。而「扩展名表」这种写法**天生会漏** ——
    #    加新形态的人不一定会想到这里。更隐蔽的是：漏了之后判据**照样输出
    #    「自洽 —— 均引用本仓资源」**，是彻头彻尾的假绿。
    #    ⇒ 用一条断言把「漏」变成判据会叫。加新形态时必须同步两处：
    #      ① `EXTS` 加后缀 ② 下面加期望项。
    KNOWN_FORMS = {
        ".conf": "Surge（`surge/profiles/*.conf`）",
        ".yaml": "Egern / mihomo（`*/profiles/*.yaml`）",
        ".stoverride": "**Stash**（`stash/override/*.stoverride`）",
    }
    # ⚠️ 必须查**两件事**（初版只查了文件系统 ⇒ 改 `EXTS` 不会红，那是查错了对象）：
    #    ① `EXTS` 这张表里有没有该形态 ② 文件系统里确实有这种文件。
    seen_exts = set()
    for dp, dn, fs in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fs:
            for e in KNOWN_FORMS:
                if f.endswith(e):
                    seen_exts.add(e)
    for ext, who in KNOWN_FORMS.items():
        if ext not in EXTS:
            bad.append(("(扫描面 EXTS)", 0,
                        "覆盖形态缺失：`EXTS` 不含 `%s`，但它是已知交付形态 —— %s。"
                        "**新加一侧时 EXTS 与 KNOWN_FORMS 必须同步**"
                        "（`check_side_coverage.py` 也会列出这类扫描面提醒核对）"
                        % (ext, who)))
        elif ext not in seen_exts:
            bad.append(("(扫描面 文件)", 0,
                        "覆盖形态缺失：`EXTS` 收了 `%s`，但仓库里**找不到**这种文件 —— %s"
                        "。该侧配置是被挪走还是删了？" % (ext, who)))

    for dp, dn, fs in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fs:
            if not f.endswith(EXTS):
                continue
            p = os.path.join(dp, f)
            for ln, u in scan(p):
                bad.append((os.path.relpath(p, ROOT), ln, u))

    if bad:
        print("外部依赖 %d 处（应改为指向本仓）：" % len(bad))
        for rel, ln, u in bad[:20]:
            print("  NG %s:%d" % (rel, ln))
            print("       %s" % u[:100])
        if len(bad) > 20:
            print("  ... 另 %d 处" % (len(bad) - 20))
        print("-" * 78)
        print("修法：把 URL 里的仓库名换成 self-conf，"
              "并确认对应文件已在本仓（icons/ 或 rules/）")
        return 1
    print("自洽 —— 配置与脚本均引用本仓资源")
    return 0


if __name__ == "__main__":
    sys.exit(main())

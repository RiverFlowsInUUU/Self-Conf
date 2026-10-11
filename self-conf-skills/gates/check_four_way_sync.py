#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四侧分流意图对拍 —— 「改了一处、忘了改另一处」必须判负。

为什么需要它（2026-10-11 补）
──────────────────────────────
本仓的分流意图同时存在于**四份**配置里：

    surge/profiles/*.conf      egern/profiles/*.yaml
    clash/profiles/*.yaml      stash/override/*.stoverride

在这道闸门之前，四侧之间**没有任何机器对拍**（只有各内核内部的 `.min` 对拍、
以及若干只管版本号/AD 口径的窄判据）。后果是**真实发生过**的：

  · 加 `stash/` 那一轮，作者（AI）改了 5 处陈述才靠**人工**发现漏改 ——
    期间四侧一致性全靠肉眼，没有任何判据会叫。
  · `stash/override/*.stoverride` 是**手工派生**（Stash 跑不了 mihomo 的 JS，
    本仓唯一没有生成器的派生）⇒ 它的漂移形态就是「静默」：Stash 加载失败不报错，
    组空着、规则不生效，面板上只「看起来少了东西」。

⇒ 这正是本仓反复记录的那类事故的同构案例：**「全绿但已损坏」**。
   故落成判据（AGENTS.md：「不是『记得去检查』，而是把它变成一道会定期跑的闸门」）。

断言（全部为**实测成立**的不变量，不是设计理想）
────────────────────────────────────────────────
F1  `clash` 与 `stash` 的**规则列表逐字相同**（实测 27/27、13/13）。
F2  `clash` 与 `stash` 的**组（name / type / proxies）逐项相同**，且组名**序列**相同。
F3  `clash` 与 `stash` 的 **rule-provider 键集合与序列**相同。
F4  `surge` 与 `egern` 的**组名序列**相同。
F5  四侧的**规则集去向（source → target）**一致，豁免表内的刻意差异除外。
F6  四侧**组名集合**的差集只能是登记过的刻意项（`Airport` 只在 Surge/Egern；
    倍率三档只在 Clash/Stash）。

⚠️ 刻意豁免都写在下面的表里，**并注明理由与出处**。新增豁免要一并写理由 ——
   本仓纪律：差异可以刻意，但不能「没人知道它刻意」（见 profiles/*.md 的
   `EXPECTED_DIFF` 与 gates.md 的判别力一节）。

为什么不复用 check_priority_weight.py 的 S7
──────────────────────────────────────────
S7 断言的是「**smart 组**的组名集合跨内核一致」—— 它只覆盖 Surge/Egern
（Clash 系用 `url-test`，没有 smart 组）。把 Stash 塞进 S7 会**必红**
（它没有 smart 组）。S7 管的是「权重口径」，本闸门管的是「意图同构」，
两者判据面不同，**不能合并**。

退出码：0 = 全部成立 · 1 = 有断言不成立 · 2 = 前置环境不达标（文件缺失/解析失败）。
用法：python self-conf-skills/gates/check_four_way_sync.py [仓库根]
"""
import io
import os
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.join(HERE, "..", "run"), os.path.join(HERE, "..", "lib")):
    _cand = os.path.normpath(_cand)
    if os.path.isdir(_cand):
        sys.path.insert(0, _cand)

try:
    import build_ir
except Exception as e:                                                # noqa: BLE001
    print("❌ 前置不达标：无法 import build_ir（%s）" % e)
    raise SystemExit(2)

SIDES = ("surge", "egern", "clash", "stash")

# ── 刻意豁免表（**唯一真源**，改口径只改这里）─────────────────────────────
#
# ① 规则集去向的刻意差异。
#    Surge 侧广告规则**直接挂 REJECT**（它的内置拦截口径如此），而 Egern 侧
#    统一挂 `AD` 组（可在面板上切换 DIRECT）。两者都达成「广告拦截」，只是
#    Surge 少一层可切换的组。出处：check_ad_caliber.py 的 docstring 与
#    references/profiles/surge.md 的 AD 组一节。
TARGET_EXEMPT = {
    "surge-ads": {"surge": "REJECT", "egern": "AD"},
    "awavenue-ads-rule-surge-rule-set": {"surge": "REJECT", "egern": "AD"},
}

# ② 组名集合的刻意差异。
#    · `Airport` —— Surge/Egern 的**订阅槽位组**（`external` / 手填订阅）；
#      Clash 系用 `proxy-providers`，没有这个组。
#    · 倍率三档 —— Clash/Stash 的 `Smart` 用三档结构（运行时 filter 能分档）；
#      Surge/Egern 的 smart 组用 `policy-priority` 权重表达同一件事，故无这三个组。
#    出处：根 AGENTS.md「三内核机制差异」+ profiles/clash.md §7。
GROUP_EXEMPT = {
    "Airport": ("surge", "egern"),
    "Auto": ("clash", "stash"),
    "Low Mult.": ("clash", "stash"),
    "High Mult.": ("clash", "stash"),
}

FAMS = ("routing", "lazy")


def _load(root, side, fam):
    path = build_ir._kernel_paths(Path(root), fam)[side]
    if not path.exists():
        raise FileNotFoundError(str(path))
    if side == "surge":
        return build_ir._load_surge_groups(path), build_ir._load_surge_rules(path)
    if side in ("clash", "stash"):
        return build_ir._load_clash_groups(path), build_ir._load_clash_rules(path)
    return build_ir._load_egern_groups(path), build_ir._load_egern_rules(path)


def _providers(root, side, fam):
    """rule-provider 的键序列。只有 clash/stash 有（Surge/Egern 内联在规则行里）。"""
    path = build_ir._kernel_paths(Path(root), fam)[side]
    if side not in ("clash", "stash"):
        return None
    import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list((data.get("rule-providers") or {}).keys())


def _targets(rules):
    """source_norm -> target（跳过终结规则：各侧形态不同，无可比性）。"""
    out = {}
    for r in rules:
        key = r.get("source_norm")
        if not key or r["kind"] in ("FINAL", "MATCH"):
            continue
        out[key] = r.get("target")
    return out


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(HERE))
    root = os.path.abspath(root)

    if not os.path.isdir(os.path.join(root, "stash", "override")):
        print("❌ 前置不达标：找不到 stash/override/（不在仓库根？）")
        return 2

    ok, bad = [], []
    try:
        data = {}
        for fam in FAMS:
            for side in SIDES:
                data[(fam, side)] = _load(root, side, fam)
    except Exception as e:                                            # noqa: BLE001
        print("❌ 前置不达标：解析失败 —— %s" % e)
        return 2

    for fam in FAMS:
        # ── F1：clash 与 stash 规则逐字相同 ──────────────────────────────
        rc = [r["kind"] + "," + str(r.get("source")) + "," + str(r.get("target"))
              for r in data[(fam, "clash")][1]]
        rs = [r["kind"] + "," + str(r.get("source")) + "," + str(r.get("target"))
              for r in data[(fam, "stash")][1]]
        if rc == rs:
            ok.append("F1 %-7s clash ≡ stash 规则逐字相同（%d 条）" % (fam, len(rc)))
        else:
            detail = []
            for i in range(max(len(rc), len(rs))):
                a = rc[i] if i < len(rc) else "（缺）"
                b = rs[i] if i < len(rs) else "（缺）"
                if a != b:
                    detail.append("第 %d 条 clash=%s stash=%s" % (i + 1, a, b))
                if len(detail) >= 3:
                    break
            bad.append("F1 %-7s clash 与 stash 规则不一致：%s" % (fam, "；".join(detail)))

        # ── F2：组（name/type/proxies）逐项相同 ──────────────────────────
        gc = [(g["name"], g["type"], tuple(g["members"])) for g in data[(fam, "clash")][0]]
        gs = [(g["name"], g["type"], tuple(g["members"])) for g in data[(fam, "stash")][0]]
        if gc == gs:
            ok.append("F2 %-7s clash ≡ stash 组逐项相同（%d 组）" % (fam, len(gc)))
        else:
            d = []
            for i in range(max(len(gc), len(gs))):
                a = gc[i] if i < len(gc) else ("（缺）", "", ())
                b = gs[i] if i < len(gs) else ("（缺）", "", ())
                if a != b:
                    d.append("%s vs %s" % (a, b))
                if len(d) >= 3:
                    break
            bad.append("F2 %-7s clash 与 stash 组不一致：%s" % (fam, "；".join(d)))

        # ── F3：rule-provider 键序列相同 ─────────────────────────────────
        pc = _providers(root, "clash", fam)
        ps = _providers(root, "stash", fam)
        if pc == ps:
            ok.append("F3 %-7s clash ≡ stash 规则集键序列相同（%d 份）" % (fam, len(pc or [])))
        else:
            only_c = [x for x in (pc or []) if x not in (ps or [])]
            only_s = [x for x in (ps or []) if x not in (pc or [])]
            if set(pc or []) != set(ps or []):
                bad.append("F3 %-7s 规则集键集合不同：仅 clash=%s 仅 stash=%s"
                           % (fam, only_c, only_s))
            else:
                bad.append("F3 %-7s 规则集键**集合相同但次序不同** —— "
                           "Stash 覆写默认前置插入，次序影响可读性与后续 diff" % fam)

        # ── F4：surge ≡ egern 组名序列相同 ───────────────────────────────
        names_sg = [g["name"] for g in data[(fam, "surge")][0]]
        names_eg = [g["name"] for g in data[(fam, "egern")][0]]
        if names_sg == names_eg:
            ok.append("F4 %-7s surge ≡ egern 组名序列相同（%d 组）" % (fam, len(names_sg)))
        else:
            bad.append("F4 %-7s surge 与 egern 组名序列不同：surge=%s egern=%s"
                       % (fam, names_sg, names_eg))

        # ── F5：四侧去向一致（豁免表外）──────────────────────────────────
        tgt = {s: _targets(data[(fam, s)][1]) for s in SIDES}
        keys = sorted(set().union(*[set(t) for t in tgt.values()]))
        mism = []
        for key in keys:
            present = {s: tgt[s][key] for s in SIDES if key in tgt[s]}
            if len(set(present.values())) <= 1:
                continue
            exempt = TARGET_EXEMPT.get(key)
            if exempt and present == exempt:
                continue
            mism.append("%s=%s" % (key, present))
        if not mism:
            ok.append("F5 %-7s 四侧规则集去向一致（豁免 %d 条刻意项，%d 个 source 已核）"
                      % (fam, len(TARGET_EXEMPT), len(keys)))
        else:
            bad.append("F5 %-7s 四侧去向不一致（且不在豁免表内）：%s"
                       % (fam, "；".join(mism[:4])))

        # ── F6：组名集合只差登记过的刻意项 ───────────────────────────────
        gsets = {s: {g["name"] for g in data[(fam, s)][0]} for s in SIDES}
        unregistered = []
        for name in sorted(set().union(*gsets.values())):
            holders = tuple(s for s in SIDES if name in gsets[s])
            if len(holders) == len(SIDES):
                continue
            if GROUP_EXEMPT.get(name) == holders:
                continue
            unregistered.append("%s（仅 %s）" % (name, list(holders)))
        if not unregistered:
            ok.append("F6 %-7s 组名差集全部是登记过的刻意项（豁免 %d 项）"
                      % (fam, len(GROUP_EXEMPT)))
        else:
            bad.append("F6 %-7s 出现未登记的组名差集：%s"
                       % (fam, "；".join(unregistered)))

    print("四侧分流意图对拍（surge · egern · clash · stash）")
    print("-" * 78)
    for m in ok:
        print("  ✅ %s" % m)
    for m in bad:
        print("  ❌ %s" % m)
    print("-" * 78)
    if bad:
        print("判负 %d 处 —— 改了一处却漏改另一处（豁免表在本文件顶部）" % len(bad))
        return 1
    print("通过 %d 项 —— 四侧意图同构，无未登记的漂移" % len(ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())

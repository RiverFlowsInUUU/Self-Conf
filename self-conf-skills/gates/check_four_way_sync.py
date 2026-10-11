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
F1  `clash` 与 `stash` 的**规则逐字相同**（含 `no-resolve` 等 options；实测 27/27、13/13）。
F2  `clash` 与 `stash` 的**组逐字段相同**（除 `filter`/`exclude-filter` 两个刻意项）。
F3  `clash` 与 `stash` 的 rule-provider **键集合与序列**相同，且**逐字段**相同
    （除 `format`/`url`/`path`/`type`）；`url` 另比「去扩展名后的完整 URL」。
F4  `surge` 与 `egern` 的**组名序列**相同。
F5  四侧的**规则集去向（source → target）**一致，豁免表内的刻意差异除外。
F6  四侧**组名集合**的差集只能是登记过的刻意项（`Airport` 只在 Surge/Egern；
    倍率三档只在 Clash/Stash）。

⚠️ **F1/F2/F3 的「全字段」是对抗性自审后补的**（2026-10-11）。初版只比
   `kind/source/target`、`name/type/proxies`、provider **键序列** ——
   实测有 **4 处漏报**（判据仍绿但配置已漂）：
     · 删掉 stash 某条规则的 `no-resolve` ⇒ 会为判定命中触发本地解析（DNS 泄露入口）
     · 改组的 `interval` ⇒ 测速周期静默漂移
     · 改组的 `hidden` ⇒ 本该隐藏的倍率子组暴露在面板上
     · 换 provider 的 `url` ⇒ 整份名单被换源
   ⚠️ 第二个坑：F2 一度读的是 `build_ir._load_clash_groups()` 的结果，而那个加载器
      只抽 name/type/members 三字段 ⇒ 「全字段比对」名不副实、仍漏报。
      现改为 `_raw_groups()` 直读原始 YAML。
   ⇒ 教训：**判据的「全绿」不能自己声明，要用对抗性自审去证伪**
      （本仓 gates.md §2 三条铁律的同构应用）。

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


def _rule_sig(r):
    """规则的可比签名 —— **含 options**（no-resolve 等），不只是 kind/source/target。

    ⚠️ 2026-10-11 对抗性自审补：最初只比 `kind,source,target`，实测**漏报**
       「删掉 stash 某条规则的 `no-resolve`」（判据仍绿）。`no-resolve` 是有语义的
       ——丢了它会为判定命中而触发一次本地解析，是 DNS 泄露的一个入口。故纳入。
    """
    opts = tuple(r.get("options") or [])
    return (r["kind"], str(r.get("source")), str(r.get("target")), opts)


# 组级字段的**豁免**：这些字段在 clash 与 stash 之间**刻意不同**，不参与逐字段对拍。
#   · filter —— Stash 无 `exclude-filter`，把信息词合进了 filter（见 stash/AGENTS.md ③）
#   · exclude-filter —— 同上（Stash 没有这个键）
# ⚠️ 其余字段（type/proxies/url/interval/tolerance/hidden/icon/lazy/…）**全部逐字对拍**。
GROUP_FIELD_EXEMPT = ("filter", "exclude-filter")


def _raw_groups(root, side, fam):
    """从**原始文件**读组的全部字段。

    ⚠️ 2026-10-11 对抗性自审补：不能用 `build_ir._load_clash_groups()` 的结果 ——
       那个加载器**只抽 name/type/members 三个字段**（IR 只需要这些），
       于是「全字段比对」实际只比了那三个 ⇒ 实测**漏报**「改 interval」「改 hidden」。
       必须直接读原始 YAML。
    """
    import yaml
    path = build_ir._kernel_paths(Path(root), fam)[side]
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("proxy-groups") or []


def _group_fields(g):
    """组的全部字段（除豁免项）—— 用于逐字段对拍。

    ⚠️ 2026-10-11 对抗性自审补：最初只比 `name/type/proxies`，实测**漏报**
       「改 interval」「改 hidden」。后者会让本该隐藏的倍率子组暴露在面板上；
       前者是测速周期的静默漂移。故改为**全字段**（数据源见 `_raw_groups`）。
    """
    return {k: v for k, v in g.items() if k not in GROUP_FIELD_EXEMPT}


def _provider_fields(root, side, fam):
    """rule-provider 的全部字段（url/path/interval 等）—— 用于逐字段对拍。

    ⚠️ 2026-10-11 对抗性自审补：最初只比**键序列**，实测**漏报**
       「改 provider 的 url」。那会让规则集指向错误的源（或换掉整份名单）。
       注意：`format`（mrs→text）与 `url`/`path` 的后缀在两侧**刻意不同**，
       故只比对**同一键在两侧都存在时的 interval 等参数**，格式类差异单列豁免。
    """
    path = build_ir._kernel_paths(Path(root), fam)[side]
    import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("rule-providers") or {}


# provider 中**刻意不同**的字段：
#   · format —— mihomo 用 mrs（省内存），Stash 官方只列 yaml/text（见 stash/AGENTS.md）
#   · url/path —— 前者指向 .mrs、后者指向 .list/.yaml；path 前缀也不同（rule_provider vs ruleset）
#   · type —— mihomo 写 `type: http`，Stash 无此键
# ⚠️ 其余（interval 等）必须一致 —— 刷新周期漂移是真实风险。
PROVIDER_FIELD_EXEMPT = ("format", "url", "path", "type")


def _url_stem(url):
    """规则集 URL 的「资源标识」—— **去掉扩展名，其余原样保留**。

    用于跨侧比对「是否指向同一份上游资源」：两侧扩展名刻意不同
    （mihomo `.mrs` / Stash `.list`、`.yaml`），故不能直接比 url；
    但**去掉扩展名后必须逐字相同** —— 实测 25 份 + 10 份全部一致。

    ⚠️ 2026-10-11 对抗性自审补：最初只取 **basename**，实测**漏报**
       「把 stash 的 github 规则集指向 `example.com/github.list`」——
       basename 同为 `github`，比不出来。改为保留完整 URL（仅去扩展名）后能抓住。
    """
    if not url:
        return None
    import re as _re
    return _re.sub(r"\.(list|txt|yaml|yml|mrs)$", "", str(url).rstrip("/"), flags=_re.I)


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
        # ── F1：clash 与 stash 规则逐字相同（**含 options**）─────────────
        rc = [_rule_sig(r) for r in data[(fam, "clash")][1]]
        rs = [_rule_sig(r) for r in data[(fam, "stash")][1]]
        if rc == rs:
            ok.append("F1 %-7s clash ≡ stash 规则逐字相同（%d 条，含 no-resolve 等选项）"
                      % (fam, len(rc)))
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

        # ── F2：组逐字段相同（除 filter/exclude-filter 两个刻意项）───────
        # ⚠️ 数据源必须是 _raw_groups（原始 YAML 全字段），不能用 IR 的组
        #    —— 后者只含 name/type/members，会让「全字段比对」名不副实。
        cg = [(g.get("name"), _group_fields(g)) for g in _raw_groups(root, "clash", fam)]
        sg = [(g.get("name"), _group_fields(g)) for g in _raw_groups(root, "stash", fam)]
        if cg == sg:
            ok.append("F2 %-7s clash ≡ stash 组逐字段相同（%d 组，除 filter/exclude-filter）"
                      % (fam, len(cg)))
        else:
            d = []
            for i in range(max(len(cg), len(sg))):
                a = cg[i] if i < len(cg) else ("（缺）", {})
                b = sg[i] if i < len(sg) else ("（缺）", {})
                if a != b:
                    fields = {k for k in set(a[1]) | set(b[1]) if a[1].get(k) != b[1].get(k)}
                    d.append("%s 差异字段%s => %s vs %s"
                             % (a[0], sorted(fields),
                                {k: a[1].get(k) for k in fields},
                                {k: b[1].get(k) for k in fields}))
                if len(d) >= 2:
                    break
            bad.append("F2 %-7s clash 与 stash 组不一致：%s" % (fam, "；".join(d)))

        # ── F3：rule-provider 键序列 + 逐字段（除 format/url/path/type）──
        pc = _providers(root, "clash", fam)
        ps = _providers(root, "stash", fam)
        if pc != ps:
            only_c = [x for x in (pc or []) if x not in (ps or [])]
            only_s = [x for x in (ps or []) if x not in (pc or [])]
            if set(pc or []) != set(ps or []):
                bad.append("F3 %-7s 规则集键集合不同：仅 clash=%s 仅 stash=%s"
                           % (fam, only_c, only_s))
            else:
                bad.append("F3 %-7s 规则集键**集合相同但次序不同** —— "
                           "Stash 覆写默认前置插入，次序影响可读性与后续 diff" % fam)
        else:
            fc = _provider_fields(root, "clash", fam)
            fs = _provider_fields(root, "stash", fam)
            pd = []
            for k in fc:
                a = {f: v for f, v in fc[k].items() if f not in PROVIDER_FIELD_EXEMPT}
                b = {f: v for f, v in (fs.get(k) or {}).items()
                     if f not in PROVIDER_FIELD_EXEMPT}
                if a != b:
                    fields = {f for f in set(a) | set(b) if a.get(f) != b.get(f)}
                    pd.append("%s 差异字段%s => %s vs %s"
                              % (k, sorted(fields), {f: a.get(f) for f in fields},
                                 {f: b.get(f) for f in fields}))
            # ⚠️ url 虽在豁免表内（后缀 .mrs vs .list 刻意不同），但**语义必须等价**：
            #    同一份规则集两侧必须指向**同名的上游资源**。对抗性自审实测：
            #    只豁免 url 会**漏报**「把 stash 的 github 规则集指向 example.com」
            #    —— 那是整份名单被换掉，比 interval 漂移严重得多。
            #    故这里再比一层「去后缀后的 basename」。
            for k in fc:
                uc = _url_stem(fc[k].get("url"))
                us = _url_stem((fs.get(k) or {}).get("url"))
                if uc and us and uc != us:
                    pd.append("%s 的 url 指向不同资源：clash=…/%s stash=…/%s"
                              % (k, uc, us))
            if not pd:
                ok.append("F3 %-7s clash ≡ stash 规则集键序列与字段相同"
                          "（%d 份，除 format/url/path/type）" % (fam, len(pc or [])))
            else:
                bad.append("F3 %-7s 规则集字段不一致（如 interval 漂移）：%s"
                           % (fam, "；".join(pd[:3])))

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

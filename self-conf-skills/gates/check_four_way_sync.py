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
#
#    ⚠️ 2026-10-18 两次修正（都来自独立审查）：
#      ① 键名改为 **canonical key**（SOURCE_EQUIV 归一之后的名字）。原来只登记
#         `surge-ads` / `awavenue-ads-rule-surge-rule-set`（URL basename），而归一之后
#         这两个键**永不出现** ⇒ 是两条死条目，让「豁免 4 条」的读数虚高。
#      ② 豁免必须登记**全四侧**的期望去向。原先只写 surge/egern 两侧，判定用
#         `all(present.get(s)==t for s,t in exempt.items())` 只校验这两侧 ⇒
#         **clash/stash 可以被改成任意值而判绿**（实测把 clash 的 `jinx-ads` 改成
#         `DIRECT` = 广告拦截静默关闭，F5 仍报"四侧齐全"）。这比原实现更宽。
#         ⇒ 现在四侧全写，判定改回"全字典相等"语义。
TARGET_EXEMPT = {
    "jinx-ads": {"surge": "REJECT", "egern": "AD", "clash": "AD", "stash": "AD"},
    "awavenue-ads": {"surge": "REJECT", "egern": "AD", "clash": "AD", "stash": "AD"},
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

# ③ 跨内核的 source 归一类别。**按"等价强度"分两张表**，不可混用：
#
#    ⚠️ 2026-10-18 独立审查指出：初版把两类混在一张 `SOURCE_EQUIV` 里，并在注释
#    声称「只登记同一上游、同一语义」，实际有一半条目是**不同上游、只是语义相近**
#    （blackmatrix7 ↔ MetaCubeX ↔ Loyalsoldier 之间互不相同）。这违反了自己定的准入
#    条件，而且掩盖了「某一侧换了源也无人发现」的风险。
#    ⇒ 现在拆开：
#      · SOURCE_EQUIV  = **同一份上游**，只是命名/格式不同 ⇒ 归一后必须四侧齐全
#      · SEMANTIC_ALIKE = **不同上游**，但表达同一意图、去向也相同 ⇒ 只用于"缺侧"判定
#        （即：某侧的这类规则换了个上游名字，不算漂移；但两侧同时换了上游**不会**被这里
#        发现，那是"换源"风险，需人工评审 —— 本判据不声称能守这个）。
#
#    ── 表一：同一上游，不同命名/格式 ──────────────────────────────────
SOURCE_EQUIV = {
    # 同一条 URL：Jinx/main/surge-direct.list ↔ Jinx/main/mihomo-direct.yaml
    # （独立审查逐条比对：47 条内容完全相同）
    "surge-direct": "jinx-cn",
    # 同一 Jinx ads 上游的两种格式（Surge .list ↔ mihomo .yaml）；
    # 3885 条语义等价，只是语法不同（DOMAIN-WILDCARD ↔ DOMAIN-REGEX）
    "surge-ads": "jinx-ads",
    # 同一 AWAvenue 仓库的两个格式变体（Surge 965 行 / Clash 962 行）
    "awavenue-ads-rule-surge-rule-set": "awavenue-ads",
    # `rules/apple_system.list` 头注自述 = Surge 官方内置 SYSTEM 的 2026-09-24 快照
    # ⇒ Surge 用内置、其余三侧用本仓快照，是同一份内容
    "system": "apple-system",
}

#    ── 表二：不同上游，语义相近（去向相同才算对齐）─────────────────────
SEMANTIC_ALIKE = {
    # Apple 更新域：blackmatrix7 `SystemOTA.list` ↔ MetaCubeX `geosite/apple-update`
    "systemota": "apple-update",
    # 国内直连：Loyalsoldier `direct.txt` ↔ MetaCubeX `geosite/cn.mrs`
    #
    # ⚠️ **已知边界（2026-10-18 审查指出，未修但已登记）**：`cn` 这个 canonical 在本表
    #    与 `SIDE_ONLY` 的共同作用下，实际会合并**三个来源**：
    #      ① surge/egern 的 `direct`（Loyalsoldier direct.txt，域名维度）
    #      ② clash/stash 的 `cn`（MetaCubeX geosite/cn.mrs，域名维度）
    #      ③ egern 的 `geoip → CN`（IP 维度，经 norm_source 归一成 `cn`*）
    #    而 `ctgt[s][canon]` 是 `set()`，**只比去向集合、不比来源条数** ⇒
    #    删掉 egern 的任意一条、甚至两条全删，只要还有一条存活且去向相同，就判"齐全"。
    #    实测：W1（只删 geoip CN）/ W2（只删 direct.txt）/ X1（两条都删）均 EXIT 0。
    #
    #    归因：HEAD 版对 W2/X1 **同样漏报**（那时 `direct` 与 `cn` 是两个独立 key，
    #    漏的是 `direct`）⇒ **不是本表引入的回归**，但归一化确实让掩盖面变宽。
    #
    #    ⇒ 若将来要收紧，正解是给 canonical 记「期望来源数」并断言，
    #      而不是把不同维度的 source 硬合并。当前登记为已知边界，不在此处改。
    "direct": "cn",
    # 私有域：Surge 用**内置** `LAN`；Egern 用 blackmatrix7 `Lan/Lan.list`（不是内置）；
    # Clash/Stash 用 MetaCubeX 域名集 `private`
    "lan": "private",
    # Gemini：blackmatrix7 `Gemini.list` ↔ MetaCubeX `geosite/google-gemini`
    "gemini": "google-gemini",
    # Apple 直连域：Loyalsoldier `apple.txt` ↔ MetaCubeX `geosite/apple-cn`
    # ⚠️ 初版注释误写成「blackmatrix7 的 Apple」，全仓并无该集
    "apple": "apple-cn",
    # Anthropic：blackmatrix7 的 Anthropic+Claude **两条** ↔ MetaCubeX `anthropic` 一条
    "claude": "anthropic",
    # YouTube Music：规则集 `YouTubeMusic` ↔ 直写的 `DOMAIN-SUFFIX,music.youtube.com`
    "youtubemusic": "music.youtube.com",
}

# ④ **单侧独有**的规则集：只有某些内核支持这种形态，缺侧是机制决定、不是漂移。
#
#    ⚠️ 三张表的语义**不可混用**（混用会让"缺少的规则"被当成"换了个名字"，掩盖真漂移）：
#      · SOURCE_EQUIV   = 同一份上游，四侧写法不同 ⇒ 归一后**必须四侧齐全**
#      · SEMANTIC_ALIKE = 不同上游但意图相同 ⇒ 只放宽"缺侧"判定，不声称是同一份规则
#      · SIDE_ONLY      = 该形态只有这些内核有 ⇒ 不要求其他侧存在；但**登记项本身
#                         必须仍然存在**（整组删除 = 判负，见下方显式校验）
#
#    每个登记项的值是按**产品线**的 dict：`{"routing": (...), "lazy": (...)}`。
#    某产品线为 `None` = 该产品线本来就没有这条（例如懒人版无 Google/Telegram 分流，
#    故 `geoip-google` / `geoip-telegram` 在 lazy 下不存在是正常的、不该判负）。
SIDE_ONLY = {
    # Clash 系的 IP 归属规则（behavior: ipcidr）。Surge/Egern 用域名集表达同一意图，
    # 但那是**另一个维度**（域名 vs IP），不能算"同一份规则"。故登记为单侧独有。
    # ⚠️ `geoip-google` / `geoip-telegram` **只在 routing 版**有 —— 懒人版没有
    #    Google / Telegram 分流组，这两条自然不存在。故其登记项写成按产品线的
    #    dict（`{"routing": (...)}`），`None` 表示该产品线不存在这条。
    "geoip-cn": {"routing": ("clash", "stash"), "lazy": ("clash", "stash")},
    "geoip-private": {"routing": ("clash", "stash"), "lazy": ("clash", "stash")},
    "geoip-google": {"routing": ("clash", "stash"), "lazy": None},
    "geoip-telegram": {"routing": ("clash", "stash"), "lazy": None},
    # Clash 系额外引的 MetaCubeX AI 全集；Surge/Egern 用自托管 AI.list 覆盖同一批域，
    # 但条目并不逐条相同 ⇒ 单侧独有，不假装等价。
    "category-ai-chat-!cn": {"routing": ("clash", "stash"), "lazy": ("clash", "stash")},
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
#   · filter —— Stash 无 `exclude-filter`，把信息词合进了 filter（见 profiles/stash.md §3.3）
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
#   · format —— mihomo 用 mrs（省内存），Stash 官方只列 yaml/text（见 profiles/stash.md §2）
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

        # ── F5：四侧去向一致 + **四侧齐全**（豁免表外）──────────────────
        #
        # ⚠️ 2026-10-18（外部审查实锤）：原实现有两个洞。
        #
        #   洞一（单侧整条规则消失判绿）：原代码是
        #       present = {s: tgt[s][key] for s in SIDES if key in tgt[s]}
        #       if len(set(present.values())) <= 1: continue
        #   `if key in tgt[s]` 过滤掉了「该侧没有这条规则」的情况 ⇒ 从某一侧删掉整条
        #   规则后，剩下三侧去向仍一致 ⇒ 通过。实测删掉 egern 的完整 `Jinx-Ads` 块
        #   （rules 25→24，YAML 合法）后本判据仍 exit 0。
        #
        #   洞二（读数系统性夸大覆盖面）：原输出「%d 个 source 已核」取的是**并集**大小，
        #   而真正四侧齐全参与比对的只有一小部分（实测 routing 37→13、lazy 18→3）。
        #   读者会按「37 个已核」判断覆盖充分 ⇒ 读数必须改成「齐全 N / 并集 M」。
        #
        # ⇒ 修法：① 先把 source 按 SOURCE_EQUIV（同一上游）+ SEMANTIC_ALIKE（不同上游
        #   但语义相近）归成 canonical key（否则跨内核命名差异会被误判成"缺失"，
        #   24 条误报）；② 再断言 canonical key 必须**四侧齐全**；
        #   ③ 输出把「四侧齐全 / 单侧独有 / 并集」分三类报，不混算。
        raw_tgt = {s: _targets(data[(fam, s)][1]) for s in SIDES}

        def _canon(k):
            return SEMANTIC_ALIKE.get(SOURCE_EQUIV.get(k, k), SOURCE_EQUIV.get(k, k))

        # canonical -> {side: set(targets)}（同一 canonical 下可能有多条 source）
        ctgt = {s: {} for s in SIDES}
        for s in SIDES:
            for k, v in raw_tgt[s].items():
                ctgt[s].setdefault(_canon(k), set()).add(v)

        keys = sorted(set().union(*[set(t) for t in ctgt.values()]))
        mism, missing = [], []
        side_only_cnt = 0

        def _side_only_for(k, fam_):
            """该 key 在**本产品线**下登记的单侧独有集合；None = 本产品线不存在这条。"""
            spec = SIDE_ONLY.get(k)
            if spec is None:
                return False, None
            return True, spec.get(fam_)

        for key in keys:
            holders = [s for s in SIDES if key in ctgt[s]]
            if len(holders) != len(SIDES):
                # 单侧独有的形态（IP 维度 / Clash 系专有集）⇒ 不要求四侧齐全
                registered, only = _side_only_for(key, fam)
                if registered:
                    if only is None:
                        missing.append("%s（本产品线不应存在，实际出现在 %s）"
                                       % (key, sorted(holders)))
                    elif tuple(sorted(holders)) != tuple(sorted(only)):
                        missing.append("%s（实际 %s，登记为 %s —— 登记与实际不符）"
                                       % (key, sorted(holders), sorted(only)))
                    else:
                        side_only_cnt += 1
                    continue
                # 缺侧：若该 key 在豁免表里 ⇒ 豁免是"去向不同"，不是"可以整条不存在"，
                # 故缺侧**不放行**（与下面四侧齐全分支的豁免语义分开）。
                missing.append("%s（仅 %s）" % (key, holders))
                continue
            # 四侧齐全：比去向（去重后应只有一个值）
            present = {s: tuple(sorted(ctgt[s][key])) for s in SIDES}
            if len(set(present.values())) <= 1:
                continue
            # 豁免判定：**必须登记全四侧且逐一相等**（不是只校验登记到的那几侧）。
            # 2026-10-18 独立审查实测：旧的 all() 写法下，把 clash 的 jinx-ads 改成
            # DIRECT（= 关掉广告拦截）仍判绿 —— 只因为 clash 没被登记进豁免表。
            exempt = TARGET_EXEMPT.get(key)
            if exempt and set(exempt) == set(SIDES) \
                    and all(present.get(s) == (t,) for s, t in exempt.items()):
                continue
            mism.append("%s=%s" % (key, present))

        # SIDE_ONLY 的登记项**必须仍然存在**：整组删除时 keys 里就没有它了，
        # 光靠上面的循环永远发现不了（2026-10-18 独立审查实测：两侧都删
        # `geoip-private` 后 F5 判绿，只体现为"单侧独有 5→4"的读数变化）。
        # 只对「本产品线应有」的登记项要求存在（`None` = 本产品线本就没有）。
        for k, spec in SIDE_ONLY.items():
            should = spec.get(fam)
            if should is not None and k not in keys:
                missing.append("%s **整组消失**（本产品线应存在于 %s 单侧独有）"
                               % (k, sorted(should)))

        # ⚠️ 读分数要**分两类报**，别混：
        #    「四侧齐全」只数真正在四侧都出现的；SIDE_ONLY 另计。
        #    上一版把两者加在一起（`or k in SIDE_ONLY`），实测显示 26 而真正齐全只有 21
        #    —— 这正是本判据号称要修的「读数夸大覆盖面」，却用新方式重现了一遍。
        full_cnt = sum(1 for k in keys if all(k in ctgt[s] for s in SIDES))
        if not mism and not missing:
            ok.append("F5 %-7s 四侧规则集去向一致（四侧齐全 %d · 单侧独有 %d · 并集 %d；"
                      "豁免 %d 条刻意去向）"
                      % (fam, full_cnt, side_only_cnt, len(keys), len(TARGET_EXEMPT)))
        else:
            if mism:
                bad.append("F5 %-7s 四侧去向不一致（且不在豁免表内）：%s"
                           % (fam, "；".join(mism[:4])))
            if missing:
                bad.append("F5 %-7s 规则集**缺侧**（该 source 未在四侧齐全出现，"
                           "且未登记等价类/豁免）：%s —— 若确属刻意，加进 SOURCE_EQUIV "
                           "或 TARGET_EXEMPT 并写清理由"
                           % (fam, "；".join(missing[:6])))

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

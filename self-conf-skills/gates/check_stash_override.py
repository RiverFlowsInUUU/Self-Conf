#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stash 覆写：结构、引用与正则判别力。

为什么要有这一项
    本仓的 Stash 覆写（`stash/override/*.stoverride`）是 `clash/override/my_clash*.js`
    的**派生物** —— 同一套组名 / 规则次序 / 防泄露底线，只是换了客户端。
    派生关系天生会漂移：改了 JS 却忘了改 stoverride，两边就悄悄分叉，
    而 Stash 加载失败**不报错**（组空着、规则不生效，面板上只是「看起来少了东西」）。

    本仓已有过一次同类教训：`my_clash.js` 的头注数字长期与实际输出不符，
    直到人工核对才发现。派生文件的漂移同理，必须落成判据。

判据（六条）
    ① YAML 语法可解析 —— 解析不了 Stash 直接拒绝加载
    ② 数组键必须带 `#!replace`
       ⚠️ 这是 Stash 覆写**最容易踩**的一条：官方〈覆写配置（Override）〉规定
         数组类型默认是「把覆写数组**插入到原数组前面**」，不是替换。
         不写 `#!replace` ⇒ 订阅自带的 proxy-groups / rules 残留在前面，
         而规则自上而下首次命中即生效 ⇒ 全部改动被静默架空。
    ③ filter 正则可编译（编译不了 = 配置缺陷，判负而不是放过）
    ④ 组名唯一 + 组间引用可解析（悬空引用 ⇒ 组为空）
    ⑤ 规则引用的规则集 / 出口组都存在；末条为 MATCH
    ⑥ 规则集无孤儿；behavior/format ∈ Stash 官方支持的组合

    另外断言规模：分流版 25 组 / 25 集 / 27 条（= 静态模板 `routing.yaml` 的形态，
    **不是**覆写脚本的 22 组 —— 差的 3 个是倍率子组，脚本做不到分档）。

退出码：0 = 通过 · 1 = 判负 · 2 = 环境/参数问题（文件缺失 / 解析失败）
用法：
    python self-conf-skills/gates/check_stash_override.py [仓库根]
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

try:
    import yaml
except ImportError:
    print("需要 PyYAML：<venv>/Scripts/python -m pip install pyyaml", file=sys.stderr)
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# ⚠️ 官方〈规则集合〉列出的 behavior × format 组合。
#    MRS 未列入「format 参数」一节（第三方站点说支持，但官方正文只写 yaml/text），
#    故本仓只用这两者 —— 任何 Stash 版本都能加载。
OK_BEHAVIOR_FORMAT = {
    ("domain", "yaml"), ("domain", "text"),
    ("ipcidr", "yaml"), ("ipcidr", "text"),
    ("classical", "yaml"), ("classical", "text"),
}

BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "PASS", "COMPATIBLE", "GLOBAL"}

# 文件 → 期望规模。
# ⚠️ 分流版是 **25 组**（不是 22）—— 它与 `clash/profiles/routing.yaml` 的**静态形态**
#    对齐，用的是「倍率三档」结构（Smart → Low Mult./Auto/High Mult.），
#    而 mihomo 覆写脚本做不到分档、只有 22 组。两者差的就是那 3 个倍率子组。
FILES = {
    "stash/override/routing.stoverride": (25, 25, 27),
    "stash/override/lazy.stoverride": (3, 10, 13),
}


def has_replace(raw, key):
    """该顶层数组键是否标注了 `#!replace`。"""
    return bool(re.search(r"^%s:\s*#!replace" % re.escape(key), raw, re.M))


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    if not os.path.isdir(os.path.join(root, "stash", "override")):
        print("❌ 不在仓库根（找不到 stash/override/）—— 环境不达标")
        return 2

    ok, bad = [], []

    for rel, (want_g, want_p, want_r) in sorted(FILES.items()):
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            bad.append("%s 不存在" % rel)
            continue
        raw = io.open(p, encoding="utf-8").read()

        # ① YAML 语法
        try:
            d = yaml.safe_load(raw) or {}
        except Exception as e:                                       # noqa: BLE001
            bad.append("%s YAML 解析失败：%s" % (rel, str(e)[:100]))
            continue
        ok.append("%s YAML 可解析" % rel)

        # ② 数组键必须 #!replace
        for key in [k for k, v in d.items() if isinstance(v, list)]:
            if has_replace(raw, key):
                ok.append("%s `%s: #!replace`" % (rel, key))
            else:
                bad.append("%s 的 `%s` 没写 `#!replace` —— Stash 覆写对数组默认是"
                           "**前置插入**，订阅自带的同名字段会残留在前面，"
                           "改动会被静默架空（官方〈覆写配置〉语法参考）" % (rel, key))

        groups = d.get("proxy-groups") or []
        rp = d.get("rule-providers") or {}
        rules = d.get("rules") or []

        # ③ filter 可编译
        for g in groups:
            flt = g.get("filter")
            if not flt:
                continue
            try:
                re.compile(flt)
            except re.error as e:
                bad.append("%s 组 `%s` 的 filter 无法编译：%s"
                           % (rel, g.get("name"), str(e)[:80]))
        ok.append("%s filter 正则全部可编译（%d 条）"
                  % (rel, sum(1 for g in groups if g.get("filter"))))

        # ④ 组名唯一 + 引用可解析
        names = [g.get("name") for g in groups]
        dup = sorted(n for n in set(names) if names.count(n) > 1)
        if dup:
            bad.append("%s 组名重复：%s" % (rel, dup))
        else:
            ok.append("%s 组名唯一（%d 组）" % (rel, len(names)))
        nameset = set(names)
        dangling = ["%s→%s" % (g.get("name"), m) for g in groups
                    for m in (g.get("proxies") or [])
                    if m not in nameset and m not in BUILTIN_POLICIES]
        if dangling:
            bad.append("%s 组间引用悬空：%s" % (rel, dangling))
        else:
            ok.append("%s 组间引用全部可解析" % rel)

        # ⑤ 规则引用 + 末条 MATCH
        bad_set, bad_out = [], []
        for r in rules:
            parts = [x.strip() for x in r.split(",")]
            if parts[0] == "RULE-SET" and parts[1] not in rp:
                bad_set.append(parts[1])
            pol = parts[-1]
            if pol == "no-resolve" and len(parts) >= 2:
                pol = parts[-2]
            if pol not in nameset and pol not in BUILTIN_POLICIES:
                bad_out.append("%s→%s" % (r[:40], pol))
        if bad_set:
            bad.append("%s 规则引用了不存在的规则集：%s" % (rel, sorted(set(bad_set))))
        else:
            ok.append("%s 规则引用的规则集都存在（%d 条规则）" % (rel, len(rules)))
        if bad_out:
            bad.append("%s 规则的出口策略不存在：%s" % (rel, bad_out))
        else:
            ok.append("%s 规则出口策略都可解析" % rel)
        if rules and rules[-1].startswith("MATCH,"):
            ok.append("%s 末条为 %s" % (rel, rules[-1]))
        else:
            bad.append("%s 末条不是 MATCH（未匹配流量会无出口）：%s"
                       % (rel, rules[-1] if rules else "（空）"))

        # ⑥ 规则集：无孤儿 + behavior/format 合法
        used = {r.split(",")[1].strip() for r in rules if r.startswith("RULE-SET")}
        orphan = sorted(set(rp) - used)
        if orphan:
            bad.append("%s 有未被任何规则引用的规则集：%s" % (rel, orphan))
        else:
            ok.append("%s 规则集无孤儿（%d 份）" % (rel, len(rp)))
        badbf = ["%s=%s/%s" % (k, v.get("behavior"), v.get("format"))
                 for k, v in rp.items()
                 if (v.get("behavior"), v.get("format")) not in OK_BEHAVIOR_FORMAT]
        if badbf:
            bad.append("%s 规则集的 behavior/format 不在 Stash 支持集内：%s"
                       % (rel, badbf))
        else:
            ok.append("%s behavior/format 全部合法" % rel)

        # ⑦ 规模（对齐静态模板形态）
        got = (len(groups), len(rp), len(rules))
        if got == (want_g, want_p, want_r):
            ok.append("%s 规模 %d 组 / %d 集 / %d 条"
                      % ((rel,) + got))
        else:
            bad.append("%s 规模 %d 组 / %d 集 / %d 条，应为 %d / %d / %d"
                       % ((rel,) + got + (want_g, want_p, want_r)))

    print("Stash 覆写结构检查（stash/override/*.stoverride）")
    print("-" * 78)
    for m in ok:
        print("  ✅ %s" % m)
    for m in bad:
        print("  ❌ %s" % m)
    print("-" * 78)
    if bad:
        print("判负 %d 处" % len(bad))
        return 1
    print("通过 %d 项 —— 覆写结构、引用与正则均正常" % len(ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())

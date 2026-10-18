#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判别力回归 —— 注错样例常驻跑，守住「闸门改坏了还能全绿」这个盲区。

为什么需要（本仓已知挂账，见 gates.md §9.3 / §16.4）：
    一道闸门「跑一遍是绿的」证明不了它有效 —— 现役配置永远是好的，
    判据被改坏后照样全绿，直到真出事那天给不出诊断。判别力只能靠
    「喂坏配置、断言判负」来证明。此前仓里只有跨内核的
    `check_region_filters.py` 把判负样例做进了常驻 CI；本闸门把剩下
    4 道**判负样例已人工实测**的闸门补上同等回归：

      1. `check_structure`          —— 插入引用了未定义规则集的规则
      2. `check_min_pair`           —— 往 .min 里加一行规则（内容漂移）
      3. `check_script_sync`        —— 静态 profile 与脚本规则长度不一致
      4. `build_rules.py --check`   —— 真源 .list 有更新、生成物未重跑
      5. `check_ad_caliber`         —— 懒人版的 AD 组被加上 `DIRECT`（口径被改错）
      6. `check_waiver_usage`       —— 造一条不会触发的 `# audit-waive:`（陈旧豁免）

（5/6 是 2026-10-10 补的：那两道闸门本身就是为了「把靠自觉的格子变成机器守」
而新增的，它们同样需要判别力回归 —— 否则将来被改坏（如把口径表写成恒真、
把豁免解析写成恒空集）仍会全绿，等于白加。）

怎么做的（照抄 check_region_filters 的断言口径）：
    临时目录里搭一份最小仓库副本（真仓工作副本一个字节不动），对副本
    注入已知错误，断言「退出码 = 1 且输出含预期标记」两条 —— 因为闸门
    崩了（如 NameError / UnicodeEncodeError）同样以退出码 1 结束，
    只有输出标记能证明它判的是**这条**错。退出码 2 是闸门自己的
    环境失败，不计入判负。

退出码：0 = 全部判负（判别力在位）· 1 = 有闸门没判负（判别力失效，必须查）
       2 = 基线不绿或环境缺失（判据本身有问题，不是判别力问题）
用法：python self-conf-skills/gates/check_negative_fixtures.py
"""

import os
import shutil
import subprocess
import sys
import tempfile

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PY = sys.executable or "python"


def _has_node():
    return shutil.which("node") is not None


def _build_sandbox(dst):
    """把 4 道闸门所需扫描面的最小文件集拷进沙箱。

    只拷会注错、会被读的文件，不拷 .git / 门禁脚本本身
    —— 门禁脚本跑在原仓（保证读到的是当前版本），ROOT 指向沙箱。
    """
    files = [
        "AGENTS.md",                    # lib/paths.py 上溯标志物
        "surge/profiles/routing.conf",  # lib/paths.py 上溯标志物
        "surge/profiles/lazy.conf",
        "surge/profiles/routing.min.conf",
        "surge/profiles/lazy.min.conf",
        "egern/profiles/lazy.yaml",
        "egern/profiles/routing.yaml",
        "egern/profiles/lazy.min.yaml",
        "egern/profiles/routing.min.yaml",
        "clash/profiles/lazy.yaml",
        "clash/profiles/routing.yaml",
        "clash/profiles/lazy.min.yaml",
        "clash/profiles/routing.min.yaml",
        "clash/override/clash-routing.js",
        "clash/override/clash-lazy.js",
        # ⚠️ 2026-10-11：check_min_pair 的对拍面扩到了覆写脚本 4 对 ⇒ 沙箱必须带上，
        #    否则「缺文件判负」让**基线本身**变红（判别力回归前置失败，实测踩出）。
        "clash/override/clash-routing.min.js",
        "clash/override/clash-lazy.min.js",
        "stash/override/stash-routing.stoverride",
        "stash/override/stash-lazy.stoverride",
        "stash/override/stash-routing.min.stoverride",
        "stash/override/stash-lazy.min.stoverride",
        "rules/emby.list", "rules/emby.yaml",
        "rules/apple_system.list", "rules/apple_system.yaml",
        "rules/AI.list", "rules/AI_Domains.yaml",
        "self-conf-skills/lib/paths.py",
        "self-conf-skills/run/clash/build_rules.py",
    ]
    for rel in files:
        src = os.path.join(_ROOT, rel)
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(src, out)

    # ⚠️ 2026-10-18：`check_portability.py` 靠 `git ls-files` 取扫描面，沙箱不是 git 仓
    #    时它会返回 2（前置不达标）⇒ 判别力用例无法验证「`.stoverride` 的 BOM/CRLF」。
    #    故把沙箱初始化成一个最小 git 仓并把拷进去的文件 add 进索引。
    #    只影响沙箱（tempfile.mkdtemp），不碰真仓；失败也不致命（该用例会报 NG 而非崩溃）。
    try:
        subprocess.run(["git", "init", "-q"], cwd=dst, check=True,
                       capture_output=True)
        subprocess.run(["git", "add", "-A", "-f"], cwd=dst, check=True,
                       capture_output=True)
    except Exception as e:                                        # noqa: BLE001
        print("  提示：沙箱 git 初始化失败（%s）—— portability 用例会被跳过" % e)


def _mutate(path, old, new):
    """按字节替换注入错误；注错没命中锚点直接算环境失败（exit 2）。"""
    with open(path, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    if old not in text:
        print("  注错锚点没找到：%s 里的 %r" % (path, old[:60]))
        sys.exit(2)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace(old, new, 1))


def _run(argv):
    p = subprocess.run(argv, capture_output=True)
    out = (p.stdout + p.stderr).decode("utf-8", errors="replace")
    return p.returncode, out


def _case(name, mutate, argv, marker):
    """一条判负用例：注错 → 断言「退出码=1 且输出含标记」两条。"""
    mutate()
    rc, out = _run(argv)
    problems = []
    if rc != 1:
        problems.append("退出码 %d（应为 1）" % rc)
    if marker not in out:
        problems.append("输出无标记 %r" % marker)
    if problems:
        print("  NG %-28s %s" % (name, "；".join(problems)))
        print("       输出尾部：")
        for line in out.strip().splitlines()[-4:]:
            print("       " + line)
        return False
    print("  OK %-28s 判负 exit=1 + 标记 %r" % (name, marker))
    return True


def main():
    print("判别力回归（判负样例常驻）")
    print("-" * 78)

    missing = []
    if not _has_node():
        missing.append("node（check_script_sync 要执行 override 脚本）")
    try:
        import yaml  # noqa: F401
    except ImportError:
        missing.append("pyyaml")
    if missing:
        print("环境缺依赖，无法验证判别力：" + "、".join(missing))
        return 2

    sb = tempfile.mkdtemp(prefix="self-conf-negfix-")
    try:
        _build_sandbox(sb)

        GATES = os.path.join(_ROOT, "self-conf-skills", "gates")
        clash_sb = os.path.join(sb, "clash")

        # ---- 基线：未注错时每道都必须放行，否则判据本身有问题（非判别力问题）
        baselines = [
            ("check_structure",
             [PY, os.path.join(GATES, "clash", "check_structure.py"), clash_sb]),
            ("check_min_pair",
             [PY, os.path.join(GATES, "check_min_pair.py"), sb]),
            ("check_script_sync",
             [PY, os.path.join(GATES, "clash", "check_script_sync.py"), clash_sb]),
            ("build_rules --check",
             [PY, os.path.join(sb, "self-conf-skills", "run", "clash",
                               "build_rules.py"), "--check"]),
            # 2026-10-10 新增的两道，基线同样要在未注错的副本上放行
            ("check_ad_caliber",
             [PY, os.path.join(GATES, "check_ad_caliber.py"), sb]),
            ("check_waiver_usage",
             [PY, os.path.join(GATES, "check_waiver_usage.py"), sb]),
        ]
        for nm, argv in baselines:
            rc, out = _run(argv)
            if rc != 0:
                print("基线不绿：%s 在未注错的副本上退出码 %d —— 判据本身有问题，"
                      "不是判别力问题。输出尾部：" % (nm, rc))
                for line in out.strip().splitlines()[-6:]:
                    print("  " + line)
                return 2
        print("  基线 %d/%d 绿（未注错的副本全部放行）" % (len(baselines), len(baselines)))

        passed = 0

        # 1 · check_structure：规则引用了未定义的规则集
        c1 = _case(
            "check_structure",
            lambda: _mutate(
                os.path.join(clash_sb, "profiles", "lazy.yaml"),
                "  - RULE-SET,Jinx-CN,DIRECT\n",
                "  - RULE-SET,ghost-set,DIRECT\n"),
            baselines[0][1],
            "规则引用了未定义的规则集: ghost-set")
        passed += c1

        # 2 · check_min_pair：.min 里加一行规则（与完整版漂移）
        #    ⚠️ 标记与判据文案同步（2026-10-11：判负输出改为「去注释后第 N 行不同」）
        c2 = _case(
            "check_min_pair",
            lambda: _mutate(
                os.path.join(clash_sb, "profiles", "lazy.min.yaml"),
                "rules:\n",
                "rules:\n  - DOMAIN-SUFFIX,negfix-probe.example,DIRECT\n"),
            baselines[1][1],
            "去注释后第")
        passed += c2

        # 3 · check_script_sync：静态 profile 的规则比脚本少一条
        c3 = _case(
            "check_script_sync",
            lambda: _mutate(
                os.path.join(clash_sb, "override", "clash-lazy.js"),
                '    "RULE-SET,Jinx-CN,DIRECT",\n',
                ""),
            baselines[2][1],
            "长度不同")
        passed += c3

        # 4 · build_rules --check：真源 .list 有更新、生成物未重跑
        c4 = _case(
            "build_rules --check",
            lambda: _mutate(
                os.path.join(sb, "rules", "AI.list"),
                "# NAME: AI_Domains (AI 全量整合集 · Surge ruleset)\n",
                "# NAME: AI_Domains (AI 全量整合集 · Surge ruleset)\nnegfix-probe.example\n"),
            baselines[3][1],
            "已过期")
        passed += c4

        # ── 5–7 · 2026-10-10 新增的三道闸门，同样纳入判别力回归 ───────────
        #    ⚠️ 为什么这三条必须在这里：它们本身就是「补『没有机器守』的格子」而加的
        #    （见各自 docstring）。若不加回归，它们将来被改坏（比如把 AD_CALIBER
        #    写成恒真、把 WAIVED 解析写错成恒空集）仍会**全绿**，等于白加。
        #
        # 5 · AD 组口径：把懒人版 mihomo 的 AD 加上 DIRECT（懒人版不该放行）
        c5 = _case(
            "AD 组口径",
            lambda: _mutate(
                os.path.join(clash_sb, "profiles", "lazy.yaml"),
                "  - name: AD\n    type: select\n    proxies:\n      - REJECT\n",
                "  - name: AD\n    type: select\n    proxies:\n"
                "      - REJECT\n      - DIRECT\n"),
            [PY, os.path.join(GATES, "check_ad_caliber.py"), sb],
            "应为")
        passed += c5

        # 6 · 豁免用量：声明一个**不会触发**的检查号（陈旧豁免）
        c6 = _case(
            "豁免用量",
            lambda: _mutate(
                os.path.join(sb, "surge", "profiles", "lazy.conf"),
                "# audit-waive: 1 加密 DNS 端点保留",
                "# audit-waive: 7 negfix 造一条陈旧豁免\n"
                "# audit-waive: 1 加密 DNS 端点保留"),
            [PY, os.path.join(GATES, "check_waiver_usage.py"), sb],
            "陈旧豁免")
        passed += c6

        # ── 8–10 · 2026-10-18 新增：钉死外部审查实锤的三个「假绿」─────────
        #    ⚠️ 为什么必须补：这三条都属「判据声称覆盖、实际不判」的假绿，
        #    且**全都落在此前的未覆盖集合里**（原回归只覆盖 6/51 道），
        #    所以能长期潜伏而无人发现。补上用例 = 以后改坏了会当场叫。
        #
        # 8 · secrets：往 `.stoverride` 注入 YAML 凭据（password/uuid）
        #    原缺陷：`yaml_ = f.endswith((".yaml",".yml"))` 不认 `.stoverride`
        #    ⇒ 落进 Surge INI 分支、用 `password=` 匹配 YAML 的 `password:`
        #    ⇒ 永远匹配不到 ⇒ 注入真实凭据仍 exit 0（2026-10-18 实锤）。
        c8 = _case(
            "secrets·.stoverride 凭据",
            lambda: _mutate(
                os.path.join(sb, "stash", "override", "stash-routing.stoverride"),
                "dns: #!replace\n",
                "proxies:\n"
                "  - name: negfix-leak\n"
                "    server: negfix-probe.attacker-cdn.net\n"
                "    password: NegfixSuperSecret123\n"
                "dns: #!replace\n"),
            [PY, os.path.join(GATES, "check_secrets.py"), sb],
            "凭据字段")
        passed += c8

        # 9 · portability：给 `.stoverride` 加 UTF-8 BOM
        #    原缺陷：`.stoverride` 不在 `TEXT_EXT` ⇒ `is_text()` 返回 False
        #    ⇒ E2/E2b/E3 三项字节层判据**完全不覆盖 Stash**（2026-10-18 实锤）。
        #    ⚠️ 这条不能用 _mutate（它按 UTF-8 文本读写，写不回 BOM），故直接写字节。
        def _add_bom():
            p = os.path.join(sb, "stash", "override", "stash-lazy.stoverride")
            with open(p, "rb") as f:
                raw = f.read()
            if raw[:3] == b"\xef\xbb\xbf":
                print("  注错锚点异常：该文件已有 BOM")
                sys.exit(2)
            with open(p, "wb") as f:
                f.write(b"\xef\xbb\xbf" + raw)
        c9 = _case(
            "portability·.stoverride BOM",
            _add_bom,
            [PY, os.path.join(GATES, "check_portability.py"), sb],
            "BOM")
        passed += c9

        # 10 · 四侧同步：删掉 egern 的整条域名规则（domain_suffix）
        #     原缺陷（两层）：
        #       a) `if key in tgt[s]` 让「单侧整条规则消失」判绿；
        #       b) `build_ir._load_egern_rules` 只对 rule_set/geoip 取 source
        #          ⇒ egern 的 domain_suffix 类规则 source 恒为 None、被直接跳过。
        #     2026-10-18 实锤：删掉 2 条 domain_suffix（13→11，YAML 合法）仍 exit 0，
        #     而那两条正是 2026-10-13 发版的核心变更。
        c10 = _case(
            "四侧同步·egern 缺域名规则",
            lambda: _mutate(
                os.path.join(sb, "egern", "profiles", "lazy.yaml"),
                "    match: xn--ngstr-lra8j.com\n    policy: Proxy\n",
                ""),
            [PY, os.path.join(GATES, "check_four_way_sync.py"), sb],
            "缺侧")
        passed += c10

        # 11 · secrets：Surge `[Proxy]` 行里的 `token=`（等号形态）
        #     ⚠️ 这条专治「修 A 引入 B」：2026-10-18 我给冒号形态加了"必须在 URL 语境"
        #     的过滤，结果把等号形态也一并收紧了 —— 而 Surge 的行形态
        #     `NAME = http, host, port, ..., token=xxx` **不含 `://`** ⇒ 整类漏判。
        #     独立审查当场抓出（注错后新版 EXIT 0、HEAD 版 EXIT 1）。
        #     现在等号/冒号分开判：等号全文判、冒号按行判。本用例钉死等号那条。
        c11 = _case(
            "secrets·Surge token= 形态",
            lambda: _mutate(
                os.path.join(sb, "surge", "profiles", "routing.conf"),
                "\n[Proxy Group]\n",
                "\nPROXY-NEGFIX = http, 192.0.2.1, 8080, token=NegfixRealToken12345\n"
                "\n[Proxy Group]\n"),
            [PY, os.path.join(GATES, "check_secrets.py"), sb],
            "token")
        passed += c11

        # 12 · 四侧同步：把 clash 侧的广告规则去向改成 DIRECT（= 关掉广告拦截）
        #     ⚠️ 这条守的是「豁免必须登记全四侧」。初版豁免表只写了 surge/egern 两侧，
        #     判定用 `all(... for s,t in exempt.items())` 只校验那两侧 ⇒ clash/stash
        #     可被任意改动而判绿（独立审查实测）。现在四侧全登记 + 全字典相等语义。
        c12 = _case(
            "四侧同步·clash 广告改 DIRECT",
            lambda: _mutate(
                os.path.join(sb, "clash", "profiles", "routing.yaml"),
                "  - RULE-SET,Jinx-Ads,AD\n",
                "  - RULE-SET,Jinx-Ads,DIRECT\n"),
            [PY, os.path.join(GATES, "check_four_way_sync.py"), sb],
            "jinx-ads")
        passed += c12

        # ⚠️ 用例总数从用例本身派生，别写魔数：原先写死 `6`，加用例时必须同步改两处
        #    （`passed == 6` 与 `6 - passed`），漏改一处就会出现「明明全过却判负」。
        total = sum(1 for _ in (c1, c2, c3, c4, c5, c6, c8, c9, c10, c11, c12))
        print("\nTOTAL: %d discriminating, %d not" % (passed, total - passed))
        return 0 if passed == total else 1
    finally:
        shutil.rmtree(sb, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

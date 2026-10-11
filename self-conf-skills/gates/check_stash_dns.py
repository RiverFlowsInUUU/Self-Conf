#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stash 覆写的 DNS 防「解析超时」判据 —— 端点必须大陆**直连可达**。

为什么需要它（2026-10-11 真机事故）
────────────────────────────────────
用户症状：Apple 天气 / App Store 打不开，日志刷
    connect error: resolve failed: 46-courier2.push.apple.com (A: resolve timeout…)
两类配置（本仓 stash 覆写、以及把 clash 模板直接导入 Stash）**同时**复现。

根因是官方文档里两句容易被忽略的话（〈内置 DNS 服务〉）：
    「默认情况下，Stash 发出的 DNS 查询均会**直接出站**，而不经由任何代理规则转发。」
    「所有 DNS 请求将会**直接发送到服务器，不经过任何代理**。」

⇒ **Stash 里每一个 DNS 端点都是「裸直连」发出的**。所以：
    · `nameserver`            —— 写境外 DoH（1.1.1.1 / 8.8.8.8）⇒ 大陆直连超时 ⇒ resolve timeout
    · `nameserver-policy` 的值 —— 同理
    · `proxy-server-nameserver` —— 同理（官方：用独立查询链路、不跟随代理规则）

而 mihomo 侧**看起来**可以写境外 DoH，是因为它有 `respect-rules: true`
（DNS 查询跟随路由规则、可走代理）+ `direct-nameserver`（专管 DIRECT 域名的国内端点）。
⚠️ **`respect-rules` 是 mihomo 独有、Stash 不认识**（Stash 的对应物叫 `follow-rule`，
   且官方不建议开）⇒ 把 clash 模板原样导入 Stash 时，这句被**静默忽略**，
   1.1.1.1 就变成裸直连 ⇒ 同样超时。这就是「clash 模板导入 Stash 也坏」的原因。

⭐ 键映射（本判据的核心）：
    mihomo `direct-nameserver`（国内端点，管 DIRECT 域名）＝ Stash **主 `nameserver`**
    mihomo 主 `nameserver`（境外，靠 respect-rules 走代理）在 Stash 侧**无对应物**

断言
────
D1  `nameserver` 必须存在且非空（缺它 ⇒ 无解析器）
D2  ⭐ `nameserver` 不得含「大陆不可直连」的知名境外端点 —— **本判据的主判据**
D3  `nameserver-policy` 的每个值都不得含境外端点（它同样是裸直连）
D4  `proxy-server-nameserver` 必须存在（鸡蛋问题：连节点前还没有代理可用）
D5  `proxy-server-nameserver` 不得含境外端点
D6  端点不得是**明文** DNS（`udp://` / 裸 IP / `http://`）—— 明文会被运营商劫持
D7  `default-nameserver` 只能写 IP 或 `system`（官方：仅支持 IP）

为什么用「境外端点黑名单」而不是「白名单」
    黑名单精确、不误报：只有确实不可直连的知名端点才判负；
    新增的国内端点不会被误杀（本仓端点会演进，白名单必然过期）。

退出码：0 = 全部成立 · 1 = 有判负 · 2 = 前置不达标（文件缺失/解析失败）
用法：python self-conf-skills/gates/check_stash_dns.py [仓库根]
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
    print("需要 PyYAML", file=sys.stderr)
    raise SystemExit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# ── D2/D3/D5 的判据面：大陆**不可直连**的知名公共解析器 ──────────────────
#
# ⚠️ 为什么这些不能出现在 Stash 的任何 DNS 端点上：
#    Stash 的 DNS 查询**不经代理**（官方原文，见 docstring）⇒ 在大陆网络下
#    连不上它们 ⇒ 所有依赖它们的域名 `resolve timeout`。
# ⚠️ 本表**只**收「确定不可直连」的知名端点 —— 宁可漏判也不误杀国内端点。
OVERSEAS_DNS = (
    "1.1.1.1", "1.0.0.1",                      # Cloudflare
    "8.8.8.8", "8.8.4.4",                      # Google
    "9.9.9.9", "149.112.112.112",              # Quad9
    "208.67.222.222", "208.67.220.220",        # OpenDNS
    "dns.google", "dns.cloudflare.com", "cloudflare-dns.com",
    "one.one.one.one",
    "dns.quad9.net", "doh.opendns.com",
    "dns.adguard.com", "dns.adguard-dns.com",
    "dns.nextdns.io", "test.dns.nextdns.io",
    "dns.sb", "dot.pub",                       # dot.pub 是 doh.pub 的 DoT 同族，端点不同
    "unfiltered.adguard-dns.com",
)

FILES = ("stash/override/routing.stoverride", "stash/override/lazy.stoverride")


def _endpoints(val):
    """把 nameserver-policy 的值（字符串 / 列表）摊平成端点列表。"""
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return [str(x) for x in val]
    return []


def _hit_overseas(ep):
    """该端点是否命中境外黑名单（按主机名或 IP 前缀匹配）。"""
    s = str(ep).strip().strip("'\"")
    low = s.lower()
    for bad in OVERSEAS_DNS:
        b = bad.lower()
        # IP 用「词边界」匹配，避免 1.1.1.10 误命中 1.1.1.1
        if re.match(r"^[\d.]+$", b):
            if re.search(r"(?<![\d.])" + re.escape(b) + r"(?![\d.])", low):
                return bad
        elif b in low:
            return bad
    return None


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    if not os.path.isdir(os.path.join(root, "stash", "override")):
        print("❌ 前置不达标：找不到 stash/override/")
        return 2

    ok, bad = [], []

    for rel in FILES:
        p = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            print("❌ 前置不达标：%s 不存在" % rel)
            return 2
        try:
            d = (yaml.safe_load(io.open(p, encoding="utf-8").read()) or {}).get("dns") or {}
        except Exception as e:                                        # noqa: BLE001
            print("❌ 前置不达标：%s 解析失败 %s" % (rel, str(e)[:80]))
            return 2

        # D1 主 nameserver 存在
        ns = d.get("nameserver") or []
        if not ns:
            bad.append("%s D1 缺 `nameserver`（没有解析器）" % rel)
        else:
            # D2 ⭐ 主判据
            hits = [(_hit_overseas(e), e) for e in ns]
            hits = [(b, e) for b, e in hits if b]
            if hits:
                bad.append("%s D2 `nameserver` 含大陆无法直连的境外端点：%s —— "
                           "Stash 的 DNS 查询**不经代理**（官方原文），裸直连它们必然 "
                           "resolve timeout。应改成国内端点（如 %s）"
                           % (rel, [e for _, e in hits],
                              "https://doh.18bit.cn/dns-query"))
            else:
                ok.append("%s D2 nameserver 全部为大陆可达端点：%s" % (rel, ns))
            # D6 必须加密
            plain = [e for e in ns if re.match(r"^(udp://|tcp://|http://)|^[\d.]+$", str(e).strip())]
            if plain:
                bad.append("%s D6 `nameserver` 含明文端点（会被运营商劫持）：%s" % (rel, plain))
            else:
                ok.append("%s D6 nameserver 全部为加密端点" % rel)

        # D3 nameserver-policy 的值也不得含境外端点
        nsp = d.get("nameserver-policy") or {}
        phits = []
        for key, val in nsp.items():
            for e in _endpoints(val):
                b = _hit_overseas(e)
                if b:
                    phits.append("%s -> %s" % (key, e))
        if phits:
            bad.append("%s D3 `nameserver-policy` 含境外端点（同样是裸直连）：%s"
                       % (rel, phits))
        elif nsp:
            ok.append("%s D3 nameserver-policy 端点全部为大陆可达（%d 条 policy）"
                      % (rel, len(nsp)))

        # D4 / D5 proxy-server-nameserver
        psn = d.get("proxy-server-nameserver") or []
        if not psn:
            bad.append("%s D4 缺 `proxy-server-nameserver` —— 代理节点自己的域名会走主 "
                       "nameserver（鸡蛋问题），失败时退回系统明文 DNS" % rel)
        else:
            phits2 = [e for e in psn if _hit_overseas(e)]
            if phits2:
                bad.append("%s D5 `proxy-server-nameserver` 含境外端点：%s"
                           % (rel, phits2))
            else:
                ok.append("%s D5 proxy-server-nameserver 为大陆可达端点：%s" % (rel, psn))

        # D7 引导解析器只能 IP / system
        dns_default = d.get("default-nameserver") or []
        baddefault = [e for e in dns_default
                      if not re.match(r"^[\d.]+$|^\[|^system$", str(e).strip())]
        if baddefault:
            bad.append("%s D7 `default-nameserver` 只能是 IP 或 system（官方）：%s"
                       % (rel, baddefault))
        elif dns_default:
            ok.append("%s D7 default-nameserver 合规：%s" % (rel, dns_default))

    print("Stash 覆写 DNS 判据（端点必须大陆直连可达）")
    print("-" * 78)
    for m in ok:
        print("  ✅ %s" % m)
    for m in bad:
        print("  ❌ %s" % m)
    print("-" * 78)
    if bad:
        print("判负 %d 处 —— 见本文件 docstring 的官方原文与键映射" % len(bad))
        return 1
    print("通过 %d 项 —— DNS 端点全部大陆可达，不会 resolve timeout" % len(ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())

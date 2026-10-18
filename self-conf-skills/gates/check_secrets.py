#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""占位符 / 凭据纪律扫描（自原 self-conf-skills/gates/surge/architecture.sh ① 提炼，2026-09-27 精简）。

本仓的 profiles 是**脱敏模板**：节点地址必须是 RFC 5737 文档段 / example.com，
凭据必须是 REPLACE_WITH_*，订阅 URL 的 token/key/sub 参数值必须含 REPLACE_WITH。
真实值一旦推上公开仓库就不可回收 —— 这是本仓最严重的一类泄露。

扫描面 = 全仓 walk 到的 `*.conf` / `*.yaml` / `*.yml` / **`*.stoverride`（Stash）**
（跳过 `.` 开头目录与 node_modules / __pycache__；故意不用 git ls-files —— 未提交的
本地工作副本正是这道纪律要拦的东西）。注释行不判（说明性文字不是泄露），
但"禁止的敏感串"与订阅 token 两类连注释一起判（藏在注释里同样是残留）。

⚠️ 扫描面**与解析分支是两件事**，两者都必须覆盖同一批形态：
  · 扫描面 = `scan_targets()` 的扩展名表（+ `KNOWN_FORMS` 断言）
  · 解析分支 = `YAML_FORM_EXT`（YAML 凭据正则 vs Surge INI 正则）
  2026-10-11 只补了前者、2026-10-18 才补后者 —— 期间 Stash 的凭据纪律**形同虚设**
  （注入真实 `password:` / `uuid:` 仍判绿）。两条断言分别守这两件事，别再只补一半。

用法：`python self-conf-skills/gates/check_secrets.py [仓库根]`
（仓库根默认取本文件位置往上两级；可传参以便在沙箱副本上注错验证）
退出码：0 全过 · 1 有判负 · 2 前置不达标（扫不到当前版 profile）
"""
import os
import re
import sys

# 仓库定位：靠标志物上溯，不依赖目录层数（见 self-conf-skills/lib/paths.py）
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '../lib'))
from paths import repo_root as _repo_root  # noqa: E402


try:
    for _s in (sys.stdout, sys.stderr):
        _s.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = _repo_root()
# RFC 5737 文档段 + mihomo 的 fake-ip 保留段（198.18.0.0/15，RFC 6815）。
# 后者是整合 mihomo 内核后新增的：fake-ip-range 默认 198.18.0.1/16，
# 对 Surge / Egern 而言是陌生段，不加入就会被误判成真实 IP。
DOC_NETS = ("192.0.2.", "198.51.100.", "203.0.113.", "198.18.")
ALLOWED_DOMAINS = (
    "example.com", "example.net", "example.org",
    "sub.example.com", "cdn-relay.example.com",
    "connect.rom.miui.com", "www.gstatic.com",
    "raw.githubusercontent.com", "cdn.jsdelivr.net",
    "github.com", "api.github.com", "objects.githubusercontent.com",
    "www.google.com", "g.cn", "google.cn",
    "apple.com", "Surge", "Jinx", "ACL4SSR", "Loyalsoldier", "adysec",
    "blackmatrix7", "nintendo.net", "playstation.net", "xboxlive.com",
    "pool.ntp.org", "market.xiaomi.com", "home.arpa",
)
FORBIDDEN_SUBSTRINGS = [
    # 旧仓教训黑名单：只收来历可考的真实泄露串（2026-09-29 外部审查时清理过一次，
    # 移除了无法确证来历的 cloudflare-cdn.com —— 禁串条目必须条条有据，否则是哑弹）
    "tange365.com",
    "wangxinyu",
]
# ⚠️ 2026-10-18：TOKEN 判据要**按形态分两条**，不能合成一条。
#
#   洞的来历：原实现只有 `\s*=\s*`（等号），而 Stash / mihomo 的 YAML 写的是
#   `token: xxx`（冒号）⇒ `.stoverride` 里的订阅 token 永远匹配不到。
#   修的时候我一度合成 `[:=]` 一条正则、并给整条判据加了「必须在 URL 语境」的过滤，
#   结果**反而开了一个新洞**（独立审查当场抓出）：
#     Surge 的 `[Proxy]` 行形态是 `NAME = http, host, port, ..., token=xxx`，
#     这一行**不含 `://`** ⇒ 加了 URLISH 过滤之后，整类 Surge 凭据泄露变成判绿。
#     实测注错 `PROXY-LEAK = http, 192.0.2.1, 8080, token=RealTokenAbc1234567890`
#     → 新版 EXIT 0（漏），HEAD 版 EXIT 1（能抓）。这就是「修 A 引入 B」。
#
#   ⇒ 正解：两种形态**各自保留最宽的判别**：
#     · 等号形态 = Surge/INI 的权威写法 ⇒ **全文判、不加任何语境限制**（维持原口径）
#     · 冒号形态 = YAML 写法 ⇒ 只在**像订阅地址的行**上判，避免误伤普通 YAML 键
#       （`key: some-value` / `sub: another-value` 实测会被无条件判负）
TOKEN_EQ_RE = re.compile(r"(?:token|key|sub)\s*=\s*([A-Za-z0-9_\-]{6,})", re.I)
TOKEN_COLON_RE = re.compile(r"(?:token|key|sub)\s*:\s*([A-Za-z0-9_\-]{6,})", re.I)
# 冒号形态的行级语境：该行必须像订阅地址/订阅声明，否则可能只是普通 YAML 键
COLON_CTX = ("://", "subscribe", "policy-path", "urls:", "url:")
_IPV4 = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")
KNOWN_IPS = {
    "223.5.5.5", "119.29.29.29", "1.1.1.1", "8.8.8.8", "8.8.4.4",
    "1.0.0.1", "9.9.9.9", "208.67.222.222", "114.114.114.114",
    "223.6.6.6", "1.12.12.12", "120.53.53.53",
    "0.0.0.0", "127.0.0.1",
}
YAML_CRED_KEYS = ("password", "username", "uuid", "secret", "obfs-password", "credential")
YAML_CRED_RE = re.compile(r"^\s*(?:-\s+)?(%s)\s*:\s*(.+)$" % "|".join(YAML_CRED_KEYS), re.M)
YAML_SNI_RE = re.compile(r"^\s*(?:-\s+)?(sni|servername)\s*:\s*(.+)$", re.M)
PLACEHOLDER_VALS = ("REPLACE_WITH_",)

# ⚠️ 2026-10-18（外部审查实锤）：**按扩展名判「是不是 YAML」曾把 Stash 判成 Surge**。
#    原写法 `yaml_ = f.endswith((".yaml", ".yml"))` ⇒ `.stoverride` 落到 **Surge INI 分支**，
#    用 `password\s*=\s*`（等号）去匹配 YAML 的 `password:`（冒号）⇒ 永远匹配不到：
#    实测把真实节点 + `password: SuperSecretRealPass123` + `uuid: ...` 写进
#    `stash/override/stash-routing.stoverride`，本判据仍报「22 个 conf/yaml 全过」exit 0；
#    同一份内容写进 `egern/profiles/lazy.yaml` 则判负 3 处。
#    ⇒ 这是「修了扫描面、没修判据本体」的半修（2026-10-11 只补了 walk 的扩展名表），
#      比完全不修更危险 —— 它给出的是「已覆盖」的假信号。
#    ⇒ 正解：**按形态而不是按扩展名**判定，且形态表与 scan_targets 的扩展名表同源。
YAML_FORM_EXT = (".yaml", ".yml", ".stoverride")


def strip_c(s, yaml_=False):
    """去掉整行注释与行尾注释。YAML 只认 `#`；行首空白必须保留（YAML 层级）。"""
    if s.lstrip().startswith("#") or (not yaml_ and s.lstrip().startswith(";")):
        return ""
    marks = "#" if yaml_ else "#;"
    for i in range(1, len(s)):
        if s[i] in marks and s[i - 1] in " \t":
            return s[:i].rstrip()
    return s.rstrip()


def scan_targets(root):
    """全仓 walk 出要扫的配置。

    ⚠️ 2026-10-11：**扩展名表曾漏 `.stoverride`**（Stash 覆写）——
       它写成 `(".conf", ".yaml", ".yml")`，于是 Stash 的配置**完全不进扫描**：
       实测往 `stash/override/stash-routing.stoverride` 注入 `token=AbcDef1234567890`
       与外部仓 URL，本判据**判绿**。这是「加了一侧却漏改扫描面」的典型，
       也是安全判据上最不该有的洞（覆写脚本同样会含订阅地址与节点）。
    ⇒ 教训：**按扩展名枚举的扫描面，加新形态时必须同步扩展名表**。
       本仓的形态现为：`.conf`（Surge）· `.yaml`（Egern/mihomo）·
       **`.stoverride`（Stash）** · 以及将来可能的新形态。
       为防止再漏，下面同时断言「已知形态」都至少覆盖到一个文件（见 main）。
    """
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not d.startswith(".")
                  and d not in ("node_modules", "__pycache__")]
        for fn in sorted(fns):
            if not fn.endswith((".conf", ".yaml", ".yml", ".stoverride")):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            tier = ("FIXTURE" if rel.startswith("self-conf-skills/gates/") else "LIVE")
            out.append((tier, rel, p))
    return sorted(out)


def main():
    fails = []
    # ⚠️ 2026-10-18：原为 `scan_targets(ROOT)` —— **硬编码真实仓库根**，不理会 argv。
    #    后果：本判据**无法在沙箱副本上被注错验证**（注错发生在副本、判据去扫真仓），
    #    于是它既进不了 `check_negative_fixtures` 的判别力回归，也就没人能证明它真的会判负。
    #    这正是「判据声称覆盖、实际无法证伪」的一种。现改为可传根，与其余判据一致。
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    root = os.path.abspath(root)
    scan = scan_targets(root)
    live = [x for x in scan if x[0] == "LIVE"]
    if not live:
        print("❌ 全仓 walk 不到任何当前版 profile —— 目录被挪走了，这**不是**\"没有敏感串\"")
        return 2

    # ⭐ 覆盖形态断言（2026-10-11 新增）：每一种**已知交付形态**都至少要覆盖到一个文件。
    #
    #    为什么要有它：本判据曾因**扩展名表漏 `.stoverride`** 而完全跳过 Stash 配置
    #    （实测注入假密钥仍判绿）。而「扩展名表」这种写法**天生会漏** ——
    #    加新形态的人不一定会想到这里。故用一条断言把「漏」变成**判据会叫**：
    #    你新增一种形态却没进扩展名表 ⇒ 它 walk 不到 ⇒ 这里判负。
    #
    #    ⚠️ 加新形态时**必须同时**：① 扩展名表加后缀 ② 下面加期望项（写清该形态属于哪一侧）。
    KNOWN_FORMS = {
        ".conf": "Surge（`surge/profiles/*.conf`）",
        ".yaml": "Egern / mihomo（`*/profiles/*.yaml`）",
        ".stoverride": "**Stash**（`stash/override/*.stoverride`）",
    }
    for ext, who in KNOWN_FORMS.items():
        if not any(x[1].endswith(ext) for x in scan):
            fails.append("覆盖形态缺失：没有任何 `*%s` 进入扫描面，但它是已知交付形态 —— "
                         "%s。⇒ 要么扩展名表漏了它，要么该侧配置被挪走/删除。"
                         "**新加一侧时，扩展名表与 KNOWN_FORMS 必须同步**" % (ext, who))

    # ⭐ 解析分支断言（2026-10-18 新增）：**YAML 形态的扩展名必须走 YAML 凭据分支**。
    #
    #    为什么要有它：`KNOWN_FORMS` 那条断言只保证「文件进了扫描面」，
    #    **不保证它进了正确的解析分支**。2026-10-11 补了 `.stoverride` 的扩展名表，
    #    但 `yaml_` 仍只认 `.yaml/.yml` ⇒ Stash 落进 Surge INI 分支、凭据正则不执行
    #    ⇒ 实测注入真实 password/uuid 仍 exit 0。这正是「修了扫描面、没修判据本体」。
    #    ⇒ 把「形态 ∈ 扫描面」与「形态 ∈ YAML 分支」两件事绑死：任一 YAML 形态的
    #      扩展名若不在 YAML_FORM_EXT 里，这里判负。
    YAML_FORMS = (".yaml", ".yml", ".stoverride")
    for ext in YAML_FORMS:
        if ext not in YAML_FORM_EXT:
            fails.append("解析分支缺失：`%s` 是 YAML 形态，但不在 `YAML_FORM_EXT` 里 ⇒ "
                         "它会落进 Surge 的 INI 分支，`password:` / `uuid:` / `secret:` "
                         "这些 YAML 凭据正则**根本不会执行**（2026-10-18 实锤过的假绿）。"
                         "**加 YAML 形态时必须同步 YAML_FORM_EXT**" % ext)

    for tier, f, path in scan:
        yaml_ = f.endswith(YAML_FORM_EXT)
        tag = "%s %s" % (tier, f)
        try:
            raw_text = open(path, encoding="utf-8").read()
        except UnicodeDecodeError:
            fails.append(f"{tag}: 非 UTF-8 ⇒ 占位符纪律读不了（按未审处理）")
            continue
        text = "\n".join(strip_c(l, yaml_) for l in raw_text.splitlines())

        for bad in FORBIDDEN_SUBSTRINGS:
            if bad in raw_text:
                fails.append(f"{tag}: 出现禁止的敏感串 `{bad}`")

        for ip in set(_IPV4.findall(text)):
            if ip.startswith(DOC_NETS) or ip in KNOWN_IPS:
                continue
            fails.append(f"{tag}: 出现非占位 IPv4 `{ip}`（必须用文档段 192.0.2.x / 198.51.100.x / 203.0.113.x，或 mihomo fake-ip 段 198.18.x）")

        if yaml_:
            for m in YAML_CRED_RE.finditer(text):
                val = m.group(2).strip().strip("\"'")
                if not val or val.startswith(PLACEHOLDER_VALS):
                    continue
                fails.append(f"{tag}: 凭据字段 `{m.group(1)}` 的值不是占位符（`{val[:24]}…`）")
            for m in YAML_SNI_RE.finditer(text):
                val = m.group(2).strip().strip("\"'")
                if not val or val.startswith(PLACEHOLDER_VALS) or val.endswith("example.com"):
                    continue
                fails.append(f"{tag}: sni 的值不是占位符（`{val}`）")
        else:
            for m in re.finditer(r"(password|username|auth)\s*=\s*\"?([^,\"\n]+)", text):
                val = m.group(2).strip()
                if val.startswith("REPLACE_WITH_"):
                    continue
                fails.append(f"{tag}: 凭据字段 `{m.group(1)}` 的值不是占位符（`{val[:24]}…`）")
            for m in re.finditer(r"sni\s*=\s*([^,\n]+)", text):
                val = m.group(1).strip()
                if val.startswith("REPLACE_WITH_") or val.startswith(DOC_NETS) \
                        or val.endswith("example.com"):
                    continue
                fails.append(f"{tag}: sni 的值不是占位符（`{val}`）")

        # ① 等号形态（Surge / INI 的权威写法）：**全文判、不加语境限制**。
        #    ⚠️ 这里刻意保持"宽"：`NAME = http, host, port, ..., token=xxx` 这种行
        #    不含 `://`，一旦加语境过滤就会整类漏掉（2026-10-18 独立审查实测的回归）。
        for m in TOKEN_EQ_RE.finditer(raw_text):
            val = m.group(1)
            if "REPLACE_WITH" in val.upper():
                continue
            line_no = raw_text.count("\n", 0, m.start()) + 1
            fails.append(f"{tag}:{line_no}: 出现疑似真实 token（`{val[:8]}…`）"
                         f"—— 必须写成 REPLACE_WITH_YOUR_TOKEN")

        # ② 冒号形态（YAML 写法）：只在**像订阅地址的行**上判，避免误伤普通 YAML 键。
        #    `key: some-value` / `sub: another-value` 这类普通键实测会被无条件判负，
        #    故要求同一行含 COLON_CTX 之一。
        for lineno, line in enumerate(raw_text.splitlines(), 1):
            for m in TOKEN_COLON_RE.finditer(line):
                val = m.group(1)
                if "REPLACE_WITH" in val.upper():
                    continue
                if not any(k in line for k in COLON_CTX):
                    continue
                fails.append(f"{tag}:{lineno}: 订阅地址里出现疑似真实 token"
                             f"（`{val[:8]}…`）—— 必须写成 REPLACE_WITH_YOUR_TOKEN")

        if yaml_:
            in_proxies = False
            for i, line in enumerate(text.splitlines(), 1):
                if line.startswith("proxies:"):
                    in_proxies = True
                    rest = line.split(":", 1)[1].strip()
                    if rest not in ("", "[]"):
                        fails.append(f"{tag}:{i}: `proxies:` 内联了非空值 —— 模板不得携带节点")
                    continue
                if in_proxies and line and not line[0].isspace() and not line.startswith("-") \
                        and ":" in line:
                    in_proxies = False
                if not in_proxies:
                    continue
                m = re.search(r"\b(?:server|host)\s*[:=]\s*[\"']?([^\"'\s,]+)", line)
                if not m:
                    continue
                srv = m.group(1)
                if _IPV4.match(srv):
                    if not (srv.startswith(DOC_NETS) or srv in KNOWN_IPS):
                        fails.append(f"{tag}:{i}: 节点 `server` 是非占位 IPv4 `{srv}`")
                    continue
                if srv.startswith("["):
                    continue
                if not any(a in srv for a in ALLOWED_DOMAINS):
                    fails.append(f"{tag}:{i}: 节点主机名 `{srv}` 不在允许清单内")
        else:
            in_proxy = False
            for i, line in enumerate(text.splitlines(), 1):
                s = line.strip()
                if s.startswith("[Proxy]"):
                    in_proxy = True
                    continue
                if s.startswith("[") and in_proxy:
                    in_proxy = False
                if not in_proxy or not s or "=" not in s:
                    continue
                rhs = s.split("=", 1)[1]
                p = [x.strip() for x in rhs.split(",")]
                if len(p) < 2:
                    continue
                server = p[1]
                if _IPV4.match(server) or server.startswith("["):
                    continue
                if not any(a in server for a in ALLOWED_DOMAINS):
                    fails.append(f"{tag}:{i}: [Proxy] 里的节点主机名 `{server}` 不在允许清单内")

    if fails:
        print("❌ 占位符 / 凭据纪律判负 %d 处：" % len(fails))
        for f_ in fails:
            print("   · " + f_)
        return 1
    # 文案别再写「conf/yaml」：扫描面已含 `.stoverride`（Stash），共 4 种形态。
    print("✅ 占位符 / 凭据纪律：%d 个配置文件全过（当前版 %d · 夹具 %d）"
          % (len(scan), len(live), len(scan) - len(live)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

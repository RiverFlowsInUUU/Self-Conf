# -*- coding: utf-8 -*-
"""Release 断言 —— 远端发布状态与本仓当前版本是否一致。

模型（2026-10-08 改革后）：**当前版本 → 一张 Release**（tag = `vYYYY-MM-DD` = 发布日）。
旧模型从 git 历史重建全部历史 Release，为此需要归档目录 + 手写历史表 + 日期口径文档；
现已全部移除。本文件相应只剩 5 条断言，且都对着「现役」判，不考古。

判据
────
R1 tag 形状 `^vYYYY-MM-DD$` 且唯一
R2 资产名 ∈ 固定名集合（三内核 × 两产品线 × 完整/min）且不含版本号样式
R3 最新那张 Release 的资产 = 当前应发的 12 件（不多不少）
R4 最新那张 Release 的正文含当前三内核版本号
R5 仓库级 Latest 指针指向最新那张 Release
R6 本地 profile 必须已发出（防「改了配置没发版」整类漏发）
   R6a 若本地 profile 与已发布资产不一致 ⇒ 当日 Release 必须存在
   R6b 且该 Release 的资产与本地 profile 逐件一致（改了没重发即判负）
   ⚠️ 两者**只在「本地 profile 确实与已发布资产不一致」时才要求 Release** ——
      只改脚本/文档的日子本地 profile 没变，**不需要**当日 Release（ops.md §2）。

⚠️ R6 的存在理由（2026-10-10 实测事故）：
    R1–R5 全部是「对着**已有** Release 判」。`newest = max(releases)` 取的是
    远端现有 Release 里最新的那张 —— 于是只要**一张新 Release 都没建**，
    `newest` 就还停在旧的那张，而旧那张与旧版本号天然自洽 ⇒ **R3/R4 全绿**。
    实测：连续 4 个功能提交（IR / P1 可移植性 / 懒人版 Play 修复 / 升号）都没发版，
    `verify_all` 一路全绿，直到升号让「现役版本号 ≠ 旧 Release 正文」才判负 ——
    **判据只能抓「发了但不一致」，抓不到「根本没发」。**
    更早的证据：`v2026-09-26` 与 `v2026-10-07` 两个 tag 指向同一个提交，即当日的
    版本当时都没发、事后批量补打。
    R6 补上这一格：**当前 HEAD 该有的 tag = HEAD 提交日期**（与 release_publish.plan
    的 `today = git log -1 --format=%as` 同口径），它必须出现在远端 Release 里。

退出码：0 = 全过 · 1 = 有判负 · 2 = 前置环境不达标 · 3 = 未验证（读不到远端）
分界线只有一条：**没读到远端真值 = 3；读到了但断言不过 = 1。**
（环境类码先修环境，别去逐条读判据。）
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = os.environ.get("GITHUB_REPO", "RiverFlowsInUUU/self-conf")
API = "https://api.github.com/repos/%s" % REPO
TAG_RE = re.compile(r"^v\d{4}-\d{2}-\d{2}$")
VER_STYLE = re.compile(r"(?i)_?v\d+(\.\d+)?")       # 资产名里出现版本号即违规


class Skip(Exception):
    """读不到远端真值（不可达 / 限流 / 上游 5xx / 非 JSON）—— 未验证，不是判负。"""


def git(*a):
    return subprocess.check_output(["git", *a], encoding="utf-8", errors="replace",
                                   stderr=subprocess.DEVNULL).strip()


def _api_json(path, token, allow_404=False):
    """本文件**唯一**的请求入口 —— 异常分类只写一遍，不手抄第二份。"""
    req = urllib.request.Request(API + path)
    req.add_header("User-Agent", "self-conf-release")
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        if e.code == 404 and allow_404:
            return None                       # 读到了：端点的确定回答是「没有」
        why = ("仓路径不可读：不存在 / 私有且无权限 / 已移除 —— 先核 GITHUB_REPO"
               if e.code == 404 else
               "凭据无效 —— 先核 GITHUB_TOKEN" if e.code == 401 else
               "限流" if e.code in (403, 429) else
               "上游故障" if e.code >= 500 else "请求被拒")
        raise Skip("GitHub API %s HTTP %s（%s）" % (path, e.code, why))
    except urllib.error.URLError as e:
        raise Skip("网络不可达（%s）" % e.reason)
    except json.JSONDecodeError as e:
        raise Skip("响应不是 JSON（多为上游错误页）：%s" % e)


def fetch_releases(token):
    out, page = [], 1
    while True:
        batch = _api_json("/releases?per_page=100&page=%d" % page, token)
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def asset_relpath(name):
    """资产固定名 → 仓库内相对路径。`surge-lazy.min.conf` → `surge/profiles/lazy.min.conf`。

    ⚠️ 必须做这层还原：资产名是「内核前缀 + 产品线 + 形态」，而实际文件在
        `<kern>/profiles/<fam><.min><ext>` —— 两者 basename 永不相等。
        （历史教训见 gates.md §10.2.1：第一版用 basename 判，对任何 profile
        改动都判绿，是个假闸门。）
    """
    for kern in ("surge", "egern", "clash"):
        pre = kern + "-"
        if not name.startswith(pre):
            continue
        rest = name[len(pre):]                    # 如 lazy.min.yaml
        fam, _, tail = rest.partition(".")
        ext = "." + tail.split(".")[-1]           # .yaml / .conf
        mid = ".min" if tail.startswith("min.") else ""
        return "%s/profiles/%s%s%s" % (kern, fam, mid, ext)
    return None


def local_sha256(path):
    with open(path, "rb") as fh:
        return "sha256:" + hashlib.sha256(fh.read()).hexdigest()


def mismatched_assets(rel, root, assets):
    """远端资产 ↔ 本地 profile 的逐件比对。

    返回 (unpub, unverified)：
      unpub      —— 本地已改但远端资产还是旧的（**真漏发**，判负）
      unverified —— 无法比对（本地文件缺失 / 远端没给 digest），未验证，不判负

    为什么优先用 digest：GitHub 在 assets 上返回 `digest`（`sha256:...`），
    可直接与本地哈希比，**零下载**。无 digest 时退回「大小 + 下载全文比对」，
    两者都拿不到则记 unverified —— 不能默默放过（那正是本判据上一版栽的地方）。
    """
    unpub, unverified = [], []
    for name, rpath in sorted(rel.items()):
        a = assets.get(name)
        if a is None:
            unpub.append("%s（该 Release 没有这件资产）" % name)
            continue
        lp = os.path.join(root, rpath)
        if not os.path.isfile(lp):
            unverified.append("%s（本地缺 %s）" % (name, rpath))
            continue
        digest = (a.get("digest") or "").strip().lower()
        if digest.startswith("sha256:"):
            if digest != local_sha256(lp):
                unpub.append(name)
            continue
        try:
            want = open(lp, "rb").read()
        except OSError as e:
            unverified.append("%s（读不到本地文件：%s）" % (name, e))
            continue
        url = a.get("browser_download_url")
        if not url:
            unverified.append("%s（远端未给下载地址）" % name)
            continue
        if a.get("size") != len(want):
            unpub.append(name)
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "self-conf-release"})
            with urllib.request.urlopen(req) as r:
                got = r.read()
        except Exception as e:                        # noqa: BLE001
            unverified.append("%s（下载失败：%s）" % (name, e))
            continue
        if got != want:
            unpub.append(name)
    return unpub, unverified


def main():
    root = git("rev-parse", "--show-toplevel")
    sys.path.insert(0, os.path.join(root, "self-conf-skills", "run"))
    import release_publish as rp                  # 单一真源：资产名与版本口径都从这来

    p = rp.plan(root)
    want_assets = set(p["assets"])
    want_vers = set(p["versions"].values())

    try:
        releases = fetch_releases(os.environ.get("GITHUB_TOKEN"))
    except Skip as e:
        print("SKIP: %s —— 未能验证远端 Release 状态（离线/限流/上游故障/无凭据）。"
              "不是绿，是未验证。" % e)
        return 3

    ok, bad, skipped = [], [], []

    def judge(cond, msg_ok, msg_bad):
        (ok if cond else bad).append(msg_ok if cond else msg_bad)

    judge(bool(releases), "至少有一个 Release",
          "仓库还没有任何 Release —— 先跑 release_publish.py --apply")

    seen = set()
    for r in releases:
        tag = r["tag_name"]
        judge(bool(TAG_RE.match(tag)), "%s: tag 形状" % tag,
              "%s: tag 不匹配 ^vYYYY-MM-DD$" % tag)
        judge(tag not in seen, "%s: tag 唯一" % tag, "%s: tag 重复" % tag)
        seen.add(tag)
        for a in r.get("assets", []):
            n = a["name"]
            judge(n in rp.ASSET_NAMES and not VER_STYLE.search(n),
                  "%s/%s: 资产命名" % (tag, n),
                  "%s/%s: 不在固定名集合或带版本号（应 ∈ %s）"
                  % (tag, n, sorted(rp.ASSET_NAMES)))

    # 最新那张 = 字典序最大（tag 形态 vYYYY-MM-DD，字典序即时间序）
    newest = max(releases, key=lambda r: r["tag_name"])
    tag = newest["tag_name"]
    have = {a["name"] for a in newest.get("assets", [])}
    judge(have == want_assets, "%s: 资产齐全且无多余（%d 件）" % (tag, len(want_assets)),
          "%s: 资产与当前版本不符 —— 缺 %s / 多 %s"
          % (tag, sorted(want_assets - have), sorted(have - want_assets)))

    body = newest.get("body") or ""
    missing_v = [v for v in want_vers if v not in body]
    judge(not missing_v, "%s: 正文含当前版本号 %s" % (tag, sorted(want_vers)),
          "%s: 正文缺版本号 %s —— 跑 release_publish.py --apply 幂等回写"
          % (tag, missing_v))

    try:
        latest = _api_json("/releases/latest", os.environ.get("GITHUB_TOKEN"), allow_404=True)
    except Skip as e:
        skipped.append("R5 /releases/latest：%s —— 未能核对 Latest 指针" % e)
    else:
        if latest is None:
            judge(False, "", "R5 /releases/latest 返回 404 = 仓库无 Latest Release —— "
                             "跑 release_publish.py --apply")
        else:
            lt = latest.get("tag_name")
            judge(lt == tag, "R5 Latest=%s（最新）" % lt,
                  "R5 Latest=%s ≠ 最新 %s —— 跑 release_publish.py --apply" % (lt, tag))

    # ── R6 本地 profile 必须已发出 ────────────────────────────────────────
    #   ⚠️ 只认**远端 Release**，不查本地 `git tag`：本地可能没 fetch 到 tag
    #      （实测 2026-10-10：远端 Release 已在、本地 `git tag --list` 却是空的）。
    #   ⚠️ 与 R3/R4 的分工：R3/R4 判「最新那张**自身**对不对」，R6 判「本地的
    #      改动**有没有**被发出去」。没有 R6 时，一张新 Release 都没建的场景下
    #      R3/R4 会全绿（见头注）。
    #
    #   判据对象的历史（设计时**来回错了四次**，四次都实测过，钉在这里）：
    #
    #      · 错法一 `tag_sha == head_sha`：tag 一经创建即固定，而
    #        `release_publish.apply()` 只 PATCH body/name、**从不移动 tag**。
    #        「一天一版」下当天任何后续提交都会让 `tag != HEAD` ⇒ 门禁**永远红**。
    #      · 错法二 `is_ancestor(tag_sha, head_sha)` 取真：判的是「HEAD 是否
    #        超出 tag」，把「当天只改文档/判据」也误判成漏发 —— 而本仓显式规定
    #        「只改注释/文档 ⇒ 不必升号」（ops.md §2），更不该因此判负。
    #      · 错法三 `git diff tag_sha..HEAD` 找变动过的 profile（2026-10-10）：
    #        **与错法一同病** —— tag 不动 ⇒ 当天改过 profile 并重发过，该 diff
    #        恒非空 ⇒ 永远红，且提示的补救（再跑 --apply）治不了它。
    #        更糟的是浅克隆下 `git diff` 抛 Invalid revision range，被
    #        `except` 吞成空列表 ⇒ **静默判绿**（假阴性）。
    #      · 错法四 「HEAD 提交日必须有 Release」当作**无条件**前提（2026-10-11
    #        实测撞上）：跨午夜后提交任何东西（哪怕只改一个错别字）都会逼出一张
    #        「说明写着什么都没改」的空 Release —— 自相矛盾，见下方长注释。
    #
    #      ⇒ 正确的是问：**本地 profile 与已发布资产一致吗？**
    #        一致 = 该发的都发了，不需要任何新 Release；
    #        不一致 = 才要求有 Release 承载（并逐件核对资产）。
    #        直接比内容（digest 优先，零下载），不猜日期、不依赖 git 历史深度。
    #   ⚠️ 2026-10-11 重写 R6a 的**前置条件**（原设计会逼出「空 Release」）：
    #
    #     原 R6a 无条件要求「HEAD 提交日 == 某张 Release 的 tag」。后果：跨过午夜后
    #     提交任何东西 —— **哪怕只改一个错别字、一个判据** —— 都会因为没有当天的
    #     Release 而判红，于是被迫发一张「说明里写着什么都没改」的 Release。
    #     2026-10-11 实测踩中：为消红发了 `v2026-10-11`，正文只能写「配置无变化」，
    #     自相矛盾（Releases 页面挂着一条没有内容的版本）。
    #
    #     而 ops.md §2 的表格明说：只改注释/文案/排版 ⇒ **不升号**，
    #     且「进 Release」那一栏的措辞是「**并入当天那张**」——
    #     即：**当日没有 Release 时，注释类改动不该凭空造一张**。
    #
    #     ⇒ 正解：先把「本地 profile 与**最新已发布资产**」比一遍。
    #        · 一致 ⇒ 该发的都发了，**无需任何当日 Release**，直接通过；
    #        · 不一致 ⇒ 才要求有当日 Release 来承载这批变动（并逐件核对）。
    #       这样「只改文档」天然放行，「改了配置没发版」仍被判负。
    #
    #     顺带：判据对象从「HEAD 的**日期**」换成「**内容**是否已发布」，
    #     比日期口径更本质 —— 也避免了跨午夜、补发、时区等日期类假红。
    rel = {}
    for nm in want_assets:
        rp_ = asset_relpath(nm)
        if rp_:
            rel[nm] = rp_

    # 最新那张 = 已发布状态的真值（tag 形态 vYYYY-MM-DD，字典序即时间序）
    newest_assets = {a["name"]: a for a in newest.get("assets", [])}
    stale, unverified_pre = mismatched_assets(rel, root, newest_assets)
    if unverified_pre:
        skipped.append("R6 部分资产未能与最新 Release 比对：%s"
                       % ", ".join(unverified_pre))

    if not stale:
        judge(True, "R6 本地 profile 与最新 Release(%s) 逐件一致 —— 无需发版"
                    % newest["tag_name"], "")
    else:
        # 有未发布的 profile 变动 ⇒ 必须有**当日** Release 承载（原 R6a 的本意）
        head_tag = rp.plan(root)["tag"]
        target_release = next((r for r in releases if r["tag_name"] == head_tag), None)
        have_tag = target_release is not None
        judge(have_tag,
              "R6a 本地 profile 有变动，当日 Release %s 已发布" % head_tag,
              "R6a 本地 profile 有变动（%s），但没有当日 Release %s —— "
              "跑 release_publish.py（预览）→ --apply（真发）；"
              "若本次是功能变动，先按 ops.md §2 升号再发"
              % (", ".join(stale), head_tag))
        if have_tag:
            # ② 该 Release 的资产与**本地 profile 逐件一致**
            rel_assets = {a["name"]: a for a in target_release.get("assets", [])}
            unpub, unverified = mismatched_assets(rel, root, rel_assets)
            judge(not unpub,
                  "R6b %s 的 %d 件资产与本地 profile 逐件一致" % (head_tag, len(rel)),
                  "R6b %s 的资产与本地 profile 不一致（本地已改但没重发）：%s —— "
                  "跑 release_publish.py --apply 重发资产（幂等回写同一张，tag 不动）"
                  % (head_tag, ", ".join(unpub)))
            if unverified:
                skipped.append("R6b 部分资产未能比对：%s" % ", ".join(unverified))

    for m in ok:
        print("   ✅ %s" % m)
    for m in bad:
        print("   ❌ %s" % m)
    for m in skipped:
        print("   ⚠️ 未验证 %s" % m)
    print("\nTOTAL: %d passed, %d failed, %d unverified" % (len(ok), len(bad), len(skipped)))
    if bad:
        return 1
    return 3 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())

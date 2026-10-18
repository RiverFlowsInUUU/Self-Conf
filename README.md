<div align="center">

<img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Surge.png" height="56" alt="Surge">&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Brand-Cross.png" height="56" alt="">&nbsp;&nbsp;&nbsp;<img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Egern.png" height="56" alt="Egern">&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Brand-Cross.png" height="56" alt="">&nbsp;&nbsp;&nbsp;<img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/mihomo.png" height="56" alt="mihomo">

# Surge · Egern · mihomo 配置模板

殊途同归 · 久用如一

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](#-各美其美--皆合心意)
[![Egern](https://img.shields.io/badge/Egern-iOS%20%7C%20macOS-0969da?style=flat-square)](#-各美其美--皆合心意)
[![mihomo](https://img.shields.io/badge/mihomo-Clash%20Meta-8250df?style=flat-square)](#-各美其美--皆合心意)
[![Groups](https://img.shields.io/badge/Groups-23%20%7C%2023%20%7C%2025-8250df?style=flat-square)](#-井然有序)
[![Rules](https://img.shields.io/badge/Rules-26%20%7C%2026%20%7C%2027-dc3545?style=flat-square)](#-井然有序)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](#-隐私至上--无-dns-泄露)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](LICENSE)
[![CI](https://github.com/RiverFlowsInUUU/self-conf/actions/workflows/ci.yml/badge.svg)](https://github.com/RiverFlowsInUUU/self-conf/actions/workflows/ci.yml)

</div>

> 🤖 **AI agent 请从这里开始** → [`AGENTS.md`](AGENTS.md)：动手顺序，与各侧判据。

一份配置，三款内核。Surge、Egern、mihomo（Clash Meta），外加 **Stash 覆写**。

换客户端，不必重学。**组结构一致。规则次序一致。防泄露底线，一致。**
不同的只是语法 —— 那是我们的事，不是你的事。

## 📥 各美其美 · 皆合心意

| <div align="center">内核</div> | 🪶 懒人版 · 至简 · 省心 | 🧭 分流版 · 可控 · 随心 |
|:--|:--|:--|
| <img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Surge-Icon.png" height="20" alt=""> **Surge** | [`surge-lazy.min.conf`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/surge/profiles/lazy.min.conf) | [`surge-routing.min.conf`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/surge/profiles/routing.min.conf) |
| <img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Egern-Icon.png" height="20" alt=""> **Egern** | [`egern-lazy.min.yaml`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/egern/profiles/lazy.min.yaml) | [`egern-routing.min.yaml`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/egern/profiles/routing.min.yaml) |
| <img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/mihomo-Icon.png" height="20" alt=""> **mihomo** | [`clash-lazy.min.yaml`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/clash/profiles/lazy.min.yaml) | [`clash-routing.min.yaml`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/clash/profiles/routing.min.yaml) |
| <img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/mihomo-Icon.png" height="20" alt=""> **mihomo**<br><sub>覆写脚本</sub> | [`clash-lazy.min.js`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/clash/override/clash-lazy.min.js) | [`clash-routing.min.js`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/clash/override/clash-routing.min.js) |
| <img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Stash-Icon.png" height="20" alt=""> **Stash**<br><sub>覆写脚本</sub> | [`stash-lazy.min.stoverride`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/stash/override/stash-lazy.min.stoverride) | [`stash-routing.min.stoverride`](https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/stash/override/stash-routing.min.stoverride) |

**覆写脚本**，为自有订阅而生。挂上即用，配置不必下载。
mihomo 取 `.js`，Stash 取 `.stoverride`。

⚠️ **Stash 不认 mihomo 的任何东西。** 脚本不行，配置也不行 ——
键名机制不同，`respect-rules` 静默失效，DNS 直连境外端点，解析超时。
请用上表两份 `.stoverride`。

## 🧭 井然有序

🗂️ 各司其职。各安其序。无隙可乘。

| <div align="center">组</div> | 🪶 懒人版 | 🧭 分流版 |
|:---|:---:|:---:|
| 🚀 `Proxy` | ✅ | ✅ |
| ⚡ `Smart` | - | ✅ |
| 🤖 `ChatGPT` · `Gemini` · `Claude` · `AI` | 仅 `AI` | ✅ |
| ▶️ `YouTube` · 🎬 `Emby` · 🔎 `Google`<br>✈️ `Telegram` · 🐦 `Twitter` · 🪟 `Microsoft`<br>🎶 `YouTube Music` · 🎵 `Spotify` | - | ✅ |
| 🍎 `Apple Update` | - | ✅ |
| 🛑 `AD` | ✅ | ✅ |
| 🇭🇰 `Hong Kong` · 🇨🇳 `Taiwan` · 🇯🇵 `Japan`<br>🇸🇬 `Singapore` · 🇺🇸 `United States`<br>🇦🇶 `Other Regions` | - | ✅ |

分流版组数：**Surge / Egern 23 组 · 26 条规则**，**mihomo 25 组 · 27 条规则**。

## 🌐 隐私至上 · 无 DNS 泄露

八类出口。逐一封死。四侧写法的差异不改结论 —— **出口没有例外**。

| | 出口 | 怎么封 |
|:--:|:--|:--|
| 🚫 | 旁路设备 | 接管明文 `:53`，绕开你的 DNS 直接发包也没用 |
| 🔐 | 加密通道 | 主解析全走 DoH / DoT，不落明文 |
| 🛡️ | 明文回退 | 兜底只指向加密组，**绝不写 `system`** |
| 🧭 | 规则克制 | IP 类规则一律 `no-resolve`，不为判定触发解析 |
| ✂️ | 远端解析 | 代理域名交节点解析，本地不留答案 |
| 🔎 | IPv6 | 显式关闭，不让真实 IPv6 绕过隧道 |
| 🛑 | 广告拦截 | 解析层就掐断，不必等连接建立 |
| 📦 | 数据库依赖 | 零 dat，规则集全部远程自更新 |

前六行堵漏，后两行白送。

<details>
<summary>四侧具体写法（展开看）</summary>

| | Surge | Egern | mihomo | Stash |
|:--|:--|:--|:--|:--|
| 旁路 | `hijack-dns`（六个知名解析器） | `hijack_dns`（全量） | 客户端 TUN 重定向 | 网络引擎（无该键） |
| 加密 | DoH，主机名端点经裸 IP 引导 | DoH / DoT，端点全 IP 字面量 | DoH，端点全 IP 字面量 | DoH，`default-nameserver` 仅填 IP |
| 回退 | `dns-server` 全裸 IP | `forward` 兜底只指加密组 | `proxy-server-nameserver` 专用通道 | 同 mihomo |
| 规则 | IP 规则 `no-resolve` | `no_resolve` | IP 规则 `no-resolve` | 同 mihomo |
| 远端 | 交节点解析 | `proxy_nameservers` 通道 | `fake-ip` | 默认 Fake IP |
| IPv6 | `ipv6 = false` | `ipv6: false` | 顶层 + `dns.ipv6` 两处 | 官方自动判定¹ |
| 广告 | `pre-matching REJECT` | `forward` → `reject` | DNS 双条件 | 规则层 `AD` 组 |
| dat | 内置系统集 | 共享 `.list` | 零 dat，用 `.mrs` | 零 dat，用 `.list` / `.yaml` |

¹ Stash 未显式写 `ipv6` —— 官方按当前网络自动判定，双栈下仍会返回 AAAA。

</details>

而且不止说到位 —— **每一条都有判据守着**。全套闸门，外加 CI。
逐键推导见 [`dns.md`](self-conf-skills/references/dns.md) §7「四侧语法对照」。

## 📖 按需查阅

操作手册、逐键语义、审计判据、发版规矩 —— 尽在 [`AGENTS.md`](AGENTS.md)。

---

<div align="center">

🐈 让 DNS 无处可漏 · MIT License

</div>

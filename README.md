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

八类出口。逐一封死。

| 泄露出口 | <div align="center"><img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Surge-Icon.png" height="22" alt=""> Surge</div> | <div align="center"><img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Egern-Icon.png" height="22" alt=""> Egern</div> | <div align="center"><img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/mihomo-Icon.png" height="22" alt=""> mihomo</div> | <div align="center"><img src="https://raw.githubusercontent.com/RiverFlowsInUUU/self-conf/main/icons/Stash-Icon.png" height="22" alt=""> Stash</div> |
|:--|:--|:--|:--|:--|
| 🚫 旁路设备<br>| `hijack-dns` 接管明文 `:53`（六个知名解析器） | `hijack_dns` 接管明文 `:53`（全量） | 交给客户端 TUN 或透明代理重定向 | 交给网络引擎（无该键） |
| 🔐 加密通道<br>| 主解析走 DoH，主机名端点经裸 IP 受控引导 | 主解析走 DoH/DoT，四条端点全是 IP 字面量 | 主解析走 DoH，端点一律 IP 字面量 | 主解析走 DoH，`default-nameserver` 仅填 IP |
| 🛡️ 明文回退<br>| `dns-server` 全裸 IP，绝不写 `system` | `forward` 兜底只指加密组，绝不落明文 | `default-nameserver` 裸 IP（仅引导）+ `proxy-server-nameserver` 专用通道 | 同左（`proxy-server-nameserver` 专用通道） |
| 🧭 规则克制<br>| IP 类规则一律 `no-resolve`；零 IP 的规则集不写 | IP 类规则一律 `no_resolve`；该键对 `rule_set` 不生效 | IP 类规则一律 `no-resolve`；纯域名规则集不写 | 同左（4 个 `ipcidr` 集带 `no-resolve`） |
| ✂️ 远端解析<br>| 代理域名交节点解析，本地不留答案 | 代理域名交节点解析（`proxy_nameservers` 专用通道） | `fake-ip` 只回假 IP，真实解析在落地侧 | 同左（默认 Fake IP） |
| 🔎 IPv6<br>| `ipv6 = false` | `ipv6: false` | 顶层 + `dns.ipv6`，两处都关 | 按官方〈IPv6 兼容性〉自动选择，不写该键 |
| 🛑 广告拦截<br>| `pre-matching REJECT` | `forward` → `reject` | DNS 层双条件（`rcode://success` 与 `fake-ip-filter` 成对） | 规则层 `AD` 组（无 `rcode` 语法） |
| 📦 数据库依赖<br>| 内置系统集 | 引用共享 `.list` | 零 dat 依赖，用 `.mrs` 远程集 | 零 dat，用 `.list` / `.yaml` 远程集 |

前六行，堵漏。后两行，白送。
出口分类的完整推导，见 [`dns.md`](self-conf-skills/references/dns.md) 的「接到本模板上」。

四侧机制各异，写法各异。**出口没有例外。**

而且不止说到位 —— **每一条都有判据守着**。全套闸门，外加 CI。

## 📖 按需查阅

操作手册、逐键语义、审计判据、发版规矩 —— 尽在 [`AGENTS.md`](AGENTS.md)。

---

<div align="center">

🐈 让 DNS 无处可漏 · MIT License

</div>

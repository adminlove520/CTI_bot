# 🏴‍☠️🤖 威胁情报钉钉机器人

本项目是从 [Threat Intelligence Discord Bot from vx-underground](https://github.com/vxunderground/ThreatIntelligenceDiscordBot/) 分叉而来，最初修改为支持 Microsoft Teams，现在已更新为支持钉钉推送（webhook+签名），并可以作为小时级 GitHub Action 运行。

> 原始的 vx-underground 威胁情报 Discord 机器人从各种明网域名、勒索软件威胁行为者域名获取更新。本机器人将每隔 1800 秒（30分钟）检查一次更新。

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) ![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)  [![Twitter: JMousqueton](https://img.shields.io/twitter/follow/JMousqueton.svg?style=social)](https://twitter.com/JMousqueton) [![Last Run](https://github.com/JMousqueton/CTI-MSTeams-Bot/actions/workflows/fetchCTI.yml/badge.svg)](.github/workflows/fetchCTI.yml)  [![CodeQL](https://github.com/JMousqueton/CTI-MSTeams-Bot/actions/workflows/codeql-analysis.yml/badge.svg)](.github/workflows/codeql-analysis.yml)

## 项目说明

* 使用 Python 编写

   ⚠️ 需要 Python 3.10+ 版本
* 需要钉钉 Webhook 和签名密钥

威胁情报钉钉机器人从各种明网域名和勒索软件威胁行为者域名获取更新，并通过钉钉 webhook+签名的方式推送通知。

本机器人将每 30 分钟检查一次更新。

主要更新内容：

* GitHub-Action 支持：详见 [fetchCTI.yml](.github/workflows/fetchCTI.yml) 文件
* 订阅源列表从源代码外部化到 [Feed.csv](Feed.csv) 文件
* 使用 JSON 库从 [Ransomwatch](https://ransomwatch.mousqueton.io) 获取勒索软件攻击列表
* 为不同来源的消息添加相关 emoji 标识
* 支持多个钉钉 webhook 推送
* 代码重构，遵循最佳实践
* 无需手动在 [Config.txt](Config.txt) 添加条目（自动添加）
* 检查是否安装了 Python 3.10+（某些功能需要）
* 添加 [requirements.txt](requirements.txt) 文件
* 添加 [checkFeed.py](checkFeed.py) 脚本，用于检查 [Feed.csv](Feed.csv) 文件中订阅源的健康状态
* 添加命令行选项 [使用说明](#使用说明)
* 检查新版本是否可用
* 添加 [新的信息源](#信息源)
* 更新推送方式为钉钉 webhook+签名

## 安装

克隆仓库或下载 [最新发布版本](https://github.com/JMousqueton/CTI-MSTeams-Bot/releases/latest)

```bash
git clone https://github.com/JMousqueton/CTI-MSTeams-Bot
```

安装 ```requirements.txt``` 中的所有模块

```bash
pip3 install -r requirements.txt
```

## 配置

### GitHub Action 配置

* 创建钉钉机器人 webhook 和签名密钥
* 在名为 `CI` 的环境中，将创建的 webhook URL 和签名密钥分别设置为 `DINGTALK_WEBHOOK_*` 和 `DINGTALK_SECRET_*` 变量

### 服务器配置（Windows, MacOS, Linux）

* 设置以下环境变量：
  * `DINGTALK_WEBHOOK_*` - 钉钉机器人 webhook URL
  * `DINGTALK_SECRET_*` - 钉钉机器人签名密钥

示例：

```bash
# Windows 环境
export DINGTALK_WEBHOOK_FEED=https://oapi.dingtalk.com/robot/send?access_token=xxx
export DINGTALK_SECRET_FEED=SECxxx
export DINGTALK_WEBHOOK_RANSOMWARE=https://oapi.dingtalk.com/robot/send?access_token=xxx
export DINGTALK_SECRET_RANSOMWARE=SECxxx
export DINGTALK_WEBHOOK_IOC=https://oapi.dingtalk.com/robot/send?access_token=xxx
export DINGTALK_SECRET_IOC=SECxxx
python3 TeamsIntelBot.py -r -d
```

```batch
:: Windows CMD 环境
set DINGTALK_WEBHOOK_FEED=https://oapi.dingtalk.com/robot/send?access_token=xxx
set DINGTALK_SECRET_FEED=SECxxx
set DINGTALK_WEBHOOK_RANSOMWARE=https://oapi.dingtalk.com/robot/send?access_token=xxx
set DINGTALK_SECRET_RANSOMWARE=SECxxx
set DINGTALK_WEBHOOK_IOC=https://oapi.dingtalk.com/robot/send?access_token=xxx
set DINGTALK_SECRET_IOC=SECxxx
python3 TeamsIntelBot.py -r -d
```

* 可以通过 crontab（Linux/MacOS）或任务计划程序（Windows）设置定期执行脚本，例如每小时执行一次

## 使用说明

```bash
python3 TeamsIntelBot.py -h
Usage: TeamsIntelBot.py [options]

Options:
  --version       显示程序版本号并退出
  -h, --help      显示帮助信息并退出
  -q, --quiet     静默模式
  -D, --debug     调试模式：仅在屏幕上输出，不发送到钉钉
  -d, --domain    启用 Red Flag Domains 信息源
  -r, --reminder  启用订阅源月度提醒
```

- 对于法语用户，建议使用 -d 和 -r 标志

```python3 TeamsIntelBot.py -r -d```

- 对于其他用户，仅使用 -r 标志

```python3 TeamsIntelBot.py -r```

### 代理设置

如果您使用代理，请设置以下环境变量：

```bash
# Linux/MacOS
export https_proxy=http://x.x.x.x:port
export http_proxy=http://x.x.x.x:port
```

```batch
:: Windows CMD
set https_proxy=http://x.x.x.x:port
set http_proxy=http://x.x.x.x:port
```

## 检查订阅源

项目中包含了一个名为 ```checkFeed.py``` 的脚本，用于检查订阅源是否有效以及最后发布日期。该脚本读取 ```Feed.csv``` 文件。

```bash
python3 checkFeed.py
```

## 添加或删除监控的 RSS 订阅源
所有监控的 RSS 订阅源都存储在 [Feed.csv](Feed.csv) 文件中。要添加新的 RSS 订阅源，只需添加新条目即可。例如：

在 ```Feed.csv``` 文件中：

```text
https://example.com/feed/,网站名称
https://another-example.com/rss/,另一个网站
```

## 信息源

已添加以下信息源：

* 🇫🇷 FR-CERT Avis (aka [ANSSI](https://www.ssi.gouv.fr/)): 法国政府 CERT 通知
* 🇫🇷 FR-CERT Alertes (aka [ANSSI](https://www.ssi.gouv.fr/)): 法国政府 CERT 警报
* [Leak-lookup](https://leak-lookup.com/): 数据泄露通知
* [Cyber-News](https://www.cyber-news.fr)
* ATT 网络安全博客
* 🇪🇺 ENSIA 出版物
* NCC Group
* Microsoft Sentinel
* SANS
* [Red Flag Domains](https://red.flag.domains/) ⚠️ 您需要使用 -d 标志来启用此专门面向法国的信息源
* [Google TAG](https://blog.google/threat-analysis-group/)

## 更新历史

* 添加了对 Red Flag Domains 信息源的激活/禁用标志（版本 2.3 已发布）
* 支持在 [Feed.csv](Feed.csv) 中使用 # 禁用行（版本 2.4）
* 更新推送方式为钉钉 webhook+签名

## 鸣谢

本项目最初由 smelly__vx 在一个缓慢而无聊的周末创建。希望它能为您的频道和/或组织提供一些价值。

感谢 [🏴‍☠️ Ecole 2600](https://www.ecole2600.com) 的同学们在夜间提供的支持和建议 😛

感谢当前使用此机器人的用户帮助改进它

感谢 Olivier 提供的代理文档 🍻

感谢所有贡献者的努力和支持

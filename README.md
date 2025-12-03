# 🏴‍☠️🤖 威胁情报钉钉机器人


[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) ![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)  [![Last Run](https://github.com/adminlove520/CTI_bot/actions/workflows/fetchCTI.yml/badge.svg)](.github/workflows/fetchCTI.yml)  [![CodeQL](https://github.com/adminlove520/CTI_bot/actions/workflows/codeql-analysis.yml/badge.svg)](.github/workflows/codeql-analysis.yml)

## 📖 项目说明

* 使用 Python 编写

   ⚠️ 需要 Python 3.10+ 版本
* 需要钉钉 Webhook 和签名密钥

威胁情报钉钉机器人从各种明网域名和勒索软件威胁行为者域名获取更新，并通过钉钉 webhook+签名的方式推送通知。

本机器人将每 30 分钟检查一次更新。

## 🎉 主要更新内容 (版本 3.0.0)

### 🚀 核心功能增强

* **GitHub-Action 支持增强**
  - `add_feed_from_issue.yml`: 从 GitHub Issue 提交 Feed 并自动添加到 Feed.csv
  - `update_rss_feeds.yml`: 定期从 OPML 源更新 RSS 订阅并移除无效 Feed
  - `fetchCTI.yml`: 支持手动触发时配置参数，增强了定时任务功能

* **OPML 转换功能**
  - `opml_to_rss.py`: 将 OPML 文件转换为 RSS 格式，支持本地文件和远程 URL
  - 支持通过 `config_rss.yaml` 配置多个 OPML 源
  - 实现了 Feed 去重功能，避免重复添加

* **Ransomware.live API PRO 集成**
  - 支持使用 API PRO 获取更丰富的威胁情报数据
  - 实现了 API 密钥认证和错误处理
  - 添加了 API 调用失败时的回退机制，自动切换到免费 API
  - 支持通过配置文件设置筛选条件

* **配置管理增强**
  - `config_rss.yaml`: 管理 OPML 源配置，支持启用/禁用控制
  - 环境变量优先于配置文件，提高安全性
  - 改进了配置文件的错误处理和兼容性

### 🔧 工具与脚本增强

* **`checkFeed.py` 增强**
  - 支持从配置文件读取参数
  - 新增自动移除无效 Feed 功能
  - 生成详细的 Feed 检查报告
  - 支持通过命令行参数控制行为

* **`TeamsIntelBot.py` 优化**
  - 增强了错误处理能力
  - 改进了 API 调用逻辑，添加了超时和重试机制
  - 优化了配置加载流程，支持多种配置方式
  - 改进了钉钉消息推送格式，增强了可读性

### 🛡️ 安全与可靠性

* 移除了配置文件中的硬编码敏感信息
* 优先使用环境变量存储 API 密钥和 Webhook URL
* 改进了 API 认证方式，使用 X-API-KEY 头部
* 增强了输入验证和错误处理
* 修复了多个 YAML 语法错误，确保工作流正常运行

## 🔧 安装

克隆仓库或下载 [最新发布版本](https://github.com/adminlove520/CTI_bot/releases/latest)

```bash
git clone https://github.com/adminlove520/CTI_bot.git
```

安装 `requirements.txt` 中的所有模块

```bash
pip3 install -r requirements.txt
```

## ⚙️ 配置

### 🌍 环境变量配置

项目支持通过 `.env` 文件配置环境变量，这是最简单和推荐的方式。

1. 复制 `.env.example` 文件并重命名为 `.env`：

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入您的钉钉机器人 webhook URL 和签名密钥：

```
# Feed推送配置
DINGTALK_WEBHOOK_FEED=https://oapi.dingtalk.com/robot/send?access_token=your_token_here
DINGTALK_SECRET_FEED=your_secret_here

# 勒索软件更新配置
DINGTALK_WEBHOOK_RANSOMWARE=https://oapi.dingtalk.com/robot/send?access_token=your_token_here
DINGTALK_SECRET_RANSOMWARE=your_secret_here
RANSOMWARE_LIVE_API_KEY=your_api_key_here

# 威胁指标配置
DINGTALK_WEBHOOK_IOC=https://oapi.dingtalk.com/robot/send?access_token=your_token_here
DINGTALK_SECRET_IOC=your_secret_here
```

> **注意**：请确保 `.env` 文件已添加到 `.gitignore` 中，避免将敏感信息提交到代码仓库。

### 📡 API PRO 配置

项目支持使用 [Ransomware.live API PRO](https://www.ransomware.live/api) 获取更丰富的威胁情报数据。

#### 配置步骤

1. 从 [Ransomware.live](https://www.ransomware.live/api) 获取 API PRO 密钥

2. 复制 `config_ransomware.yaml.example` 文件并重命名为 `config_ransomware.yaml`：

```bash
cp config_ransomware.yaml.example config_ransomware.yaml
```

3. 编辑 `config_ransomware.yaml` 文件，填入您的配置：

```yaml
ransomware:
  # API PRO 设置
  api_key: ""  # 建议通过环境变量 RANSOMWARE_LIVE_API_KEY 设置
  use_pro: true  # 设置为 true 启用 API PRO
  enabled: true
  
  # 筛选设置（匹配 API PRO 参数）
  filters:
    # 按勒索软件组织名称筛选
    # Example: group: ["lockbit", "conti"]
    group: []
    
    # 按受害者行业筛选
    # Example: sector: ["healthcare", "technology"]
    sector: []
    
    # 按 2 字母国家代码筛选
    # Example: country: ["CN", "US", "FR"]
    country: []
    
    # 按 4 位年份筛选
    # Example: year: ["2024", "2025"]
    year: []
    
    # 按 2 位月份筛选
    # Example: month: ["01", "06"]
    month: []
    
    # 使用 'discovered'（默认）或 'attacked' 日期进行筛选
    date: "discovered"
  
  # 推送设置（可选，将使用环境变量如果未设置）
  # 注意：建议使用环境变量而不是硬编码
  push_settings:
    webhook_url: ""  # 建议通过环境变量 DINGTALK_WEBHOOK_RANSOMWARE 设置
    secret: ""  # 建议通过环境变量 DINGTALK_SECRET_RANSOMWARE 设置
```

### 📋 OPML 源配置

使用 `config_rss.yaml` 文件配置 OPML 源，用于定期更新 RSS 订阅：

```yaml
title: "CTI RSS 配置"
rss:
  CustomRSS:
    enabled: false
    filename: "CustomRSS.opml"
  CyberSecurityRSS:
    enabled: false
    url: "https://raw.githubusercontent.com/zer0yu/CyberSecurityRSS/master/CyberSecurityRSS.opml"
    filename: "CyberSecurityRSS.opml"
  CyberSecurityRSS-tiny:
    enabled: false
    url: "https://raw.githubusercontent.com/zer0yu/CyberSecurityRSS/master/tiny.opml"
    filename: "CyberSecurityRSS-tiny.opml"
  Chinese-Security-RSS:
    enabled: true
    url: "https://raw.githubusercontent.com/zhengjim/Chinese-Security-RSS/master/Chinese-Security-RSS.opml"
    filename: "Chinese-Security-RSS.opml"
  awesome-security-feed:
    enabled: false
    url: "https://raw.githubusercontent.com/mrtouch93/awesome-security-feed/main/security_feeds.opml"
    filename: "awesome-security-feed.opml"
  wechatRSS:
    enabled: true
    url: "https://wechat2rss.xlab.app/opml/sec.opml"
    filename: "wechatRSS.opml"
  chinese-independent-blogs:
    enabled: false
    url: "https://raw.githubusercontent.com/timqian/chinese-independent-blogs/master/feed.opml"
    filename: "chinese-independent-blogs.opml"
```

### 🤖 GitHub Actions 配置

在 GitHub Actions 中，您仍需在 CI 环境的 secrets 中配置相应的环境变量：
- `DINGTALK_WEBHOOK_FEED`
- `DINGTALK_SECRET_FEED`
- `DINGTALK_WEBHOOK_RANSOMWARE`
- `DINGTALK_SECRET_RANSOMWARE`
- `DINGTALK_WEBHOOK_IOC`
- `DINGTALK_SECRET_IOC`

* 可以通过 crontab（Linux/MacOS）或任务计划程序（Windows）设置定期执行脚本，例如每小时执行一次

## 🚀 使用说明

### 基本使用

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

### OPML 转换功能

使用 `opml_to_rss.py` 将 OPML 文件转换为 RSS 并添加到 Feed.csv：

```bash
# 转换单个 OPML 文件
python3 opml_to_rss.py --opml-file CustomRSS.opml

# 转换远程 OPML URL
python3 opml_to_rss.py --opml-url https://example.com/feeds.opml

# 使用配置文件中的所有启用的 OPML 源
python3 opml_to_rss.py
```

### 检查订阅源

使用 `checkFeed.py` 检查和管理订阅源：

```bash
# 仅生成报告，不修改文件
python3 checkFeed.py --report-only

# 移除无效 Feed 并生成报告
python3 checkFeed.py --remove-invalid

# 使用自定义配置文件
python3 checkFeed.py --config custom_config.yaml

# 使用自定义 Feed.csv 文件
python3 checkFeed.py --feed-file custom_feed.csv
```

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

## 📊 添加或删除监控的 RSS 订阅源

所有监控的 RSS 订阅源都存储在 [Feed.csv](Feed.csv) 文件中。要添加新的 RSS 订阅源，只需添加新条目即可。例如：

在 `Feed.csv` 文件中：

```text
https://example.com/feed/,网站名称
https://another-example.com/rss/,另一个网站
```

您也可以通过 GitHub Issue 提交 Feed，`add_feed_from_issue.yml` 工作流会自动处理。

## 📡 信息源

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

## 📝 更新历史

* **版本 3.0.0** - 2025-12-03
  - 新增 GitHub Actions 工作流，支持从 Issue 添加 Feed 和定期更新 RSS
  - 新增 OPML 转换功能，支持从 OPML 源更新 RSS 订阅
  - 集成 Ransomware.live API PRO，支持更丰富的威胁情报
  - 增强了配置管理，支持通过环境变量覆盖配置
  - 改进了 Feed 管理工具，支持自动移除无效 Feed
  - 修复了多个 YAML 语法错误
  - 提高了安全性，优先使用环境变量存储敏感信息

* **版本 2.5.0** - 2023-01-11
  - 重写红旗域名解析器

* **版本 2.4.0** - 2022-10-16
  - 将 Google 源替换为 Google TAG 源
  - 支持在 Feed.csv 中使用 # 禁用行
  - 添加 MSRC 安全更新源

* **版本 2.3.0** - 2022-10-15
  - 添加了对 Red Flag Domains 信息源的激活/禁用标志

* **版本 2.0.0** - 2022-08-21
  - 支持命令行选项
  - 仅屏幕输出的调试模式
  - 静默模式
  - 在脚本中检查 Python 版本

## 🙏 鸣谢

本项目最初由 smelly__vx 在一个缓慢而无聊的周末创建。希望它能为您的频道和/或组织提供一些价值。

感谢 [🏴‍☠️ Ecole 2600](https://www.ecole2600.com) 的同学们在夜间提供的支持和建议 😛

感谢当前使用此机器人的用户帮助改进它

感谢 Olivier 提供的代理文档 🍻

感谢所有贡献者的努力和支持

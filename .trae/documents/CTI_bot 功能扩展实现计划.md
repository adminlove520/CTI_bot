# CTI_bot 功能扩展实现计划

## 1. 项目结构分析

通过对现有项目的分析，我了解到这是一个 CTI (网络威胁情报) 机器人，主要功能是从各种 RSS 源获取威胁情报并推送到钉钉。现有文件包括：
- `Feed.csv`：存储 RSS 源列表
- `checkFeed.py`：检查 RSS 源是否有效
- `TeamsIntelBot.py`：主要的情报收集和推送脚本
- `.github/workflows/fetchCTI.yml`：定时运行情报收集的 GitHub Actions workflow

## 2. 实现计划

### 2.1 创建 config_rss.yaml 配置文件

- 创建 `config_rss.yaml` 文件，用于存储 RSS 配置
- 包含用户可以开启或关闭的 RSS 源配置
- 支持本地和远程 OPML 文件

### 2.2 实现 OPML 转换脚本

- 创建 `opml_to_rss.py` 脚本，用于将 OPML 文件转换为 RSS 格式
- 支持从本地文件或远程 URL 读取 OPML
- 解析 OPML 中的 RSS 源，并输出到指定格式

### 2.3 修改 checkFeed.py 脚本

- 增强现有 `checkFeed.py` 脚本，使其支持：
  - 读取 `config_rss.yaml` 配置
  - 检查 RSS 源的有效性
  - 自动移除无效的 RSS 源
  - 生成详细的检查报告

### 2.4 创建第一个 workflow：处理 issue 提交的 feed

- 创建 `.github/workflows/add_feed_from_issue.yml` workflow
- 监听 issue 事件，当有新 issue 创建时：
  - 解析 issue 内容，提取 RSS 链接和名称
  - 将 RSS 源添加到 `Feed.csv`
  - 提交更改到远程仓库
  - 关闭 issue 并回复

### 2.5 创建第二个 workflow：定时检查和更新 RSS

- 创建 `.github/workflows/update_rss_feeds.yml` workflow
- 定时运行（例如每天）：
  - 运行 `opml_to_rss.py` 脚本，从配置的 OPML 源获取最新 RSS
  - 运行 `checkFeed.py` 脚本，检查所有 RSS 源的有效性
  - 自动移除无效的 RSS 源
  - 提交更改到远程仓库，包含详细的提交信息

## 3. 技术细节

### 3.1 config_rss.yaml 格式

```yaml
title: "CTI RSS 配置"
rss:
  CustomRSS:
    enabled: true
    filename: "CustomRSS.opml"
  CyberSecurityRSS:
    enabled: false
    url: "https://raw.githubusercontent.com/zer0yu/CyberSecurityRSS/master/CyberSecurityRSS.opml"
    filename: "CyberSecurityRSS.opml"
  # 其他配置项...
```

### 3.2 OPML 转换脚本功能

- 支持从本地文件或远程 URL 读取 OPML
- 解析 OPML 中的 `<outline>` 元素，提取 RSS 链接和标题
- 输出为 CSV 格式，可直接导入到 `Feed.csv`
- 支持过滤重复的 RSS 源

### 3.3 checkFeed.py 增强功能

- 支持读取 `Feed.csv` 和 `config_rss.yaml`
- 使用 `feedparser` 库检查 RSS 源的有效性
- 记录检查结果，包括有效的和无效的 RSS 源
- 生成详细的报告，包含删除的 RSS 源和原因

### 3.4 GitHub Actions Workflow 设计

- 使用 Ubuntu 最新版本作为运行环境
- 使用 Python 3.10
- 包含适当的错误处理和日志记录
- 支持手动触发和定时触发
- 使用 GitHub 机器人账户提交更改

## 4. 实现步骤

1. 创建 `config_rss.yaml` 配置文件
2. 实现 `opml_to_rss.py` 脚本
3. 修改 `checkFeed.py` 脚本
4. 创建 `add_feed_from_issue.yml` workflow
5. 创建 `update_rss_feeds.yml` workflow
6. 测试所有功能是否正常工作
7. 提交所有更改

## 5. 预期效果

- 用户可以通过创建 issue 来添加新的 RSS 源
- 系统会自动检查和移除无效的 RSS 源
- 用户可以通过修改 `config_rss.yaml` 来开启或关闭特定的 RSS 源
- 系统会定期从配置的 OPML 源获取最新的 RSS 源
- 所有更改都会自动提交到远程仓库，并包含详细的提交信息

这个计划将确保 CTI_bot 能够更加灵活地管理 RSS 源，提高情报收集的效率和可靠性。
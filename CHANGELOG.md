# 更新日志 📝

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 
并遵循 [语义化版本](https://semver.org/lang/zh-CN/)

## [3.0.0] - 2025-12-03

### 🎉 新增

- **GitHub Actions 工作流**
  - 添加了 `add_feed_from_issue.yml` 工作流，支持从 GitHub Issue 提交 Feed 并自动添加到 Feed.csv
  - 添加了 `update_rss_feeds.yml` 工作流，定期从 OPML 源更新 RSS 订阅
  - 增强了 `fetchCTI.yml` 工作流，支持手动触发时配置参数
  - 支持在 GitHub Actions 中使用环境变量配置

- **OPML 转换功能**
  - 新增 `opml_to_rss.py` 脚本，支持将 OPML 文件转换为 RSS 格式
  - 支持本地 OPML 文件和远程 OPML URL
  - 实现了 Feed 去重功能，避免重复添加
  - 支持通过 `config_rss.yaml` 配置多个 OPML 源

- **配置管理增强**
  - 新增 `config_rss.yaml` 文件，用于管理 OPML 源配置
  - 支持通过环境变量覆盖配置文件中的敏感信息
  - 改进了 `config_ransomware.yaml` 的配置逻辑，优先使用环境变量
  - 增强了配置文件的错误处理和兼容性

- **Ransomware.live API PRO 集成**
  - 支持使用 Ransomware.live API PRO 获取更丰富的威胁情报
  - 实现了 API 密钥认证和错误处理
  - 添加了 API 调用失败时的回退机制，自动切换到免费 API
  - 支持通过配置文件设置筛选条件

- **Feed 管理增强**
  - 改进了 `checkFeed.py` 脚本，支持从配置文件读取参数
  - 新增自动移除无效 Feed 功能
  - 生成详细的 Feed 检查报告
  - 支持通过命令行参数控制行为

### 🛠️ 改进

- **代码重构与优化**
  - 增强了 `TeamsIntelBot.py` 的错误处理能力
  - 改进了 API 调用逻辑，添加了超时和重试机制
  - 优化了配置加载流程，支持多种配置方式
  - 改进了钉钉消息推送格式，增强了可读性

- **安全增强**
  - 移除了配置文件中的硬编码敏感信息
  - 优先使用环境变量存储 API 密钥和 Webhook URL
  - 改进了 API 认证方式，使用 X-API-KEY 头部
  - 增强了输入验证和错误处理

- **YAML 语法修复**
  - 修复了 `fetchCTI.yml` 工作流中的多个 YAML 语法错误
  - 统一了 YAML 文件的缩进和格式
  - 增强了 YAML 配置的可读性

### ⚠️ 变更

- 将推送方式从 Microsoft Teams 改为钉钉 webhook+签名
- 更新环境变量名称（MSTEAMS_* 改为 DINGTALK_*）
- 添加钉钉签名密钥验证
- HTML 格式转换为 Markdown 格式以适配钉钉消息规范

## [2.5.0] - 2023-01-11

### 变更

- 重写红旗域名解析器

## [2.4.0] - 2022-10-16

### 变更

- 将 Google 源替换为 Google TAG 源
- 将 Emoji 改为函数形式
- 添加 Unit42 的表情符号

### 新增

- 添加 Google TAG 表情符号
- 添加 MSRC 安全更新源
- 添加 MSRC 安全更新表情符号
- 忽略 [CheckFeed.py](checkFeed.py) 和 [TeamsIntelBot.py](TeamsIntelBot.py) 中以#开头的 Feed 行
- 月度 Feed 提醒（已修复 bug）

## [2.3.0] - 2022-10-15

### 变更

- 一些小的更改

### 新增

- 无

## [2.2.0 未发布] - 2022-08-29

### 变更

- 代码优化

### 新增

- 在.fr域中的勒索软件域名命中添加法国国旗
- Unit42 源
- 数据泄露源（默认禁用）

## [2.1.2 未发布] - 2022-08-23

### 变更

- 修改 Config.txt 格式
- 修改读取 RSS Feed 的顺序

### 新增

- 无

## [2.1.0 未发布] - 2022-08-22

### 变更

- 添加标志以启用红旗域名源

### 新增

- 无

## [2.0.2] - 2022-08-21

### 变更

- 修复调试条件中的 bug

### 新增

- 无

## [2.0.0] - 2022-08-21

### 变更

- 无

### 新增

- 命令行选项
  - 仅屏幕输出的调试模式
  - 静默模式
- 在脚本中检查 Python 版本
- 以及更多功能 :)

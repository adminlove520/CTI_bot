# 基于API PRO的威胁情报推送方案

## 1. 需求分析

用户需要基于 `https://www.ransomware.live/api` 和 `https://api-pro.ransomware.live/docs` 构建威胁情报推送，具体需求包括：
- 使用 API PRO 版本，支持 API 密钥认证
- 根据不同分类让用户有区分度
- 在配置文件里定义所需推送类型
- 支持按国家（如中国）推送
- 支持推送特定类型（如cyberattacks、nego等）

## 2. 现有代码分析

现有 `TeamsIntelBot.py` 代码已经具备：
- 从 `https://data.ransomware.live/posts.json` 获取勒索软件数据的功能 `GetRansomwareUpdates()`
- 向钉钉推送消息的功能 `Send_DingTalk()`
- 使用 `ConfigParser` 读取配置文件 `Config.txt`
- 支持命令行参数和调试模式

## 3. 实现方案

### 3.1 配置文件设计

- 增强现有 `Config.txt` 或创建新的 `config_ransomware.yaml` 文件
- 支持配置 API PRO 密钥
- 支持配置推送分类（国家、攻击类型等）
- 支持配置推送频率和其他参数

### 3.2 API PRO 集成

- 修改 `GetRansomwareUpdates()` 函数，支持 API PRO 调用
- 添加 API 密钥认证支持
- 实现 API 调用重试机制和错误处理
- 支持 API 速率限制处理

### 3.3 分类推送功能

- 实现按国家筛选（如中国）
- 实现按攻击类型筛选（如cyberattacks、nego等）
- 实现按勒索软件组织筛选
- 支持组合筛选条件

### 3.4 数据处理和推送

- 增强数据处理逻辑，支持更多分类字段
- 优化推送消息格式，提高可读性
- 添加分类标签和表情符号，增强区分度
- 支持不同类型数据推送到不同的钉钉机器人

### 3.5 代码结构优化

- 模块化设计，提高代码可维护性
- 添加日志记录，便于调试和监控
- 支持命令行参数配置推送分类
- 保持与现有代码的兼容性

## 4. 技术细节

### 4.1 API PRO 调用示例

```python
def get_ransomware_pro(api_key, filters=None):
    url = "https://api-pro.ransomware.live/v1/posts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = filters or {}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()
```

### 4.2 配置文件示例（YAML格式）

```yaml
ransomware:
  api_key: "your_api_key_here"
  enabled: true
  filters:
    countries: ["China", "US"]
    attack_types: ["cyberattacks", "nego"]
    groups: ["LockBit", "Conti"]
  push_settings:
    webhook_url: "your_dingtalk_webhook"
    secret: "your_dingtalk_secret"
    frequency: "30m"
```

### 4.3 分类标签设计

| 分类类型 | 标签示例 | 表情符号 |
|---------|---------|---------|
| 国家 | 中国 | 🇨🇳 |
|  | 美国 | 🇺🇸 |
| 攻击类型 | cyberattacks | ⚔️ |
|  | nego | 💬 |
| 组织 | LockBit | 🔒 |
|  | Conti | 💣 |

## 5. 实现步骤

1. **增强配置文件支持**
   - 添加 API PRO 密钥配置
   - 添加分类筛选配置
   - 支持 YAML 格式配置文件

2. **集成 API PRO**
   - 修改 `GetRansomwareUpdates()` 函数
   - 添加 API 密钥认证
   - 实现 API 错误处理和重试机制

3. **实现分类筛选功能**
   - 添加国家筛选逻辑
   - 添加攻击类型筛选逻辑
   - 添加组织筛选逻辑

4. **优化推送消息格式**
   - 添加分类标签和表情符号
   - 优化消息结构，提高可读性
   - 支持不同类型数据推送到不同机器人

5. **测试和调试**
   - 测试 API 调用功能
   - 测试分类筛选功能
   - 测试推送功能
   - 调试日志记录

6. **文档更新**
   - 更新 README.md，添加 API PRO 配置说明
   - 添加分类推送配置示例
   - 记录使用方法和注意事项

## 6. 预期效果

- 用户可以在配置文件中灵活定义所需的推送分类
- 支持按国家、攻击类型、组织等多种方式筛选
- 推送消息包含分类标签和表情符号，区分度高
- 使用 API PRO，获取更丰富和及时的威胁情报
- 代码结构清晰，便于维护和扩展

## 7. 风险和应对措施

- **API 速率限制**：实现请求限流和重试机制
- **API 密钥安全**：使用环境变量或加密配置文件存储密钥
- **数据格式变化**：添加数据验证和错误处理
- **推送频率过高**：支持配置推送频率，避免消息轰炸

通过以上方案，我们可以实现基于 API PRO 的威胁情报推送，满足用户的分类推送需求，同时保持与现有代码的兼容性和可扩展性。
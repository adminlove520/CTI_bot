# 基于API PRO的威胁情报推送修复方案

## 1. 问题分析

通过分析API PRO的Swagger文档，我发现了以下关键信息：

### 1.1 API结构
- **主要端点**：
  - `/victims/`：获取受害者列表，支持筛选
  - `/victims/recent`：获取最近受害者
  - `/victims/search`：搜索受害者
  - `/groups`：获取勒索软件组织

### 1.2 筛选参数
- **`group`**：按组织筛选（单个组织名称）
- **`sector`**：按行业筛选（如healthcare）
- **`country`**：按国家筛选（2字母国家代码，如CN）
- **`year`**：按年份筛选
- **`month`**：按月筛选
- **`date`**：日期类型（discovered或attacked）

### 1.3 认证方式
- 使用`X-API-KEY`头，而非`Authorization`头

### 1.4 现有问题
1. **配置文件**：
   - 过滤器字段名不匹配（`countries` → `country`，`attack_types` → `sector`）
   - 敏感信息硬编码

2. **代码问题**：
   - 认证头不正确
   - 端点和参数名不匹配
   - 错误处理不完善

3. **Workflow问题**：
   - 配置文件生成逻辑需要调整
   - 环境变量传递可能有误

## 2. 修复方案

### 2.1 修复配置文件格式

**旧配置**：
```yaml
filters:
  attack_types: []
  countries: []
  groups: []
```

**新配置**：
```yaml
filters:
  group: []       # 按组织筛选
  sector: []      # 按行业筛选
  country: []     # 按国家筛选（2字母代码）
  year: []        # 按年份筛选
  month: []       # 按月筛选
  date: "discovered"  # 日期类型
```

### 2.2 修复代码中的API调用

1. **调整认证头**：
   ```python
   headers = {
       "X-API-KEY": api_key,
       "Content-Type": "application/json"
   }
   ```

2. **修复端点和参数**：
   ```python
   url = "https://api-pro.ransomware.live/victims/"
   params = {}
   if filters.get("group"):
       params["group"] = ",".join(filters["group"])
   if filters.get("sector"):
       params["sector"] = ",".join(filters["sector"])
   if filters.get("country"):
       params["country"] = ",".join(filters["country"])
   ```

3. **增强错误处理**：
   ```python
   try:
       response = requests.get(url, headers=headers, params=params, timeout=10)
       response.raise_for_status()
       data = response.json()
   except requests.RequestException as e:
       print(f"API PRO error: {e}")
       # 回退到免费API
   ```

### 2.3 修复GitHub Actions Workflow

1. **修复配置文件生成**：
   ```yaml
   - name: Create ransomware config
     env:
       RANSOMWARE_API_KEY: ${{ secrets.RANSOMWARE_API_KEY }}
     run: |
       if [ -n "$RANSOMWARE_API_KEY" ]; then
         cat > config_ransomware.yaml << EOF
   ransomware:
     api_key: "$RANSOMWARE_API_KEY"
     enabled: true
     use_pro: true
     filters:
       country: ["CN"]
       sector: ["healthcare", "technology"]
       group: ["Incransom"]
       date: "discovered"
   EOF
       fi
   ```

2. **确保环境变量正确**：
   - 移除配置文件中的硬编码敏感信息
   - 使用GitHub Secrets存储敏感信息

### 2.4 增强代码的灵活性

1. **支持多种筛选条件**：
   - 支持单个或多个筛选值
   - 支持动态生成查询参数

2. **优化数据处理**：
   - 确保代码能处理API返回的各种格式
   - 添加数据验证和转换

3. **增强日志记录**：
   - 添加详细的日志记录，便于调试
   - 记录API调用情况和筛选结果

## 3. 实现步骤

1. **修改TeamsIntelBot.py**：
   - 调整API认证方式
   - 修复端点和参数名
   - 增强错误处理
   - 优化数据处理逻辑

2. **更新配置文件示例**：
   - 创建正确的配置文件示例
   - 移除敏感信息

3. **修复GitHub Actions Workflow**：
   - 修复配置文件生成逻辑
   - 确保环境变量正确传递

4. **测试验证**：
   - 使用调试模式测试API调用
   - 验证筛选功能是否正常
   - 测试回退机制

## 4. 预期效果

- 代码与API PRO完全兼容
- 支持按国家、行业、组织等筛选
- 自动处理API错误，回退到免费API
- Workflow正常运行，无报错
- 配置文件格式正确，支持灵活配置

## 5. 注意事项

- **API密钥安全**：使用GitHub Secrets存储，避免硬编码
- **国家代码格式**：使用2字母ISO代码（如CN、US）
- **行业名称**：使用API支持的行业名称（可从`/listsectors`端点获取）
- **组织名称**：使用准确的勒索软件组织名称
- **错误处理**：确保代码能处理各种API错误情况

通过以上修复，威胁情报推送系统将能够正确使用API PRO，获取更丰富、更准确的威胁情报，并支持灵活的筛选配置。
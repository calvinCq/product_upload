# 火山大模型API配置设计文档

## 整体架构图
```mermaid
flowchart TD
    A[配置来源] -->|配置文件| B[ConfigManager]
    A -->|环境变量| B
    A -->|.env文件| B
    B -->|提供配置| C[VolcanoImageGenerator]
    C -->|生成图片| D[ProductWithImageGenerator]
    B -->|提供配置| E[volcano_generate_tool]
    E -->|使用| D
```

## 分层设计和核心组件
1. **配置层**：包括配置文件、环境变量和.env文件
2. **配置管理层**：ConfigManager类，负责读取和管理配置
3. **服务层**：VolcanoImageGenerator类，使用配置的API key调用火山API
4. **业务层**：ProductWithImageGenerator类，使用VolcanoImageGenerator生成商品图片
5. **应用层**：volcano_generate_tool.py，用户交互入口

## 模块依赖关系
```mermaid
flowchart TD
    A[volcano_generate_tool] -->|依赖| B[ConfigManager]
    A -->|依赖| C[ProductWithImageGenerator]
    C -->|依赖| D[VolcanoImageGenerator]
    D -->|依赖| B
```

## 接口契约定义
1. **ConfigManager**
   - `__init__(config_path=None)`: 初始化配置管理器
   - `load_config()`: 加载配置
   - `get(key, default=None)`: 获取配置项
   - `load_volcano_config()`: 专门加载火山配置，处理优先级

2. **VolcanoImageGenerator**
   - `__init__(config=None, api_key=None)`: 接受配置对象或直接API key

## 数据流向图
```mermaid
sequenceDiagram
    participant User as 用户
    participant Tool as volcano_generate_tool
    participant CM as ConfigManager
    participant VIG as VolcanoImageGenerator
    participant PWG as ProductWithImageGenerator
    
    User->>Tool: 执行命令
    Tool->>CM: 初始化并加载配置
    CM->>CM: 从多源读取配置
    Tool->>PWG: 创建实例
    PWG->>VIG: 创建实例(传递配置)
    VIG->>VIG: 使用配置的API key
```

## 异常处理策略
1. 当无法读取API key时，提供清晰的错误提示
2. 配置文件不存在时，使用默认配置或从其他来源获取
3. 提供配置验证机制，确保必要的配置项存在
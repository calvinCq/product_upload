# 测试图片生成和商品上传功能设计文档

## 1. 整体架构

```mermaid
flowchart TD
    A[测试入口脚本] --> B[图片生成测试]
    A --> C[商品上传测试]
    B --> D[火山大模型API]
    C --> E[微信小店API]
    B --> F[图片存储]
    C --> F
    G[配置管理器] --> B
    G --> C
```

## 2. 模块设计

### 2.1 图片生成测试模块

**功能**：测试火山大模型图片生成功能

**输入**：
- 商品描述文本
- 图片生成配置（模型名称、数量、类型等）

**输出**：
- 生成的图片文件路径
- 测试结果状态（成功/失败）
- 错误信息（如果有）

### 2.2 商品上传测试模块

**功能**：测试商品信息和图片上传到微信小店

**输入**：
- 商品信息（名称、价格、描述等）
- 商品图片路径

**输出**：
- 上传结果状态（成功/失败）
- 商品ID（如果上传成功）
- 错误信息（如果有）

## 3. 测试流程

### 3.1 准备阶段

1. 加载配置（从.env文件或其他配置源）
2. 验证必要的API密钥是否存在
3. 创建临时目录用于存储生成的图片

### 3.2 图片生成测试流程

```mermaid
sequenceDiagram
    participant T as 测试脚本
    participant V as VolcanoImageGenerator
    participant API as 火山大模型API
    participant FS as 文件系统
    
    T->>V: 初始化（提供配置）
    T->>V: generate_product_images(商品描述)
    V->>API: 发送图片生成请求
    API-->>V: 返回任务ID
    V->>API: 查询任务状态
    API-->>V: 返回生成的图片数据
    V->>FS: 保存图片到文件
    V-->>T: 返回图片路径列表
    T->>T: 验证图片是否生成成功
```

### 3.3 商品上传测试流程

```mermaid
sequenceDiagram
    participant T as 测试脚本
    participant P as ProductWithImageGenerator
    participant V as VolcanoImageGenerator
    participant W as WechatShopAPI
    participant API as 微信小店API
    
    T->>P: 初始化（提供配置）
    T->>P: generate_images_and_upload_product(商品信息)
    P->>V: 生成图片
    V-->>P: 返回图片路径
    P->>W: 上传图片
    W->>API: 调用图片上传接口
    API-->>W: 返回图片URL
    W-->>P: 返回图片URL列表
    P->>P: 更新商品数据，添加图片URL
    P->>W: 上传商品信息
    W->>API: 调用商品上传接口
    API-->>W: 返回上传结果
    W-->>P: 返回上传结果
    P-->>T: 返回最终结果
```

## 4. 接口设计

### 4.1 测试入口接口

```python
def test_image_generation():
    """
    测试图片生成功能
    Returns:
        dict: 包含测试结果、图片路径等信息
    """
    pass

def test_product_upload(image_paths=None):
    """
    测试商品上传功能
    Args:
        image_paths: 可选，图片路径列表
    Returns:
        dict: 包含上传结果、商品ID等信息
    """
    pass

def run_complete_test():
    """
    运行完整的测试流程（图片生成 + 商品上传）
    Returns:
        dict: 包含完整测试结果
    """
    pass
```

## 5. 数据流向

1. 配置数据 → 配置管理器 → 图片生成器/商品上传器
2. 商品描述 → 图片生成器 → 火山大模型API → 生成的图片
3. 图片文件 → 商品上传器 → 微信小店API
4. 商品信息 + 图片URL → 商品上传器 → 微信小店API
5. 测试结果 → 测试报告

## 6. 异常处理策略

- API调用失败：记录详细错误信息，支持重试机制
- 配置缺失：提供明确的错误提示，指导用户正确配置
- 图片生成失败：检查参数和网络连接，记录详细日志
- 上传失败：区分不同类型的错误（参数错误、权限不足、网络问题等）
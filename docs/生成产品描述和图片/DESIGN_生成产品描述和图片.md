# 任务设计文档：使用钱多多API生成产品描述和图片

## 整体架构图
```mermaid
flowchart TD
    A[用户] -->|执行脚本| B[process_product_description.py]
    B -->|解析文件| C[sample_product_description.txt]
    B -->|创建生成器| D[ProductGenerator]
    D -->|调用API| E[钱多多API]
    E -->|图片生成| F[doubao-seedream-4-0-250828模型]
    E -->|文案提取| G[DeepSeek-V3.1模型]
    D -->|生成商品数据| H[生成的商品信息]
    H -->|保存| I[output目录]
    B -->|上传| J[商品上传]
```

## 分层设计
1. **配置层**：.env文件存储API配置和模型选择
2. **API层**：src/api/qianduoduo_api.py封装API调用
3. **核心层**：src/core/product_generator.py实现产品生成逻辑
4. **流程层**：process_product_description.py协调整体流程

## 模块依赖关系
```mermaid
graph LR
    A[.env] --> B[config_manager.py]
    B --> C[product_generator.py]
    B --> D[qianduoduo_api.py]
    D --> C
    C --> E[process_product_description.py]
```

## 接口契约定义
1. **钱多多API接口**
   - 图片生成接口：
     - 输入：模型名称、提示词、参数
     - 输出：生成的图片URL或base64
   - 文案提取接口：
     - 输入：模型名称、原始文本、参数
     - 输出：提取的文案

2. **ProductGenerator类**
   - generate_product_images方法：
     - 输入：商品数据
     - 输出：图片列表
   - generate_product_description方法：
     - 输入：客户数据
     - 输出：商品描述

## 数据流向
1. 从sample_product_description.txt读取数据
2. 通过process_product_description.py解析并转换为客户数据
3. 客户数据传入ProductGenerator
4. ProductGenerator调用钱多多API生成图片和提取文案
5. 生成完整商品信息并保存到output目录

## 异常处理策略
1. API调用异常：使用@catch_exceptions装饰器捕获并记录
2. 配置缺失：提供默认值并记录警告
3. 文件操作异常：捕获并提供友好错误信息
4. 参数验证：在方法入口处验证参数有效性
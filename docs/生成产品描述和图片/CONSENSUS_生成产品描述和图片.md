# 任务共识文档：使用钱多多API生成产品描述和图片

## 明确的需求描述
1. 更新.env文件，配置钱多多API使用指定模型：
   - 图片生成：doubao-seedream-4-0-250828
   - 文案提取：DeepSeek-V3.1
2. 修改src目录下的代码，集成钱多多API：
   - 确保qianduoduo_api.py能使用指定模型
   - 更新product_generator.py以支持新的模型配置
3. 从sample_product_description.txt读取产品信息
4. 生成产品描述和图片
5. 保存生成的文件并添加商品

## 技术实现方案
1. 修改.env文件，添加/更新模型配置
2. 更新src/api/qianduoduo_api.py，支持指定模型调用
3. 修改src/core/product_generator.py，确保与钱多多API正确集成
4. 确保process_product_description.py能正确处理流程

## 技术约束和集成方案
- 必须使用钱多多API
- 图片生成使用doubao-seedream-4-0-250828模型
- 文案提取使用DeepSeek-V3.1模型
- 所有修改限制在src目录内
- 保持与现有代码结构一致

## 任务边界限制
- 不创建新的测试文件
- 不修改项目整体架构
- 专注于API配置和集成

## 验收标准
1. .env文件包含正确的模型配置
2. 系统能成功调用钱多多API，使用指定模型
3. 从sample_product_description.txt读取并生成产品信息
4. 成功生成产品描述和图片
5. 生成的文件保存到output目录
6. 商品添加成功
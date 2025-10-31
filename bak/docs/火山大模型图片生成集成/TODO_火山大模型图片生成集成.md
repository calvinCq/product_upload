# 火山大模型图片生成集成待办事项

## 必要配置（必须完成）

### 1. 火山大模型API配置

- [ ] **API密钥配置**：设置环境变量 `VOLCANO_API_KEY` 或在配置文件中配置
  ```bash
  # Windows 命令行设置环境变量
  set VOLCANO_API_KEY=your_volcano_api_key_here
  
  # 或者在配置文件中添加（不推荐，出于安全考虑）
  ```

- [ ] **配置文件验证**：确保配置文件包含火山大模型相关配置段
  ```json
  {
    "volcano_api": {
      "api_key": "your_api_key",
      "api_base_url": "https://api.volcengine.com/ark/v3",
      "model_version": "stable-diffusion-v1.5",
      "main_images_count": 3,
      "detail_images_count": 2
    }
  }
  ```

### 2. 微信小店API配置

- [ ] **确认微信小店API配置正确**：确保已配置 `app_id`, `app_secret`, `access_token` 等必要信息
- [ ] **权限验证**：确保微信小店API账号具有商品上传和图片上传的权限

## 功能测试与验证

### 1. 图片生成测试

- [ ] **基本功能测试**：运行命令测试图片生成功能
  ```bash
  python volcano_generate_tool.py --generate-images --description "测试商品描述"
  ```

- [ ] **生成质量验证**：检查生成的图片是否符合预期质量
- [ ] **格式要求检查**：验证生成的图片是否满足微信小店的图片要求（尺寸、大小、格式）

### 2. 商品上传测试

- [ ] **传统小店上传测试**：测试向传统小店上传商品
  ```bash
  python volcano_generate_tool.py --generate-and-upload \
    --description "测试商品描述" \
    --shop-type traditional \
    --product-data test_data/example_product.json
  ```

- [ ] **视频号小店上传测试**：测试向视频号小店上传商品
  ```bash
  python volcano_generate_tool.py --generate-and-upload \
    --description "测试商品描述" \
    --shop-type video_shop \
    --product-data test_data/example_product_video.json
  ```

## 系统配置与环境

### 1. 依赖安装

- [ ] **安装所需依赖**：确保安装了所有必要的Python库
  ```bash
  pip install requests pillow python-dotenv
  ```

### 2. 目录结构

- [ ] **创建图片保存目录**：确保图片保存目录存在并有写入权限
  ```bash
  mkdir -p generated_images
  ```

## 已知限制与后续优化

### 1. 限制

- **API请求频率**：火山大模型API可能有请求频率限制，需注意批量操作时的间隔时间
- **图片生成时间**：生成多张图片可能需要较长时间，请耐心等待
- **生成质量**：图片质量受输入描述的详细程度影响，建议提供具体、详细的描述

### 2. 后续优化建议

- [ ] 实现图片格式自动转换，确保符合微信小店要求
- [ ] 添加图片生成进度显示功能
- [ ] 实现批量商品生成和上传功能
- [ ] 添加错误重试和断点续传机制
- [ ] 优化提示词工程，提高生成图片的质量

## 紧急支持联系

如果在配置或使用过程中遇到问题，请联系：
- 技术支持邮箱：support@example.com
- 紧急问题处理电话：+86-xxx-xxxxxxx
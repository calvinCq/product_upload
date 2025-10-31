# 微信小店商品自动生成与上传 - 待办事项

## 1. 环境配置待办

### 1.1 环境变量配置

- [ ] 创建 `.env` 文件，配置以下敏感信息：
  ```
  WECHAT_APPID=您的微信小程序AppID
  WECHAT_APPSECRET=您的微信小程序AppSecret
  WECHAT_API_KEY=您的API密钥（如有）
  ```
- [ ] 确保 `.env` 文件已添加到 `.gitignore` 中，避免敏感信息泄露

### 1.2 依赖安装

- [ ] 安装必要的Python依赖包：
  ```bash
  pip install requests python-dotenv
  ```

## 2. 配置文件设置

### 2.1 配置文件修改

- [ ] 根据您的实际需求修改 `product_generator_config.json` 中的配置：
  - [ ] 设置正确的商品类目ID (`category_ids`)
  - [ ] 调整价格范围 (`price_range`) 和库存范围 (`stock_range`)
  - [ ] 配置合理的请求间隔 (`request_interval`) 避免API限流
  - [ ] 设置适当的批量大小 (`batch_size`)

### 2.2 图片资源准备

- [ ] 准备默认主图URL，确保图片可访问且符合微信小店要求
- [ ] 如需生成更多商品图片，请调整相关配置

## 3. API权限确认

- [ ] 确认微信小程序已开通微信小店功能
- [ ] 验证小程序是否有权限调用以下接口：
  - `/shop/product/add` (商品上传接口)
  - `/shop/vip/getvipuserscore` (积分查询接口)
  - `/cgi-bin/token` (获取access_token接口)
  - `/shop/category/get` (获取指定分类接口)
  - `/shop/category/getall` (获取所有分类接口)
- [ ] 确认已完成相关资质认证

### 3.1 API配置完善

- [x] 在`.env`文件中配置正确的API参数：
  ```
  APPID=your_app_id_here
  APPSECRET=your_app_secret_here
  API_BASE_URL=https://api.weixin.qq.com
  ```

- [x] 在wechat_shop_api.py中定义`API_PATHS`常量，并更新为正确的API路径：
  ```python
  API_PATHS = {
      'access_token': '/cgi-bin/token',
      'get_vip_user_score': '/shop/vip/getvipuserscore',
      'get_category': '/merchant/category/get',
      'get_all_category': '/merchant/category/getall',
      'get_channels_category_all': '/channels/ec/category/all'
  }
  ```

- [x] 在WeChatShopAPIClient类中实现`_record_operation`方法用于记录API操作日志

- [x] ✅ 视频号小店类目API路径已解决
  - 已更新为微信官方文档指定的正确API路径：`/channels/ec/category/all`
  - API调用已成功返回数据，errcode=0，errmsg="ok"
  - 返回了完整的三级类目结构和资质要求信息
  - 类目数据已保存到`wechat_shop_channels_category_result.json`
- [ ] ⚠️ 传统微信小店类目API路径问题
  - 路径：`/merchant/category/getall` 仍返回40066: invalid url错误
  - 可能需要不同的基础URL或已被弃用
  - 建议优先使用已验证成功的视频号小店类目API

## 4. 测试验证

### 4.1 功能验证

- [ ] 在正式使用前，建议先进行小规模测试：
  ```bash
  # 先生成少量商品（如2个）
  python auto_product_manager.py generate --config product_generator_config.json --output test_products.json
  
  # 再上传测试
  python auto_product_manager.py upload --config product_generator_config.json --input test_products.json
  ```

### 4.2 积分查询验证

- [ ] 准备测试用的用户openid列表
- [ ] 执行积分查询测试：
  ```bash
  # 单个用户测试
  python auto_product_manager.py score --config product_generator_config.json --openid 测试用户的openid
  ```

### 4.3 单元测试完善

- [ ] 为关键功能编写单元测试，特别是ProductGenerator、ProductUploader和VipScoreManager
- [ ] 使用mock模拟API调用，避免依赖真实环境

## 5. 后续优化建议

### 5.1 功能扩展

- [ ] 考虑添加单元测试和集成测试
- [ ] 实现定时任务功能，支持自动化调度
- [ ] 增加更多商品模板和生成规则
- [ ] 开发GUI界面提升用户体验

### 5.2 配置优化

- [ ] 根据实际使用情况，持续优化API调用参数：
  - 请求间隔
  - 批量大小
  - 超时设置
  - 重试策略

### 5.3 错误信息增强

- [ ] 优化商品上传失败时的错误信息，提供更具体的错误原因
- [ ] 建议在上传失败时检查HTTP响应状态和详细错误内容

### 5.4 并发性能优化

- [ ] 考虑实现更高效的并发上传机制，提高批量处理速度
- [ ] 实现动态调整上传间隔的功能，适应不同的网络环境

### 5.5 异常恢复机制

- [ ] 实现断点续传功能，允许在程序中断后从上次失败的地方继续上传
- [ ] 增加定时备份功能，保存生成的商品数据

## 6. 注意事项

- **API调用频率**：请遵守微信小店API的调用频率限制，避免频繁调用导致账号受限
- **商品数据**：生成的商品数据需要符合微信小店的审核规范
- **错误处理**：遇到错误时，请查看日志输出和生成的报告
- **备份**：定期备份配置文件和重要数据
- **API密钥安全**：确保敏感信息不被记录到日志中，实现API密钥的加密存储和安全传输

## 7. 后续开发建议

- [ ] 考虑开发简单的Web界面，方便非技术人员使用
- [ ] 实现可视化的配置管理和结果查看功能
- [ ] 添加上传失败率监控和告警功能
- [ ] 实现定期自动执行和状态报告发送功能

## 8. 文档更新

- [ ] 更新README.md，添加详细的使用说明和配置示例
- [ ] 提供常见问题解答(FAQ)部分
- [ ] 根据最新的微信小店API规范更新代码和文档

## 9. 紧急联系

如遇到无法解决的问题，请联系开发团队获取技术支持。
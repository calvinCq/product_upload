# 待办事项清单

## 配置项

### 1. 微信小店API配置

- 需要在`.env`文件中配置以下环境变量：
  ```
  WECHAT_APP_ID=你的微信小程序APPID
  WECHAT_APP_SECRET=你的微信小程序APP_SECRET
  WECHAT_API_BASE_URL=https://api.weixin.qq.com/shop/goods
  ```

### 2. 图片验证配置

- 默认图片URL验证是启用的，如需禁用请修改`run_product_pipeline.py`中的`verify_image_url`参数为`False`

### 3. 上传参数配置

- 上传重试次数默认为3次，可在`ProductUploader`类初始化时调整
- 批量上传时的并发数默认为3，可根据API限流调整

## 待办事项

### 1. 环境配置检查

- [ ] 确保安装了所有必需的依赖：`pip install -r requirements.txt`
- [ ] 验证`.env`文件中的API配置是否正确
- [ ] 确认`output`目录有写入权限

### 2. 功能验证

- [ ] 首次使用时请先进行连接测试：`python run_product_pipeline.py --test-connection`
- [ ] 上传前请检查生成的CSV文件格式是否符合预期
- [ ] 对于批量操作，建议先上传单个商品进行测试

### 3. 后续优化建议

- [ ] 考虑添加更多的错误处理和恢复机制
- [ ] 实现批量商品处理功能
- [ ] 定期清理`output`目录中不需要的历史文件
- [ ] 增加更详细的日志记录功能

### 4. 注意事项

- CSV文件中的描述字段包含多行文本时，已自动用引号包裹，请不要手动修改
- 图片URL必须是公网可访问的，否则会上传失败
- 请确保商品类目ID与微信小店后台配置一致
- 上传成功后，建议在微信小店后台确认商品信息

### 5. 联系方式

如有问题，请联系：
- 技术支持：[支持邮箱]
- 文档更新：[文档维护者]
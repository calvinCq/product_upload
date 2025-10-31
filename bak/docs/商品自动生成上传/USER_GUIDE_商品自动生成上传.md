# 微信小店商品自动生成与上传工具

## 1. 工具概述

本工具是一个用于微信小店商品自动生成和上传的自动化工具，支持批量生成商品信息、自动上传至微信小店，并提供用户积分查询功能。

### 1.1 核心功能

- **商品信息自动生成**：根据配置生成符合微信小店API要求的商品数据
- **商品自动上传**：将生成的商品数据上传至微信小店
- **用户积分查询**：支持单个或批量查询用户的积分信息
- **完整工作流**：提供一键式生成并上传的功能
- **报告生成**：生成上传和积分查询的详细报告

## 2. 安装与环境配置

### 2.1 系统要求

- Python 3.7+
- 依赖库：requests, python-dotenv, argparse, json, logging

### 2.2 安装步骤

1. 克隆或下载项目到本地
2. 安装依赖：

```bash
pip install requests python-dotenv
```

3. 配置环境变量（.env文件）：

```
# .env文件内容
WECHAT_APPID=your_appid
WECHAT_APPSECRET=your_appsecret
WECHAT_API_KEY=your_api_key
```

## 3. 配置文件说明

### 3.1 配置文件结构

配置文件 `product_generator_config.json` 包含以下主要部分：

- `generation`: 商品生成相关配置
- `upload`: 上传相关配置
- `api`: API调用相关配置
- `vip_score`: 积分查询相关配置

### 3.2 配置项详细说明

#### 3.2.1 商品生成配置 (generation)

```json
{
  "product_count": 10,
  "category_ids": ["10001", "10002"],
  "price_range": [10.0, 999.99],
  "stock_range": [1, 1000],
  "title_prefix": "自动生成商品",
  "description_template": "这是一个自动生成的商品描述",
  "main_image_url": "https://example.com/default.jpg",
  "sku_enabled": true,
  "random_title": true,
  "generate_images": true
}
```

- `product_count`: 要生成的商品数量
- `category_ids`: 商品类目ID列表
- `price_range`: 价格范围 [最小值, 最大值]
- `stock_range`: 库存范围 [最小值, 最大值]
- `title_prefix`: 商品标题前缀
- `description_template`: 商品描述模板
- `main_image_url`: 默认主图URL
- `sku_enabled`: 是否启用SKU
- `random_title`: 是否使用随机标题
- `generate_images`: 是否生成随机图片URL

#### 3.2.2 上传配置 (upload)

```json
{
  "batch_size": 10,
  "request_interval": 1,
  "timeout": 30,
  "retry_count": 3,
  "async_mode": true,
  "save_results": true,
  "results_dir": "./results"
}
```

- `batch_size`: 批量上传时每批的数量
- `request_interval`: 请求间隔（秒）
- `timeout`: 请求超时时间（秒）
- `retry_count`: 失败重试次数
- `async_mode`: 是否使用异步上传模式
- `save_results`: 是否保存上传结果
- `results_dir`: 结果保存目录

#### 3.2.3 API配置 (api)

```json
{
  "appid": "",
  "use_env_for_appid": true,
  "base_url": "https://api.weixin.qq.com",
  "upload_endpoint": "/shop/product/add",
  "access_token_endpoint": "/cgi-bin/token"
}
```

- `appid`: 微信小程序AppID（如果不使用环境变量）
- `use_env_for_appid`: 是否从环境变量读取AppID
- `base_url`: API基础URL
- `upload_endpoint`: 上传接口路径
- `access_token_endpoint`: 获取access_token的接口路径

#### 3.2.4 积分配置 (vip_score)

```json
{
  "enabled": true,
  "endpoint": "/shop/vip/getvipuserscore",
  "batch_query_size": 50,
  "save_reports": true,
  "report_dir": "./reports"
}
```

- `enabled`: 是否启用积分功能
- `endpoint`: 积分查询接口路径
- `batch_query_size`: 批量查询时每批的用户数量
- `save_reports`: 是否保存积分报告
- `report_dir`: 报告保存目录

## 4. 使用方法

### 4.1 命令行参数

主程序 `auto_product_manager.py` 支持以下子命令：

```
auto_product_manager.py [command] [options]
```

### 4.2 子命令说明

#### 4.2.1 generate - 生成商品数据

```bash
python auto_product_manager.py generate [--config CONFIG_FILE] [--output OUTPUT_FILE]
```

参数：
- `--config, -c`: 配置文件路径（默认：product_generator_config.json）
- `--output, -o`: 输出文件路径（默认：generated_products.json）

#### 4.2.2 upload - 上传商品数据

```bash
python auto_product_manager.py upload [--config CONFIG_FILE] [--input INPUT_FILE]
```

参数：
- `--config, -c`: 配置文件路径（默认：product_generator_config.json）
- `--input, -i`: 输入文件路径（默认：generated_products.json）

#### 4.2.3 score - 查询用户积分

```bash
python auto_product_manager.py score [--config CONFIG_FILE] [--openid OPENID | --file FILE]
```

参数：
- `--config, -c`: 配置文件路径（默认：product_generator_config.json）
- `--openid, -o`: 单个用户openid
- `--file, -f`: 包含多个openid的文件路径

#### 4.2.4 auto - 自动生成并上传

```bash
python auto_product_manager.py auto [--config CONFIG_FILE]
```

参数：
- `--config, -c`: 配置文件路径（默认：product_generator_config.json）

#### 4.2.5 config - 查看或验证配置

```bash
python auto_product_manager.py config [--config CONFIG_FILE] [--validate]
```

参数：
- `--config, -c`: 配置文件路径（默认：product_generator_config.json）
- `--validate, -v`: 验证配置有效性

#### 4.2.6 validate - 验证商品数据

```bash
python auto_product_manager.py validate [--input INPUT_FILE]
```

参数：
- `--input, -i`: 输入文件路径

## 5. 示例使用场景

### 5.1 生成10个商品数据

```bash
python auto_product_manager.py generate --config product_generator_config.json --output my_products.json
```

### 5.2 上传生成的商品

```bash
python auto_product_manager.py upload --config product_generator_config.json --input my_products.json
```

### 5.3 查询单个用户积分

```bash
python auto_product_manager.py score --config product_generator_config.json --openid oxxxxxxx
```

### 5.4 查询多个用户积分

```bash
python auto_product_manager.py score --config product_generator_config.json --file openids.txt
```

### 5.5 一键式自动生成并上传

```bash
python auto_product_manager.py auto --config product_generator_config.json
```

### 5.6 验证配置

```bash
python auto_product_manager.py config --config product_generator_config.json --validate
```

## 6. 输出结果说明

### 6.1 生成结果

- 生成的商品数据保存在指定的输出文件中（默认为 `generated_products.json`）

### 6.2 上传结果

- 上传结果保存在配置的 `results_dir` 目录下
- 文件名格式：`upload_results_YYYYMMDD_HHMMSS.json`
- 包含成功和失败的商品列表

### 6.3 积分查询结果

- 积分查询报告保存在配置的 `report_dir` 目录下
- 文件名格式：`vip_score_report_YYYYMMDD_HHMMSS.json`
- 包含用户openid和对应的积分信息

## 7. 错误处理

程序会在以下情况输出错误信息：

- 配置文件不存在或格式错误
- API调用失败（网络问题、认证错误等）
- 商品数据验证失败
- 参数错误

请根据错误信息检查相应的配置或参数。

## 8. 注意事项

1. 确保 `.env` 文件中的敏感信息正确配置
2. 避免频繁调用API，建议设置合理的 `request_interval`
3. 对于大量商品上传，建议使用异步模式 `async_mode: true`
4. 定期检查上传和积分查询报告
5. 确保网络环境可以正常访问微信API

## 9. 扩展与定制

### 9.1 添加新的商品生成规则

可以修改 `product_generator.py` 中的 `_generate_single_product` 方法，添加更多的商品属性生成规则。

### 9.2 自定义报告格式

可以修改 `product_uploader.py` 和 `vip_score_manager.py` 中的报告生成相关方法，自定义报告格式。

### 9.3 添加新的API集成

可以扩展 `ConfigManager` 类和相应的业务类，添加新的API集成。

## 10. 故障排除

### 10.1 常见问题

1. **API调用失败**
   - 检查网络连接
   - 验证AppID和密钥是否正确
   - 确认API权限是否开启

2. **商品上传失败**
   - 检查商品数据格式是否符合微信小店要求
   - 验证类目ID是否正确
   - 检查图片URL是否可访问

3. **积分查询失败**
   - 验证用户openid是否正确
   - 确认积分功能是否已开通

4. **配置文件读取错误**
   - 检查文件路径是否正确
   - 验证JSON格式是否有效

## 11. 联系与支持

如有问题或建议，请联系开发团队。
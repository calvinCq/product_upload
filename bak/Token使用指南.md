# Token使用指南

本文档提供了如何获取微信API的access_token并使用它进行请求的详细步骤。

## 准备工作

1. **获取AppID和AppSecret**：
   - 登录微信公众平台 (https://mp.weixin.qq.com/)
   - 在「开发」-「基本配置」中获取AppID和AppSecret
   - 确保公众号已通过认证，否则某些API可能无法使用

## 脚本说明

本项目提供了三个相关脚本：

### 1. print_token.py - 打印Token

最简单的脚本，专门用于获取并打印access_token。

**使用方法**：

1. 编辑脚本，填写正确的AppID和AppSecret
2. 运行脚本：
   ```bash
   python print_token.py
   ```
3. 脚本会：
   - 获取access_token
   - 打印token信息（包括有效期和过期时间）
   - 将token保存到token_info.json文件

### 2. use_token.py - 使用Token

专门用于使用已有的access_token进行API请求的交互式脚本。

**使用方法**：

```bash
# 方法1：运行时输入token
python use_token.py

# 方法2：命令行参数传递token
python use_token.py your_access_token_here
```

**功能**：
- 支持测试多个常用API
- 交互式选择要调用的API
- 显示API响应结果
- 对于大数据量的响应，自动保存到文件

### 3. get_and_use_token.py - 完整工具

综合工具，包含获取token、保存token、使用token测试多个API的功能。

**使用方法**：

1. 编辑脚本，填写正确的AppID和AppSecret
2. 运行脚本：
   ```bash
   python get_and_use_token.py
   ```

**功能**：
- 获取并打印access_token
- 保存token到文件
- 使用token测试通用API
- 使用token测试类目API

## 使用示例

### 示例1：获取并打印Token

```bash
# 1. 编辑print_token.py，填入AppID和AppSecret
# 2. 运行脚本
python print_token.py

# 输出示例:
=============================================
          微信API Token打印工具
=============================================

正在请求token...
请求URL: https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx123456&secret=abcdef

✅ Token获取成功!

📋 Token信息:
┌───────────────────────────────────────────
│ Access Token: 12_YOUR_TOKEN_HERE_789012
├───────────────────────────────────────────
│ 有效期: 7200 秒
├───────────────────────────────────────────
│ 过期时间戳: 1719603600
└───────────────────────────────────────────

🕒 过期时间: 2024-07-01 12:00:00

💾 Token已保存到 token_info.json
```

### 示例2：使用Token请求API

```bash
# 运行use_token.py脚本
python use_token.py 12_YOUR_TOKEN_HERE_789012

# 输出示例:
=============================================
       使用access_token进行API请求
=============================================

使用的access_token: 12_YOUR_TOKEN_HERE_789012

请选择要测试的API:
1. 获取微信服务器IP地址
2. 获取视频号小店类目信息
3. 退出

请输入选择 (1-3): 2

正在调用 获取视频号小店类目信息 API...
请求URL: https://api.weixin.qq.com/channels/ec/category/all?access_token=12_YOUR_TOKEN_HERE_789012

✅ API调用完成，响应结果:
  状态码: 200
  errcode: 0
  errmsg: ok
  cats数组长度: 10
  cats_v2数组长度: 15

💾 完整响应已保存到 use_token_category_result.json
```

## 注意事项

1. **安全性**：
   - access_token是敏感信息，请妥善保管
   - 不要在公开场合分享您的token或AppSecret
   - 保存token的文件请妥善管理，避免泄露

2. **有效期**：
   - access_token有效期为2小时（7200秒）
   - 过期后需要重新获取

3. **权限问题**：
   - 某些API需要特定权限才能调用
   - 如果遇到权限相关错误，请检查公众号权限设置

4. **频率限制**：
   - 获取access_token有调用频率限制
   - 请合理缓存和使用token，避免频繁请求

## 故障排除

**常见错误及解决方案**：

1. **40013错误 - invalid appid**
   - 检查AppID是否正确
   - 确认没有多余的空格或特殊字符

2. **40164错误 - invalid ip xxx, not in whitelist**
   - 需要在微信公众平台设置IP白名单
   - 前往「开发」-「基本配置」-「IP白名单」添加您的服务器IP

3. **41001错误 - access_token missing**
   - 确认在API请求中正确传递了access_token参数

4. **42001错误 - access_token expired**
   - access_token已过期，需要重新获取

如有其他问题，请参考微信公众平台官方文档或检查错误码说明。
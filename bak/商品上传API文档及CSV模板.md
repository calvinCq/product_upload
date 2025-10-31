# 微信视频号小店商品上传API文档与CSV模板

## 1. API接口概述

**接口名称**: addproduct
**接口路径**: /channels/ec/product/add
**调用方式**: POST
**调用环境**: 服务器端调用
**权限要求**: 需要微信小店相关权限集ID 129

## 2. 必需参数说明

### 2.1 查询参数（Query String）
- **access_token**: 接口调用凭证，必需

### 2.2 请求体参数（Request Payload）

#### 核心必需字段：

| 参数名 | 类型 | 是否必填 | 说明 | 示例值 |
|-------|------|---------|------|--------|
| title | string | 是 | 商品标题，至少5个有效字符，最多60字符 | 商业模式重构：线上生意破局 |
| head_imgs | array | 是 | 主图，最少3张（食品饮料和生鲜类目最少4张），最多9张 | ["https://example.com/img1.jpg", ...] |
| deliver_method | number | 是 | 发货方式：0-快递发货；1-无需快递，手机号发货；3-无需快递，可选发货账号类型 | 0 |
| cats | array | 是 | 商品类目（旧版），大小恒等于3（一二三级类目） | [{"cat_id":"381003"}, {"cat_id":"380003"}, {"cat_id":"517050"}] |
| cats_v2 | array | 是 | 商品类目（新版），多级类目结构 | [{"cat_id":"381003"}, {"cat_id":"380003"}, {"cat_id":"517050"}] |
| extra_service | object | 是 | 额外服务 | {"service_tags":[]} |
| skus | array | 是 | 商品SKU，最少1个，最多500个 | [{"price":800,"stock_num":100,"out_sku_id":"SKU001"}] |

#### 条件必填字段：

| 参数名 | 类型 | 条件 | 说明 | 示例值 |
|-------|------|------|------|--------|
| deliver_acct_type | numarray | deliver_method=3时必需 | 发货账号：1-微信openid；2-QQ号；3-手机号；4-邮箱 | [3] |
| desc_info | object | 是 | 商品详情 | {"imgs":["https://example.com/desc1.jpg"], "desc":"商品描述文本"} |
| express_info | object | deliver_method=0时必需 | 运费信息 | {"express_type":0, "template_id":"template123"} |

## 3. CSV文件模板设计

### 3.1 CSV文件结构

由于微信小店API参数结构复杂，我们设计一个简化的CSV模板，主要包含核心商品信息：

```csv
商品标题,副标题,短标题,商品描述,发货方式,一级类目ID,二级类目ID,三级类目ID,主图1,主图2,主图3,主图4,主图5,主图6,主图7,主图8,主图9,详情图1,详情图2,详情图3,SKU价格(分),SKU库存,SKU编码,上架状态
```

### 3.2 CSV字段说明

| CSV列名 | 对应API字段 | 说明 | 示例值 |
|--------|------------|------|--------|
| 商品标题 | title | 商品标题，必填，5-60字符 | 商业模式重构：线上生意破局 |
| 副标题 | sub_title | 商品副标题，选填，最多18字符 | 线上营销领域实战指南 |
| 短标题 | short_title | 商品短标题，选填，最多20字符 | 商业模式重构 |
| 商品描述 | desc_info.desc | 商品描述文本，选填 | 本课程将帮助您重构商业模式... |
| 发货方式 | deliver_method | 0-快递发货；1-无需快递手机号发货；3-无需快递可选账号 | 0 |
| 一级类目ID | cats[0].cat_id | 一级类目ID，必填 | 381003 |
| 二级类目ID | cats[1].cat_id | 二级类目ID，必填 | 380003 |
| 三级类目ID | cats[2].cat_id | 三级类目ID，必填 | 517050 |
| 主图1-9 | head_imgs[] | 商品主图URL，至少3张，最多9张 | https://example.com/img1.jpg |
| 详情图1-3 | desc_info.imgs[] | 商品详情图URL，至少1张 | https://example.com/desc1.jpg |
| SKU价格(分) | skus[0].price | 商品价格，单位分，必填 | 800 |
| SKU库存 | skus[0].stock_num | 商品库存，必填 | 100 |
| SKU编码 | skus[0].out_sku_id | 商家自定义SKU编码，选填 | SKU001 |
| 上架状态 | listing | 1-立即上架；0-不上架 | 0 |

## 4. 商品上传流程

### 4.1 从CSV到API请求的转换步骤

1. **读取CSV文件**：使用pandas或csv模块读取CSV数据
2. **数据验证**：检查必填字段是否完整，格式是否正确
3. **构建API请求参数**：
   - 将CSV行数据转换为符合API要求的JSON结构
   - 处理数组字段（如图片、类目、SKU等）
   - 设置默认值（如extra_service等）
4. **获取access_token**：使用appid和appsecret获取调用凭证
5. **发送API请求**：调用addproduct接口上传商品
6. **处理响应结果**：保存上传成功或失败的商品信息

### 4.2 数据转换示例

CSV行数据：
```
商业模式重构：线上生意破局,线上营销领域实战指南,商业模式重构,本课程将帮助您重构商业模式,0,381003,380003,517050,https://example.com/img1.jpg,https://example.com/img2.jpg,https://example.com/img3.jpg,,,,,,,,https://example.com/desc1.jpg,,,800,100,SKU001,0
```

转换后的API请求参数：
```json
{
  "title": "商业模式重构：线上生意破局",
  "sub_title": "线上营销领域实战指南",
  "short_title": "商业模式重构",
  "desc_info": {
    "imgs": ["https://example.com/desc1.jpg"],
    "desc": "本课程将帮助您重构商业模式"
  },
  "head_imgs": [
    "https://example.com/img1.jpg",
    "https://example.com/img2.jpg",
    "https://example.com/img3.jpg"
  ],
  "deliver_method": 0,
  "cats": [
    {"cat_id": "381003"},
    {"cat_id": "380003"},
    {"cat_id": "517050"}
  ],
  "cats_v2": [
    {"cat_id": "381003"},
    {"cat_id": "380003"},
    {"cat_id": "517050"}
  ],
  "extra_service": {
    "service_tags": []
  },
  "skus": [
    {
      "price": 800,
      "stock_num": 100,
      "out_sku_id": "SKU001"
    }
  ],
  "listing": 0
}
```

## 5. 注意事项

1. **图片要求**：
   - 主图最少3张，最多9张，不可重复
   - 详情图最少1张，最多20张，不可重复
   - 图片必须是公开可访问的URL

2. **标题要求**：
   - 至少5个有效字符
   - 不能仅为数字或英文
   - 包含非法字符检查

3. **类目要求**：
   - 必须使用通过类目接口获取的有效cat_id
   - 类目数组顺序必须严格按照一二三级排列

4. **价格和库存**：
   - 价格单位为分，必须为整数
   - 库存必须为非负整数

5. **编码规范**：
   - CSV文件必须使用UTF-8编码
   - 包含中文的CSV应使用BOM标记

## 6. 完整CSV模板文件

```csv
商品标题,副标题,短标题,商品描述,发货方式,一级类目ID,二级类目ID,三级类目ID,主图1,主图2,主图3,主图4,主图5,主图6,主图7,主图8,主图9,详情图1,详情图2,详情图3,SKU价格(分),SKU库存,SKU编码,上架状态
商业模式重构：线上生意破局,线上营销领域实战指南,商业模式重构,本课程将帮助您重构商业模式，掌握线上营销技巧,0,381003,380003,517050,https://example.com/img1.jpg,https://example.com/img2.jpg,https://example.com/img3.jpg,,,,,,,,https://example.com/desc1.jpg,,,800,100,SKU001,0
```
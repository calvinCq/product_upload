#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信视频号小店商品上传测试脚本（从CSV读取数据）
"""

import os
import json
import csv
import requests
import logging
from datetime import datetime

# 配置日志
LOG_FILE = "wechat_api_operation.log"

def setup_logger():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

def log_message(message):
    """记录日志消息"""
    logger = setup_logger()
    logger.info(message)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def load_config():
    """加载配置文件"""
    try:
        with open('wechat_api_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        error_msg = "配置文件 wechat_api_config.json 不存在"
        log_message(error_msg)
        raise FileNotFoundError(error_msg)
    except json.JSONDecodeError:
        error_msg = "配置文件格式错误，请检查JSON格式"
        log_message(error_msg)
        raise json.JSONDecodeError(error_msg, '', 0)

def get_access_token(config):
    """获取access_token"""
    try:
        app_id = config.get('appid')
        app_secret = config.get('appsecret')
        
        if not app_id or not app_secret:
            raise ValueError("配置文件中缺少appid或appsecret")
        
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
        log_message(f"开始获取access_token: {url}")
        
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if 'access_token' in result:
            access_token = result['access_token']
            log_message(f"成功获取access_token，有效期: {result.get('expires_in', '未知')}秒")
            return access_token
        else:
            error_msg = f"获取access_token失败: {result}"
            log_message(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        log_message(f"获取access_token时发生异常: {str(e)}")
        raise

def read_csv_template(csv_file):
    """读取CSV模板文件"""
    products = []
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:  # 使用utf-8-sig处理BOM
            reader = csv.DictReader(f)
            for row in reader:
                products.append(row)
        log_message(f"成功读取CSV文件，共 {len(products)} 条商品数据")
        return products
    except FileNotFoundError:
        error_msg = f"CSV文件 {csv_file} 不存在"
        log_message(error_msg)
        raise FileNotFoundError(error_msg)
    except Exception as e:
        log_message(f"读取CSV文件时发生异常: {str(e)}")
        raise

def validate_product_data(product):
    """验证商品数据"""
    # 检查必填字段
    required_fields = ['商品标题', '发货方式', '一级类目ID', '二级类目ID', '三级类目ID', 
                      '主图1', '主图2', '主图3', '详情图1', 'SKU价格(分)', 'SKU库存']
    
    for field in required_fields:
        if not product.get(field) or product.get(field).strip() == '':
            raise ValueError(f"商品数据缺少必填字段: {field}")
    
    # 验证标题长度
    title = product.get('商品标题')
    if len(title) < 5 or len(title) > 60:
        raise ValueError(f"商品标题长度必须在5-60个字符之间，当前长度: {len(title)}")
    
    # 验证发货方式
    try:
        deliver_method = int(product.get('发货方式'))
        if deliver_method not in [0, 1, 3]:
            raise ValueError(f"发货方式必须是0、1或3，当前值: {deliver_method}")
    except ValueError:
        raise ValueError(f"发货方式必须是数字，当前值: {product.get('发货方式')}")
    
    # 验证价格和库存
    try:
        price = int(product.get('SKU价格(分)'))
        if price <= 0:
            raise ValueError(f"商品价格必须大于0，当前值: {price}")
    except ValueError:
        raise ValueError(f"商品价格必须是整数，当前值: {product.get('SKU价格(分)')}")
    
    try:
        stock = int(product.get('SKU库存'))
        if stock < 0:
            raise ValueError(f"商品库存不能为负数，当前值: {stock}")
    except ValueError:
        raise ValueError(f"商品库存必须是整数，当前值: {product.get('SKU库存')}")
    
    log_message(f"商品数据验证通过: {title}")
    return True

def convert_csv_to_api_params(product):
    """将CSV数据转换为API请求参数"""
    # 收集主图（过滤空值）
    head_imgs = []
    for i in range(1, 10):
        img_key = f"主图{i}"
        if product.get(img_key) and product.get(img_key).strip():
            head_imgs.append(product.get(img_key).strip())
    
    # 收集详情图（过滤空值）
    desc_imgs = []
    for i in range(1, 4):
        img_key = f"详情图{i}"
        if product.get(img_key) and product.get(img_key).strip():
            desc_imgs.append(product.get(img_key).strip())
    
    # 构建API参数
    params = {
        "title": product.get('商品标题').strip(),
        "head_imgs": head_imgs,
        "deliver_method": int(product.get('发货方式')),
        "cats": [
            {"cat_id": product.get('一级类目ID').strip()},
            {"cat_id": product.get('二级类目ID').strip()},
            {"cat_id": product.get('三级类目ID').strip()}
        ],
        "cats_v2": [
            {"cat_id": product.get('一级类目ID').strip()},
            {"cat_id": product.get('二级类目ID').strip()},
            {"cat_id": product.get('三级类目ID').strip()}
        ],
        "extra_service": {
            "service_tags": []  # 默认空服务标签
        },
        "skus": [
            {
                "price": int(product.get('SKU价格(分)')),
                "stock_num": int(product.get('SKU库存')),
            }
        ],
        "desc_info": {
            "imgs": desc_imgs
        }
    }
    
    # 添加可选字段
    if product.get('副标题') and product.get('副标题').strip():
        params['sub_title'] = product.get('副标题').strip()
    
    if product.get('短标题') and product.get('短标题').strip():
        params['short_title'] = product.get('短标题').strip()
    
    if product.get('商品描述') and product.get('商品描述').strip():
        params['desc_info']['desc'] = product.get('商品描述').strip()
    
    if product.get('SKU编码') and product.get('SKU编码').strip():
        params['skus'][0]['out_sku_id'] = product.get('SKU编码').strip()
    
    if product.get('上架状态'):
        try:
            params['listing'] = int(product.get('上架状态'))
        except ValueError:
            log_message("上架状态解析失败，使用默认值0")
    
    # 对于快递发货方式，添加基础的运费信息（实际使用时需要替换为有效的模板ID）
    if int(product.get('发货方式')) == 0:
        params['express_info'] = {
            "express_type": 0,  # 0: 使用模板
            "template_id": "default_template"  # 这里需要替换为实际的运费模板ID
        }
    
    return params

def upload_product(config, access_token, product_params):
    """上传商品到微信小店"""
    try:
        # API路径根据文档: /channels/ec/product/add
        api_url = f"https://api.weixin.qq.com/channels/ec/product/add?access_token={access_token}"
        
        log_message(f"开始调用添加商品API: {api_url}")
        log_message(f"商品标题: {product_params.get('title')}")
        
        # 发送POST请求
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, json=product_params, headers=headers, timeout=60)
        result = response.json()
        
        log_message(f"API响应状态码: {response.status_code}")
        log_message(f"API响应内容: {json.dumps(result, ensure_ascii=False)}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"请求异常: {str(e)}"
        log_message(error_msg)
        raise
    except Exception as e:
        error_msg = f"调用API时发生异常: {str(e)}"
        log_message(error_msg)
        raise

def save_upload_results(results, filename="upload_results.json"):
    """保存上传结果到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        log_message(f"上传结果已保存到文件: {filename}")
    except Exception as e:
        log_message(f"保存结果到文件时发生异常: {str(e)}")

def main():
    """主函数"""
    results = []
    
    try:
        # 加载配置
        config = load_config()
        log_message("配置加载成功")
        
        # 获取access_token
        access_token = get_access_token(config)
        
        # 读取CSV文件
        csv_file = "商品上传模板.csv"
        products = read_csv_template(csv_file)
        
        # 逐条处理商品
        for idx, product in enumerate(products, 1):
            log_message(f"\n===== 处理商品 {idx}/{len(products)} =====")
            
            try:
                # 验证商品数据
                validate_product_data(product)
                
                # 转换为API参数格式
                api_params = convert_csv_to_api_params(product)
                log_message("商品数据转换完成")
                
                # 保存转换后的API参数到临时文件，便于查看和调试
                with open(f"temp_product_{idx}_params.json", 'w', encoding='utf-8') as f:
                    json.dump(api_params, f, ensure_ascii=False, indent=2)
                log_message(f"API参数已保存到 temp_product_{idx}_params.json")
                
                # 调用API上传商品
                log_message("\n调用API上传商品...")
                result = upload_product(config, access_token, api_params)
                
                # 记录结果
                results.append({
                    "商品标题": product.get('商品标题'),
                    "上传结果": "成功" if result.get('errcode') == 0 else "失败",
                    "错误信息": result.get('errmsg') if result.get('errcode') != 0 else None,
                    "商品ID": result.get('product_id') if result.get('errcode') == 0 else None,
                    "响应详情": result
                })
                
            except Exception as e:
                log_message(f"处理商品时发生错误: {str(e)}")
                results.append({
                    "商品标题": product.get('商品标题', '未知'),
                    "上传结果": "失败",
                    "错误信息": str(e)
                })
        
        # 保存所有结果
        if results:
            save_upload_results(results)
        
        log_message("\n✅ 所有商品处理完毕！")
        
    except Exception as e:
        log_message(f"\n❌ 程序执行失败: {str(e)}")
    finally:
        log_message("\n✅ 程序执行完毕")

if __name__ == "__main__":
    main()
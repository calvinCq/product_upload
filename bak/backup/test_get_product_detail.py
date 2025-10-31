#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信视频号小店商品详情API测试脚本
"""

import os
import json
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

def test_get_product_detail(config, access_token, product_id):
    """测试获取商品详情API"""
    try:
        # API路径根据文档: /channels/ec/product/get
        api_url = f"https://api.weixin.qq.com/channels/ec/product/get?access_token={access_token}"
        
        # 请求参数
        payload = {
            "product_id": product_id,
            "data_type": 1  # 1:获取线上数据
        }
        
        log_message(f"开始调用获取商品详情API: {api_url}")
        log_message(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
        
        # 发送POST请求
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        result = response.json()
        
        log_message(f"API响应状态码: {response.status_code}")
        log_message(f"API响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"请求异常: {str(e)}"
        log_message(error_msg)
        raise
    except Exception as e:
        error_msg = f"调用API时发生异常: {str(e)}"
        log_message(error_msg)
        raise

def save_result_to_json(result, filename="product_detail_result.json"):
    """保存结果到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log_message(f"结果已保存到文件: {filename}")
    except Exception as e:
        log_message(f"保存结果到文件时发生异常: {str(e)}")

def main():
    """主函数"""
    try:
        # 加载配置
        config = load_config()
        log_message("配置加载成功")
        
        # 获取access_token
        access_token = get_access_token(config)
        
        # 测试商品详情API
        product_id = "10000316699884"  # 指定的商品ID
        log_message(f"开始获取商品ID: {product_id} 的详情")
        
        # 调用商品详情API
        result = test_get_product_detail(config, access_token, product_id)
        
        # 保存结果
        save_result_to_json(result)
        
        # 显示关键信息
        if result.get('errcode') == 0:
            log_message("\n🎉 商品详情获取成功!")
            # 显示一些关键商品信息
            product = result.get('product', {})
            if product:
                log_message(f"商品ID: {product.get('product_id')}")
                log_message(f"商品标题: {product.get('title', '无标题')}")
                log_message(f"商品状态: {product.get('status', '未知')}")
                log_message(f"最低价格: {product.get('min_price', '未知')}分")
            else:
                log_message("未返回商品数据，可能商品不存在或无权限访问")
        else:
            log_message(f"\n❌ 商品详情获取失败")
            log_message(f"错误码: {result.get('errcode')}")
            log_message(f"错误信息: {result.get('errmsg')}")
            
            # 提供可能的解决方法
            log_message("\n可能的原因:")
            log_message("1. 公众号未开通视频号小店功能")
            log_message("2. 当前账号类型不支持此API")
            log_message("3. 商品ID不存在或无权限访问该商品")
            log_message("4. 需要申请特定权限才能访问商品详情")
            log_message("5. 微信开放平台接口发生变更")
            
    except Exception as e:
        log_message(f"\n❌ 程序执行失败: {str(e)}")
    finally:
        log_message("\n✅ 程序执行完毕")

if __name__ == "__main__":
    main()
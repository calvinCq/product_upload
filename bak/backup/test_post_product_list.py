#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专门测试视频号小店商品列表API的POST请求
基于官方文档: https://developers.weixin.qq.com/doc/store/shop/API/channels-shop-product/shop/api_getproductlist.html
使用POST https://api.weixin.qq.com/channels/ec/product/list/get?access_token=ACCESS_TOKEN
"""

import os
import json
import sys
import time
import requests

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入日志函数，如果不存在则创建简单版本
try:
    from wechat_shop_api import log_message
except ImportError:
    def log_message(message, level="INFO"):
        """简单的日志函数"""
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        print(f"{timestamp} [{level}] {message}")

# 配置文件路径
CONFIG_FILE = "wechat_api_config.json"

def load_config(config_file):
    """
    加载配置文件
    :param config_file: 配置文件路径
    :return: 配置字典
    """
    try:
        if not os.path.exists(config_file):
            log_message(f"配置文件不存在: {config_file}", "ERROR")
            return None
            
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        # 验证必要配置项
        required_fields = ["appid", "appsecret"]
        for field in required_fields:
            if field not in config or not config[field]:
                log_message(f"配置文件缺少有效的{field}配置", "ERROR")
                return None
                
        return config
        
    except Exception as e:
        log_message(f"加载配置文件异常: {str(e)}", "ERROR")
        return None

def get_access_token(config):
    """
    获取微信API的access_token
    :param config: 配置字典
    :return: access_token或None
    """
    log_message("\n===== 获取Access Token =====")
    
    try:
        # 构造获取access_token的URL
        base_url = "https://api.weixin.qq.com"
        url = f"{base_url}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": config["appid"],
            "secret": config["appsecret"]
        }
        
        log_message(f"请求URL: {url}")
        log_message(f"请求参数: grant_type=client_credential, appid=***, secret=***")
        
        # 发送请求
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        
        log_message(f"响应状态码: {response.status_code}")
        log_message(f"响应内容: {json.dumps(result, ensure_ascii=False)}")
        
        # 检查响应
        if "access_token" in result:
            log_message(f"成功获取access_token: {result['access_token'][:10]}...")
            log_message(f"有效期: {result.get('expires_in', 0)}秒")
            return result["access_token"]
        else:
            error_code = result.get("errcode", "未知")
            error_msg = result.get("errmsg", "未知错误")
            log_message(f"获取access_token失败: 错误码 {error_code}, 错误信息: {error_msg}", "ERROR")
            return None
            
    except Exception as e:
        log_message(f"获取access_token异常: {str(e)}", "ERROR")
        return None

def test_post_product_list_api(access_token):
    """
    测试视频号小店商品列表API的POST请求
    使用官方文档指定的路径: /channels/ec/product/list/get
    
    :param access_token: 有效的access_token
    :return: API响应结果
    """
    log_message("\n===== 测试POST请求调用商品列表API =====")
    
    try:
        base_url = "https://api.weixin.qq.com"
        api_path = "/channels/ec/product/list/get"
        url = f"{base_url}{api_path}"
        
        # 构建查询参数 - access_token作为查询参数
        params = {
            "access_token": access_token
        }
        
        # 构建请求体 - 根据官方文档要求
        request_body = {
            "page_size": 10,  # 每页数量，必填
            # 可选参数
            # "status": 5,  # 商品状态，5表示上架
            # "next_key": ""  # 翻页上下文
        }
        
        log_message(f"请求URL: {url}")
        log_message(f"查询参数: access_token={access_token[:10]}...")
        log_message(f"请求体: {json.dumps(request_body, ensure_ascii=False)}")
        
        # 发送POST请求
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, params=params, json=request_body, headers=headers, timeout=15)
        
        log_message(f"响应状态码: {response.status_code}")
        
        # 解析响应
        try:
            result = response.json()
            log_message(f"响应内容: {json.dumps(result, ensure_ascii=False)}")
            return result
        except json.JSONDecodeError as e:
            log_message(f"解析JSON响应失败: {str(e)}", "ERROR")
            log_message(f"原始响应内容: {response.text}")
            return {"errcode": -1, "errmsg": "JSON解析失败"}
            
    except requests.RequestException as e:
        log_message(f"HTTP请求异常: {str(e)}", "ERROR")
        return {"errcode": -1, "errmsg": f"请求异常: {str(e)}"}
    except Exception as e:
        log_message(f"未知异常: {str(e)}", "ERROR")
        return {"errcode": -1, "errmsg": f"未知异常: {str(e)}"}

def display_api_result(result):
    """
    显示API调用结果
    :param result: API响应结果
    """
    log_message("\n===== API调用结果分析 =====")
    
    if not isinstance(result, dict):
        log_message("无效的API响应格式", "ERROR")
        return
    
    errcode = result.get("errcode", -1)
    errmsg = result.get("errmsg", "未知错误")
    
    if errcode == 0:
        log_message("✓ API调用成功！")
        
        # 显示商品信息
        total_num = result.get("total_numnumber", 0)  # 根据文档，应该是total_num
        product_ids = result.get("product_ids", [])
        next_key = result.get("next_key", "")
        
        log_message(f"总商品数: {total_num}")
        log_message(f"商品ID列表: {json.dumps(product_ids, ensure_ascii=False)}")
        log_message(f"下一页上下文: {next_key}")
        
        # 保存结果
        with open("post_product_list_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log_message("结果已保存到 post_product_list_result.json")
        
    else:
        log_message(f"✗ API调用失败: 错误码 {errcode}, 错误信息: {errmsg}", "ERROR")
        
        # 常见错误说明
        error_explanations = {
            40066: "无效的URL路径，可能是接口路径有误或当前账号类型不支持",
            40001: "无效的access_token，可能已过期或无效",
            48001: "无权限调用此API，需要相应权限",
            10020050: "无权限调用该api，请开发者获取权限后再试",
            10020051: "参数有误，请按照文档传参"
        }
        
        if errcode in error_explanations:
            log_message(f"错误说明: {error_explanations[errcode]}", "ERROR")
        
        log_message("\n可能的解决方案:")
        log_message("1. 确认公众号已开通视频号小店功能")
        log_message("2. 验证access_token是否有效")
        log_message("3. 确认当前账号类型支持此API")
        log_message("4. 检查是否已获得相应的接口权限")
        log_message("5. 确保请求参数符合文档要求")

def main():
    """
    主函数
    """
    log_message("=========================================")
    log_message("开始测试微信视频号小店商品列表API POST请求")
    log_message("基于官方文档: https://developers.weixin.qq.com/doc/store/shop/API/channels-shop-product/shop/api_getproductlist.html")
    log_message("=========================================")
    
    # 加载配置
    config = load_config(CONFIG_FILE)
    if not config:
        log_message("配置加载失败，程序终止", "ERROR")
        return
    
    # 获取access_token
    access_token = get_access_token(config)
    if not access_token:
        log_message("获取access_token失败，无法继续", "ERROR")
        return
    
    # 短暂延迟
    log_message("\n准备发送POST请求...")
    time.sleep(1)
    
    # 测试POST请求
    result = test_post_product_list_api(access_token)
    
    # 显示结果分析
    display_api_result(result)
    
    log_message("\n=========================================")
    log_message("POST请求测试完成")
    log_message("=========================================")

if __name__ == "__main__":
    main()
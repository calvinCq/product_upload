#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
真实测试视频号小店API连通性和商品列表获取功能
基于微信视频号小店API: https://developers.weixin.qq.com/doc/store/shop/API/channels-shop-product/shop/api_getproductlist.html
"""

import os
import json
import sys
import time
import requests

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wechat_shop_api import WeChatShopAPIClient, log_message

# 配置文件路径
CONFIG_FILE = "wechat_api_config.json"

# 微信视频号小店API文档: https://developers.weixin.qq.com/doc/store/shop/API/channels-shop-product/shop/api_getproductlist.html

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

def test_api_connectivity(config):
    """
    第一步：测试微信API连通性
    :param config: 配置字典
    :return: (是否连通, access_token或None)
    """
    log_message("\n========== 第一步：测试微信API连通性 ==========")
    log_message(f"使用AppID: {config['appid'][:6]}...{config['appid'][-4:]}")
    
    try:
        # 构造获取access_token的URL
        base_url = config.get("api_base_url", "https://api.weixin.qq.com")
        url = f"{base_url}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": config["appid"],
            "secret": config["appsecret"]
        }
        
        log_message(f"正在请求微信API: {url}")
        log_message(f"请求参数: grant_type=client_credential, appid=***, secret=***")
        
        # 发送请求
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        
        log_message(f"API响应状态码: {response.status_code}")
        log_message(f"API响应内容: {json.dumps(result, ensure_ascii=False)}")
        
        # 检查响应
        if "access_token" in result:
            log_message("✓ API连通性测试成功！成功获取access_token")
            log_message(f"access_token有效期: {result.get('expires_in', 0)}秒")
            return True, result["access_token"]
        else:
            error_code = result.get("errcode", "未知")
            error_msg = result.get("errmsg", "未知错误")
            log_message(f"✗ API连通性测试失败: 错误码 {error_code}, 错误信息: {error_msg}", "ERROR")
            
            # 常见错误说明
            common_errors = {
                40001: "AppSecret错误或AppSecret不属于该AppID",
                40002: "请确保grant_type字段值为client_credential",
                40164: "调用接口的IP地址不在白名单中",
                45009: "API调用太频繁，请稍后再试",
                48001: "该AppID未授权使用此API"
            }
            if error_code in common_errors:
                log_message(f"错误说明: {common_errors[error_code]}", "ERROR")
            
            return False, None
            
    except Exception as e:
        log_message(f"✗ API连通性测试异常: {str(e)}", "ERROR")
        log_message("请检查网络连接、防火墙设置或代理配置", "ERROR")
        return False, None

def display_product_list(result):
    """
    显示商品列表
    :param result: API返回结果
    """
    if not result or "errcode" not in result or result["errcode"] != 0:
        error_code = result.get("errcode", "未知")
        error_msg = result.get("errmsg", "未知错误")
        log_message(f"获取商品列表失败: 错误码 {error_code}, 错误信息: {error_msg}", "ERROR")
        return
    
    total_count = result.get("total_count", 0)
    product_list = result.get("product_list", [])
    
    log_message(f"\n=== 视频号小店商品列表 ===")
    log_message(f"总商品数: {total_count}")
    log_message(f"当前页商品数: {len(product_list)}")
    log_message("====================\n")
    
    if not product_list:
        log_message("当前页无商品数据")
        return
    
    for i, product in enumerate(product_list, 1):
        log_message(f"商品 {i}:")
        log_message(f"  商品ID: {product.get('product_id', 'N/A')}")
        log_message(f"  商品标题: {product.get('title', 'N/A')}")
        log_message(f"  商品状态: {product.get('product_status', 'N/A')}")
        log_message(f"  商品价格: {product.get('price', 'N/A')}")
        log_message(f"  商品描述: {product.get('desc', 'N/A')[:50]}...")
        log_message("-------------------")

def test_channels_product_api(config, access_token):
    """
    第二步：测试视频号小店商品列表API
    根据官方文档: https://developers.weixin.qq.com/doc/store/shop/API/channels-shop-product/shop/api_getproductlist.html
    
    :param config: 配置字典
    :param access_token: 有效的access_token
    :return: (result, error) 格式的元组
    """
    log_message("\n========== 第二步：测试视频号小店商品列表API ==========")
    log_message("开始尝试调用视频号小店商品列表API")
    
    try:
        # 确保配置是字典类型
        if not isinstance(config, dict):
            error_msg = "配置参数必须是字典类型"
            log_message(error_msg, "ERROR")
            return None, error_msg
        
        base_url = config.get("api_base_url", "https://api.weixin.qq.com")
        
        # 尝试不同的可能路径，包括官方文档指定的路径
        api_paths = [
            "/channels/ec/product/list.get",  # 官方文档路径
            "/channels/ec/product/list",      # 替代路径1
            "/channels/ec/product/batchget"   # 替代路径2
        ]
        
        for path in api_paths:
            url = f"{base_url}{path}"
            log_message(f"尝试API路径: {path}")
            
            try:
                # 构建请求参数 - access_token作为查询参数
                params = {
                    "access_token": access_token
                }
                
                # 请求体参数 - 根据官方文档要求的格式
                request_data = {
                    "page_size": 10  # 每页数量
                }
                
                log_message(f"查询参数: access_token={access_token[:10]}...")
                
                # 发送POST请求
                response = requests.post(url, params=params, json=request_data, timeout=15)
                
                # 确保响应是有效的JSON
                try:
                    result = response.json()
                    log_message(f"API响应状态码: {response.status_code}")
                    log_message(f"API响应内容: {json.dumps(result, ensure_ascii=False)}")
                except json.JSONDecodeError as e:
                    log_message(f"解析API响应失败: {str(e)}", "ERROR")
                    continue
                
                # 检查响应
                if isinstance(result, dict) and result.get("errcode") == 0:
                    log_message("成功获取商品列表数据！")
                    product_list = result.get('product_list', [])
                    log_message(f"商品数量: {len(product_list)}")
                    
                    # 如果有商品，输出部分商品信息
                    if product_list:
                        log_message("商品详情示例:")
                        for i, product in enumerate(product_list[:3]):  # 只显示前3个商品
                            log_message(f"商品{i+1}: 商品ID={product.get('product_id')}, 名称={product.get('title')}")
                    
                    return result, None
                elif isinstance(result, dict):
                    errcode = result.get("errcode")
                    errmsg = result.get("errmsg", "未知错误")
                    log_message(f"API调用失败: errcode={errcode}, errmsg={errmsg}")
                    
                    # 对于48001和40001错误，不再尝试其他路径
                    if errcode in [48001, 40001]:
                        return None, f"API调用失败: errcode={errcode}, errmsg={errmsg}"
                    # 继续尝试下一个路径
                
            except requests.RequestException as e:
                log_message(f"网络请求异常: {str(e)}")
                continue
        
        # 如果所有路径都失败
        return None, "所有尝试的API路径都返回错误，请确认公众号是否开通视频号小店功能"
                
    except Exception as e:
        error_msg = f"发生未知异常: {str(e)}"
        log_message(error_msg, "ERROR")
        return None, error_msg

def test_get_channels_product_list():
    """
    真实测试视频号小店API流程
    1. 首先测试API连通性（获取access_token）
    2. 然后测试商品列表API调用
    """
    log_message("=========================================")
    log_message("开始真实测试微信视频号小店API功能")
    log_message("=========================================")
    
    # 加载配置
    log_message(f"正在加载配置文件: {CONFIG_FILE}")
    config = load_config(CONFIG_FILE)
    if not config:
        log_message("配置加载失败，程序终止", "ERROR")
        return
    
    log_message("配置加载成功，开始API测试流程...")
    
    # 第一步：测试API连通性
    connected, access_token = test_api_connectivity(config)
    if not connected or not access_token:
        log_message("\nAPI连通性测试失败，无法继续进行商品列表测试", "ERROR")
        log_message("请解决以下问题后重试:")
        log_message("1. 确认AppID和AppSecret是否正确")
        log_message("2. 检查网络连接是否正常")
        log_message("3. 确认公众号权限是否完整")
        return
    
    # 短暂延迟
    log_message("\nAPI连通性测试通过，准备进行商品列表API测试...")
    time.sleep(1)
    
    # 第二步：测试商品列表API
    result, error = test_channels_product_api(config, access_token)
    
    # 显示结果
    if result is not None:
        display_product_list(result)
        
        # 保存结果到文件
        try:
            with open("channels_product_list_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            log_message("商品列表结果已保存到 channels_product_list_result.json")
        except Exception as e:
            log_message(f"保存结果失败: {str(e)}", "ERROR")
    else:
        log_message("\n商品列表API测试未成功获取数据", "WARNING")
        log_message(f"错误信息: {error}")
        log_message("可能的原因:")
        log_message("1. 公众号未开通视频号小店功能")
        log_message("2. 当前账号类型不支持此API")
        log_message("3. 微信开放平台接口发生变更")
        log_message("4. 需要申请特定权限才能访问商品列表")
    
    log_message("\n=========================================")
    log_message("微信视频号小店API测试流程完成")
    log_message("=========================================")

if __name__ == "__main__":
    test_get_channels_product_list()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取并打印微信API的access_token，以及使用它进行API请求
"""

import json
import requests
from wechat_shop_api import WeChatShopAPIClient, log_message

# 配置信息 - 需要替换为真实的appid和appsecret
CONFIG = {
    "appid": "your_appid_here",  # 替换为实际的AppID
    "appsecret": "your_appsecret_here"  # 替换为实际的AppSecret
}

def get_and_print_token():
    """
    获取并打印access_token
    """
    print("=============================================")
    print("      获取微信API access_token")
    print("=============================================")
    
    try:
        # 方法1：使用WeChatShopAPIClient内部方法获取
        client = WeChatShopAPIClient(
            appid=CONFIG["appid"], 
            appsecret=CONFIG["appsecret"]
        )
        
        # 直接调用_refresh_access_token方法获取token
        if client._refresh_access_token():
            print(f"\n✅ 使用WeChatShopAPIClient成功获取access_token:")
            print(f"  access_token: {client.access_token}")
            print(f"  过期时间: {client.access_token_expire_at}")
            
            # 保存token到文件
            token_info = {
                "access_token": client.access_token,
                "expire_at": client.access_token_expire_at,
                "appid": CONFIG["appid"]
            }
            with open("wechat_access_token.json", "w", encoding="utf-8") as f:
                json.dump(token_info, f, ensure_ascii=False, indent=2)
            print("\n✅ Token已保存到 wechat_access_token.json 文件")
            
            return client.access_token
        else:
            print("❌ 获取access_token失败")
            return None
            
    except Exception as e:
        print(f"❌ 获取token过程中发生错误: {str(e)}")
        return None

def use_token_for_request(token):
    """
    使用token进行API请求
    """
    if not token:
        print("❌ 没有有效的access_token，无法进行请求")
        return
    
    print("\n=============================================")
    print("        使用access_token进行API请求")
    print("=============================================")
    
    # 示例：获取微信服务器IP地址（这是一个简单的通用接口）
    api_url = f"https://api.weixin.qq.com/cgi-bin/getcallbackip?access_token={token}"
    
    try:
        print(f"\n正在调用API: {api_url}")
        
        response = requests.get(api_url, timeout=10)
        result = response.json()
        
        print(f"\n📊 API响应结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 检查是否成功
        if "errcode" in result and result["errcode"] != 0:
            print(f"\n❌ API调用失败: {result.get('errmsg', '未知错误')}")
        else:
            print("\n✅ API调用成功")
            
    except Exception as e:
        print(f"❌ API请求过程中发生错误: {str(e)}")

def test_category_api_with_token(token):
    """
    使用token测试类目API
    """
    if not token:
        return
    
    print("\n=============================================")
    print("        使用access_token测试类目API")
    print("=============================================")
    
    # 官方标准视频号小店类目API
    category_url = f"https://api.weixin.qq.com/channels/ec/category/all?access_token={token}"
    
    try:
        print(f"\n正在调用类目API: {category_url}")
        
        response = requests.get(category_url, timeout=30)
        result = response.json()
        
        print(f"\n📊 类目API响应结果:")
        # 只打印部分结果，避免输出过多
        print(f"  errcode: {result.get('errcode')}")
        print(f"  errmsg: {result.get('errmsg')}")
        if "cats" in result:
            print(f"  cats数组长度: {len(result['cats'])}")
        if "cats_v2" in result:
            print(f"  cats_v2数组长度: {len(result['cats_v2'])}")
        
        # 保存响应结果
        with open("category_api_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n✅ 类目API响应已保存到 category_api_result.json")
            
    except Exception as e:
        print(f"❌ 类目API请求过程中发生错误: {str(e)}")

if __name__ == "__main__":
    print("🔔 微信API Token获取与使用工具")
    print("🔔 请确保已在CONFIG中填写正确的appid和appsecret\n")
    
    # 1. 获取并打印access_token
    access_token = get_and_print_token()
    
    if access_token:
        # 2. 使用token进行通用API请求
        use_token_for_request(access_token)
        
        # 3. 使用token测试类目API
        test_category_api_with_token(access_token)
    
    print("\n=============================================")
    print("                 操作完成")
    print("=============================================")
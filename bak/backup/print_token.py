#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单脚本：获取并打印微信API的access_token
"""

import json
import time
import requests

# 配置信息 - 需要替换为真实的appid和appsecret
APPID = "your_appid_here"
APPSECRET = "your_appsecret_here"

def print_token():
    """
    获取并打印access_token
    """
    print("=============================================")
    print("          微信API Token打印工具")
    print("=============================================")
    
    if APPID == "your_appid_here" or APPSECRET == "your_appsecret_here":
        print("❌ 错误：请先在脚本中填写有效的appid和appsecret")
        return
    
    # 构建获取token的URL
    token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    
    try:
        print(f"\n正在请求token...")
        print(f"请求URL: {token_url}")
        
        # 发送请求
        response = requests.get(token_url, timeout=10)
        result = response.json()
        
        # 检查结果
        if "access_token" in result:
            token = result["access_token"]
            expires_in = result.get("expires_in", 7200)
            expire_time = int(time.time()) + expires_in
            
            print("\n✅ Token获取成功!")
            print(f"\n📋 Token信息:")
            print(f"┌───────────────────────────────────────────")
            print(f"│ Access Token: {token}")
            print(f"├───────────────────────────────────────────")
            print(f"│ 有效期: {expires_in} 秒")
            print(f"├───────────────────────────────────────────")
            print(f"│ 过期时间戳: {expire_time}")
            print(f"└───────────────────────────────────────────")
            
            # 格式化过期时间
            expire_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expire_time))
            print(f"\n🕒 过期时间: {expire_datetime}")
            
            # 保存到文件
            token_info = {
                "access_token": token,
                "expires_in": expires_in,
                "expire_at": expire_time,
                "appid": APPID,
                "timestamp": int(time.time())
            }
            with open("token_info.json", "w", encoding="utf-8") as f:
                json.dump(token_info, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Token已保存到 token_info.json")
            
            return token
            
        else:
            print(f"\n❌ Token获取失败: {result}")
            return None
            
    except Exception as e:
        print(f"\n❌ 请求过程中发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    print_token()
    print("\n=============================================")
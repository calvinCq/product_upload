#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用已有access_token进行微信API请求
"""

import json
import requests
import sys

def use_token(token):
    """
    使用提供的token进行API请求
    """
    if not token:
        print("❌ 请提供有效的access_token")
        return
    
    print("=============================================")
    print("       使用access_token进行API请求")
    print("=============================================")
    print(f"\n使用的access_token: {token}")
    
    # 选择要测试的API
    print("\n请选择要测试的API:")
    print("1. 获取微信服务器IP地址")
    print("2. 获取视频号小店类目信息")
    print("3. 退出")
    
    choice = input("\n请输入选择 (1-3): ")
    
    if choice == "1":
        # 获取微信服务器IP地址
        api_url = f"https://api.weixin.qq.com/cgi-bin/getcallbackip?access_token={token}"
        api_name = "获取微信服务器IP地址"
        
    elif choice == "2":
        # 获取视频号小店类目信息
        api_url = f"https://api.weixin.qq.com/channels/ec/category/all?access_token={token}"
        api_name = "获取视频号小店类目信息"
        
    elif choice == "3":
        print("\n已退出")
        return
        
    else:
        print("\n❌ 无效的选择")
        return
    
    try:
        print(f"\n正在调用 {api_name} API...")
        print(f"请求URL: {api_url}")
        
        # 发送请求
        response = requests.get(api_url, timeout=30)
        result = response.json()
        
        print(f"\n✅ API调用完成，响应结果:")
        
        # 如果是类目API，可能返回大量数据，只显示部分信息
        if choice == "2":
            print(f"  状态码: {response.status_code}")
            print(f"  errcode: {result.get('errcode')}")
            print(f"  errmsg: {result.get('errmsg')}")
            if "cats" in result:
                print(f"  cats数组长度: {len(result['cats'])}")
            if "cats_v2" in result:
                print(f"  cats_v2数组长度: {len(result['cats_v2'])}")
                
            # 保存完整结果到文件
            with open("use_token_category_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 完整响应已保存到 use_token_category_result.json")
            
        else:
            # 其他API显示完整结果
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
    except Exception as e:
        print(f"\n❌ API请求过程中发生错误: {str(e)}")

if __name__ == "__main__":
    # 从命令行参数获取token或手动输入
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = input("\n请输入access_token: ")
    
    use_token(token)
    print("\n=============================================")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：直接测试微信小店API获取类目信息的功能
"""

import os
import json
import logging
from src.api.wechat_shop_api import WeChatShopAPIClient

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config():
    """
    加载配置文件
    """
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print(f"配置文件 {config_path} 不存在，请先创建配置文件")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return None

def test_category_apis(api_client):
    """
    测试所有获取类目的API
    """
    print("\n=== 开始测试类目API ===\n")
    
    # 测试1: get_channels_category
    try:
        print("\n1. 测试 get_channels_category...")
        result = api_client.get_channels_category()
        print(f"返回结果类型: {type(result)}")
        print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result and result.get('success') and 'data' in result:
            data = result['data']
            print(f"数据类型: {type(data)}")
            if isinstance(data, list):
                print(f"类目数量: {len(data)}")
                if len(data) > 0:
                    print("前3个类目详情:")
                    for i, cat in enumerate(data[:3]):
                        print(f"  {i+1}. {json.dumps(cat, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"get_channels_category 调用失败: {str(e)}")
    
    # 测试2: get_all_category
    try:
        print("\n2. 测试 get_all_category...")
        result = api_client.get_all_category()
        print(f"返回结果类型: {type(result)}")
        print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result and result.get('success') and 'data' in result:
            data = result['data']
            print("数据结构分析:")
            if 'cats_v2' in data:
                print(f"cats_v2 存在，类型: {type(data['cats_v2'])}")
                if isinstance(data['cats_v2'], list):
                    print(f"cats_v2 数量: {len(data['cats_v2'])}")
                    if len(data['cats_v2']) > 0:
                        print("第一个 cats_v2 元素:")
                        print(json.dumps(data['cats_v2'][0], ensure_ascii=False, indent=2))
            
            if 'cats' in data:
                print(f"cats 存在，类型: {type(data['cats'])}")
                if isinstance(data['cats'], list):
                    print(f"cats 数量: {len(data['cats'])}")
                    if len(data['cats']) > 0:
                        print("第一个 cats 元素:")
                        print(json.dumps(data['cats'][0], ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"get_all_category 调用失败: {str(e)}")
    
    # 测试3: get_category
    try:
        print("\n3. 测试 get_category...")
        result = api_client.get_category()
        print(f"返回结果类型: {type(result)}")
        print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result and result.get('success') and 'data' in result:
            data = result['data']
            print(f"数据类型: {type(data)}")
            if isinstance(data, list):
                print(f"类目数量: {len(data)}")
                if len(data) > 0:
                    print("前3个类目详情:")
                    for i, cat in enumerate(data[:3]):
                        print(f"  {i+1}. {json.dumps(cat, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"get_category 调用失败: {str(e)}")
    
    print("\n=== 类目API测试完成 ===\n")

def main():
    """
    主函数
    """
    # 加载配置
    config = load_config()
    if not config:
        return
    
    # 初始化API客户端
    try:
        api_client = WeChatShopAPIClient(
            appid=config.get('appid'),
            appsecret=config.get('appsecret')
        )
        print("API客户端初始化成功")
        
        # 获取access_token
        access_token = api_client.get_access_token()
        if access_token:
            print(f"成功获取access_token: {access_token[:20]}...")
            
            # 测试类目API
            test_category_apis(api_client)
        else:
            print("获取access_token失败")
    
    except Exception as e:
        print(f"初始化API客户端失败: {str(e)}")

if __name__ == "__main__":
    main()
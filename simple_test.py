#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的测试脚本：直接测试微信小店API获取类目信息
"""

import os
import json
import sys
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.wechat_shop_api import WeChatShopAPIClient, load_api_paths

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    try:
        print("=== 开始简化测试 ===")
        
        # 加载API路径，检查是否包含所需的键
        print("1. 检查API路径配置...")
        api_paths = load_api_paths()
        print(f"API路径配置: {api_paths}")
        
        # 检查是否包含必要的API路径键
        required_keys = ['get_category', 'get_all_category', 'get_channels_category']
        for key in required_keys:
            if key not in api_paths:
                print(f"警告: API路径配置中缺少 {key}")
            else:
                print(f"✓ 找到 {key}: {api_paths[key]}")
        
        # 加载配置文件
        config_path = 'config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"\n2. 配置文件加载成功: {config_path}")
        else:
            print(f"\n2. 配置文件不存在: {config_path}")
            return
        
        # 初始化API客户端
        print("\n3. 初始化API客户端...")
        api_client = WeChatShopAPIClient(
            appid=config.get('appid'),
            appsecret=config.get('appsecret')
        )
        print("✓ API客户端初始化成功")
        
        # 显式检查api_client中的api_paths
        print(f"\n4. API客户端的API路径: {api_client.api_paths}")
        
        # 测试get_channels_category
        print("\n5. 测试 get_channels_category...")
        result = api_client.get_channels_category()
        print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
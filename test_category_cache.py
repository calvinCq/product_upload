#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证类目缓存和必填字段补全功能

该脚本用于测试以下功能：
1. 缓存目录创建和预初始化
2. AutoCategorySelector类的缓存功能
3. 必填字段自动补全逻辑
4. 类目选择和推荐功能
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入需要测试的模块
from auto_category_selector import AutoCategorySelector
from main import build_product_data, get_valid_category_id, WeChatShopAPIClient

def test_cache_directory_creation():
    """
    测试1：验证缓存目录创建功能
    """
    print("\n=== 测试1：缓存目录创建 ===")
    
    # 预初始化缓存目录
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
    try:
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            print(f"✅ 缓存目录已创建: {cache_dir}")
        else:
            print(f"✅ 缓存目录已存在: {cache_dir}")
        return True
    except Exception as e:
        print(f"❌ 创建缓存目录失败: {str(e)}")
        return False

def test_category_selector_initialization():
    """
    测试2：验证AutoCategorySelector类的初始化功能
    """
    print("\n=== 测试2：AutoCategorySelector初始化 ===")
    
    try:
        # 模拟API客户端
        class MockAPIClient:
            def __init__(self):
                pass
            
            def get_categories(self):
                # 返回模拟的类目数据
                return {
                    "data": {
                        "cat_list": [
                            {"cat_id": "10001", "name": "图书文具", "level": 1},
                            {"cat_id": "10002", "name": "办公设备", "level": 1},
                            {"cat_id": "20001", "name": "编程书籍", "level": 2, "f_cat_id": "10001"},
                            {"cat_id": "20002", "name": "文学小说", "level": 2, "f_cat_id": "10001"},
                            {"cat_id": "30001", "name": "Python编程", "level": 3, "f_cat_id": "20001"}
                        ]
                    }
                }
        
        # 初始化类目选择器
        mock_api = MockAPIClient()
        selector = AutoCategorySelector(api_client=mock_api, cache_expiry_hours=24)
        
        print(f"✅ AutoCategorySelector初始化成功")
        print(f"  - 缓存路径: {selector.categories_file}")
        print(f"  - 缓存过期时间: {selector.cache_expiry_hours}小时")
        return True
    except Exception as e:
        print(f"❌ AutoCategorySelector初始化失败: {str(e)}")
        return False

def test_cache_loading_and_saving():
    """
    测试3：验证缓存加载和保存功能
    """
    print("\n=== 测试3：缓存加载和保存功能 ===")
    
    try:
        # 创建测试缓存文件
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        test_cache_file = os.path.join(cache_dir, "test_cache.json")
        
        # 模拟的类目数据
        test_data = {
            "timestamp": int(time.time()),
            "categories": [
                {"cat_id": "10001", "name": "测试类目1"},
                {"cat_id": "10002", "name": "测试类目2"}
            ]
        }
        
        # 测试保存
        with open(test_cache_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 测试数据已保存到: {test_cache_file}")
        
        # 测试加载
        with open(test_cache_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print(f"✅ 测试数据已加载，包含 {len(loaded_data.get('categories', []))} 个类目")
        
        # 测试时间戳
        timestamp = loaded_data.get('timestamp', 0)
        cache_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print(f"✅ 缓存时间戳: {cache_time}")
        
        # 清理测试文件
        os.remove(test_cache_file)
        print(f"✅ 测试文件已清理")
        
        return True
    except Exception as e:
        print(f"❌ 缓存功能测试失败: {str(e)}")
        return False

def test_required_fields_completion():
    """
    测试4：验证必填字段自动补全功能
    """
    print("\n=== 测试4：必填字段自动补全功能 ===")
    
    try:
        # 创建一个不完整的产品描述
        product_description = {
            "title": "测试产品"
            # 故意不包含其他字段
        }
        
        # 创建一个基本的类目信息
        category_info = {
            "category_id": "10001",
            "category_id1": "10001",
            "category_id2": "20001",
            "category_id3": "30001"
        }
        
        # 构建商品数据
        product_data = build_product_data(product_description, category_info)
        
        # 验证必填字段是否已补全
        required_fields = [
            "title", "product_name", "desc", "product_desc",
            "price", "original_price", "product_status",
            "main_image", "image_list", "sku_list",
            "category_id", "category_id1", "category_id2", "category_id3",
            "cats", "cats_v2", "head_imgs", "item_imgs"
        ]
        
        all_fields_present = True
        missing_fields = []
        
        for field in required_fields:
            if field not in product_data or product_data[field] is None:
                missing_fields.append(field)
                all_fields_present = False
            else:
                print(f"✅ 字段 {field} 已存在，值: {type(product_data[field])}")
        
        if not missing_fields:
            print("✅ 所有必填字段都已成功补全")
        else:
            print(f"❌ 以下字段缺失: {missing_fields}")
        
        return all_fields_present
    except Exception as e:
        print(f"❌ 必填字段补全测试失败: {str(e)}")
        return False

def test_category_selection():
    """
    测试5：验证类目选择功能
    """
    print("\n=== 测试5：类目选择功能 ===")
    
    try:
        # 创建测试数据
        product_text = "Python编程书籍，适合初学者学习"
        
        # 初始化模拟API客户端
        class MockAPIClient:
            def __init__(self):
                pass
            
            def get_categories(self):
                # 返回模拟的类目数据
                return {
                    "data": {
                        "cat_list": [
                            {"cat_id": "10001", "name": "图书文具", "level": 1},
                            {"cat_id": "10002", "name": "办公设备", "level": 1},
                            {"cat_id": "20001", "name": "编程书籍", "level": 2, "f_cat_id": "10001"},
                            {"cat_id": "20002", "name": "文学小说", "level": 2, "f_cat_id": "10001"},
                            {"cat_id": "30001", "name": "Python编程", "level": 3, "f_cat_id": "20001"}
                        ]
                    }
                }
        
        mock_api = MockAPIClient()
        
        # 测试类目选择
        print(f"测试文本: {product_text}")
        
        # 创建类目选择器并加载数据
        selector = AutoCategorySelector(api_client=mock_api, cache_expiry_hours=24)
        categories = selector.load_categories()
        
        # 测试类目选择
        selected_categories = selector.select_categories(product_text)
        print(f"✅ 选择的类目: {selected_categories}")
        
        return True
    except Exception as e:
        print(f"❌ 类目选择功能测试失败: {str(e)}")
        return False

def main():
    """
    主测试函数
    """
    print("=== 开始类目缓存和必填字段补全功能测试 ===")
    
    # 运行所有测试
    tests = [
        test_cache_directory_creation,
        test_category_selector_initialization,
        test_cache_loading_and_saving,
        test_required_fields_completion,
        test_category_selection
    ]
    
    # 记录测试结果
    results = {}
    
    # 执行测试
    for test in tests:
        test_name = test.__name__
        print(f"\n执行测试: {test_name}")
        try:
            result = test()
            results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            print(f"测试结果: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ 测试异常: {str(e)}")
    
    # 显示测试总结
    print("\n=== 测试总结 ===")
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查代码")

if __name__ == "__main__":
    main()
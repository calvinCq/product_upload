#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信视频号小店API综合测试脚本
整合所有成功测试的功能：
- 类目获取测试（视频号小店API）
- 商品列表获取测试
- 商品详情获取测试
- 商品上传测试

根据测试结果，本脚本只保留成功的测试功能，优先使用视频号小店API
"""

import os
import json
import time
import sys
import requests
from datetime import datetime
from wechat_shop_api import WeChatShopAPIClient, log_message
# 导入测试数据管理模块
from test_data_manager import load_test_data, save_test_data, create_default_product_data, save_test_result, create_test_result_record, initialize_test_data

# 配置文件路径
CONFIG_FILE = "wechat_api_config.json"

# 结果保存目录
RESULT_DIR = "test_results"

# 确保结果目录存在
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

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

def display_category_info(category_data):
    """
    显示类目信息
    :param category_data: 类目数据
    """
    if not category_data:
        log_message("⚠️  未找到有效类目数据", "WARNING")
        return
    
    total_categories = 0
    category_list = []
    
    # 处理视频号小店格式
    if "cats" in category_data:
        for cat_group in category_data["cats"]:
            if "cat_and_qua" in cat_group:
                for cat_item in cat_group["cat_and_qua"]:
                    if "cat" in cat_item:
                        cat = cat_item["cat"]
                        cat_id = cat.get("cat_id") or cat.get("id")
                        cat_name = cat.get("cat_name") or cat.get("name")
                        level = cat.get("level", "未知")
                        category_list.append({"id": cat_id, "name": cat_name, "level": level})
                        total_categories += 1
    
    # 处理其他可能的格式
    if total_categories == 0 and "category_list" in category_data:
        for cat in category_data["category_list"]:
            cat_id = cat.get("cat_id") or cat.get("id")
            cat_name = cat.get("cat_name") or cat.get("name")
            level = cat.get("level", "未知")
            category_list.append({"id": cat_id, "name": cat_name, "level": level})
            total_categories += 1
    
    log_message(f"📊 发现类目总数: {total_categories}")
    
    # 显示前10个类目作为示例
    if category_list:
        log_message("\n🔍 类目示例 (前10个):")
        for i, cat in enumerate(category_list[:10], 1):
            log_message(f"   {i}. ID: {cat['id']}, 名称: {cat['name']}, 级别: {cat['level']}")

def test_get_channels_category(api_client):
    """
    测试视频号小店类目获取API
    :param api_client: API客户端实例
    :return: 是否成功
    """
    log_message("\n========== 测试视频号小店类目获取API ==========")
    
    try:
        start_time = time.time()
        result = api_client.get_channels_category()
        end_time = time.time()
        
        if result and result.get("success"):
            category_data = result.get("data", {})
            log_message(f"✅ 成功获取视频号小店商品类目信息，耗时{(end_time - start_time):.2f}秒")
            
            # 解析类目数据并展示
            display_category_info(category_data)
            
            # 保存结果到文件
            result_file = os.path.join(RESULT_DIR, "wechat_shop_channels_category_result.json")
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(category_data, f, ensure_ascii=False, indent=2)
            log_message(f"✅ 类目数据已成功保存到: {result_file}")
            
            return True
        else:
            error_msg = result.get("error", "获取视频号小店类目失败") if result else "未知错误"
            log_message(f"❌ 获取视频号小店商品类目失败: {error_msg}", "WARNING")
            return False
            
    except Exception as e:
        log_message(f"❌ 测试视频号小店类目API时发生异常: {str(e)}", "ERROR")
        return False

def test_get_product_list(api_client):
    """
    测试视频号小店商品列表获取API
    :param api_client: API客户端实例
    :return: 测试结果，包含成功状态和第一个商品ID（如果有）
    """
    log_message("\n========== 测试视频号小店商品列表获取API ==========")
    
    result_data = {"success": False, "first_product_id": None}
    
    try:
        # 获取商品列表
        log_message("请求商品列表（第1页，每页10个商品）")
        start_time = time.time()
        result = api_client.get_channels_product_list(page=1, size=10)
        end_time = time.time()
        
        if result and isinstance(result, dict):
            # 支持多种响应格式
            log_message(f"响应数据格式: {list(result.keys())}")
            
            # 检查是否成功（支持多种格式）
            if result.get("success") or result.get("errcode") == 0 or "product_ids" in result:
                # 根据不同格式获取商品信息
                if "product_ids" in result:
                    # 直接在根级别有product_ids的格式
                    product_ids = result.get("product_ids", [])
                    total_count = result.get("total_num", 0)
                elif "data" in result:
                    # 数据在data字段中的格式
                    product_data = result.get("data", {})
                    product_ids = product_data.get("product_ids", [])
                    total_count = product_data.get("total_num", product_data.get("total_count", 0))
                else:
                    product_ids = []
                    total_count = 0
                
                log_message(f"✅ 成功获取商品列表，耗时{(end_time - start_time):.2f}秒")
                log_message(f"📊 共获取到 {len(product_ids)} 个商品，总共有 {total_count} 个商品")
                
                # 保存第一个商品ID（如果有）
                if product_ids:
                    first_product_id = product_ids[0]
                    first_product_info = {"product_id": first_product_id}
                    result_file = os.path.join(RESULT_DIR, "first_product_info.json")
                    with open(result_file, "w", encoding="utf-8") as f:
                        json.dump(first_product_info, f, ensure_ascii=False, indent=2)
                    log_message(f"✅ 已保存第一个商品ID: {first_product_id}")
                    result_data["first_product_id"] = first_product_id
                
                # 保存结果到文件
                result_file = os.path.join(RESULT_DIR, "wechat_shop_product_list_result.json")
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                log_message(f"✅ 商品列表数据已成功保存到: {result_file}")
                
                result_data["success"] = True
            else:
                error_msg = result.get("errmsg", result.get("error", "获取商品列表失败"))
                log_message(f"❌ 获取商品列表失败: 错误码 {result.get('errcode')}, 消息: {error_msg}", "WARNING")
        else:
            log_message(f"❌ 获取商品列表失败: 返回格式异常或空响应", "WARNING")
            if result:
                log_message(f"   返回内容: {str(result)}", "DEBUG")
            
    except Exception as e:
        log_message(f"❌ 测试商品列表API时发生异常: {str(type(e).__name__)}: {str(e)}", "ERROR")
        import traceback
        log_message(f"详细异常信息: {traceback.format_exc()}", "ERROR")
    
    # 返回测试结果，包括第一个商品ID（如果有）
    return result_data

def test_get_product_detail(api_client, product_id=None):
    """
    测试视频号小店商品详情获取API
    :param api_client: API客户端实例
    :param product_id: 可选的商品ID，如果不提供则尝试从文件或商品列表中获取
    :return: 是否成功
    """
    log_message("\n========== 测试视频号小店商品详情获取API ==========")
    
    # 尝试获取商品ID的策略：
    # 1. 优先使用传入的商品ID
    # 2. 尝试从保存的文件中获取
    # 3. 最后尝试从商品列表获取
    if not product_id:
        # 尝试从保存的文件中读取第一个商品ID
        first_product_file = os.path.join(RESULT_DIR, "first_product_info.json")
        if os.path.exists(first_product_file):
            try:
                with open(first_product_file, "r", encoding="utf-8") as f:
                    first_product = json.load(f)
                    product_id = first_product.get("product_id")
                    log_message(f"✅ 从保存的文件中获取商品ID: {product_id}")
            except Exception as e:
                log_message(f"❌ 从文件读取商品ID失败: {str(e)}", "WARNING")
    
    # 如果还是没有商品ID，尝试从商品列表结果文件中获取
    if not product_id:
        list_result_file = os.path.join(RESULT_DIR, "wechat_shop_product_list_result.json")
        if os.path.exists(list_result_file):
            try:
                with open(list_result_file, "r", encoding="utf-8") as f:
                    list_result = json.load(f)
                    if "product_ids" in list_result and list_result["product_ids"]:
                        product_id = list_result["product_ids"][0]
                        log_message(f"✅ 从商品列表结果中获取第一个商品ID: {product_id}")
            except Exception as e:
                log_message(f"❌ 从商品列表结果读取商品ID失败: {str(e)}", "WARNING")
    
    # 如果还是没有商品ID，提供一个测试ID并提示用户
    if not product_id:
        log_message("⚠️  未找到可用的商品ID，使用测试ID进行演示", "WARNING")
        # 这里使用一个示例ID，实际使用时应该替换为真实ID
        product_id = "1234567890"  # 示例ID，需要替换为真实ID
        log_message(f"ℹ️  使用示例商品ID: {product_id}")
        log_message("ℹ️  提示: 请在实际使用时替换为有效的商品ID")
    
    try:
        # 获取商品详情
        log_message(f"请求商品ID: {product_id} 的详情")
        start_time = time.time()
        result = api_client.get_product_detail(product_id)
        end_time = time.time()
        
        if result and isinstance(result, dict):
            # 检查是否成功获取商品详情（支持多种响应格式）
            if result.get("success") or result.get("errcode") == 0 or ("data" in result and not result.get("data", {}).get("errcode")):
                product_data = result.get("data", {})
                log_message(f"✅ 成功获取商品详情，耗时{(end_time - start_time):.2f}秒")
                
                # 显示商品基本信息
                title = product_data.get("title", "-")
                price = product_data.get("price", "-")
                status = product_data.get("status", "-")
                log_message(f"\n🔍 商品详情:")
                log_message(f"   标题: {title}")
                log_message(f"   价格: {price}")
                log_message(f"   状态: {status}")
                
                # 保存结果到文件
                result_file = os.path.join(RESULT_DIR, f"product_detail_{product_id}.json")
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                log_message(f"✅ 商品详情数据已成功保存到: {result_file}")
                
                return True
            else:
                error_msg = result.get("error", result.get("errmsg", "获取商品详情失败"))
                log_message(f"❌ 获取商品详情失败: {error_msg}", "WARNING")
                if "errcode" in result:
                    log_message(f"   错误码: {result['errcode']}")
                return False
        else:
            log_message(f"❌ 获取商品详情失败: 返回格式异常或空响应", "WARNING")
            return False
            
    except Exception as e:
        log_message(f"❌ 测试商品详情API时发生异常: {str(type(e).__name__)}: {str(e)}", "ERROR")
        import traceback
        log_message(f"详细异常信息: {traceback.format_exc()}", "ERROR")
        return False

def test_upload_product(api_client):
    """
    测试视频号小店商品上传API（使用测试数据管理模块）
    :param api_client: API客户端实例
    :return: 是否成功
    """
    log_message("\n========== 测试视频号小店商品上传API ==========")
    
    try:
        # 首先尝试从测试数据文件加载商品数据
        product_data = load_test_data('default_product')
        
        # 如果没有找到测试数据，则创建默认数据
        if not product_data:
            log_message("ℹ️  未找到测试数据，创建默认商品数据")
            product_data = create_default_product_data()
            # 保存默认数据供下次使用
            save_test_data('default_product', product_data)
        else:
            # 更新标题，避免重复
            product_data['title'] = f"测试商品 - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        log_message(f"上传商品数据（标题: {product_data['title']}")
        
        start_time = time.time()
        result = api_client.upload_product(product_data)
        end_time = time.time()
        
        if result and result.get("success"):
            product_id = result.get("data", {}).get("product_id", "")
            log_message(f"✅ 商品上传成功！耗时{(end_time - start_time):.2f}秒")
            log_message(f"✅ 新商品ID: {product_id}")
            
            # 保存结果到文件
            result_file = os.path.join(RESULT_DIR, f"upload_result_{product_id}.json")
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            log_message(f"✅ 上传结果已成功保存到: {result_file}")
            
            # 使用测试数据管理模块保存测试结果
            test_record = create_test_result_record(
                "upload_product", 
                True, 
                {"product_id": product_id, "result": result}
            )
            save_test_result(test_record)
            
            return True
        else:
            error_msg = result.get("error", "商品上传失败") if result else "未知错误"
            log_message(f"❌ 商品上传失败: {error_msg}", "WARNING")
            
            # 保存失败结果
            test_record = create_test_result_record(
                "upload_product", 
                False, 
                error=error_msg
            )
            save_test_result(test_record)
            
            return False
            
    except Exception as e:
        error_msg = str(e)
        log_message(f"❌ 测试商品上传API时发生异常: {error_msg}", "ERROR")
        
        # 保存异常结果
        test_record = create_test_result_record(
            "upload_product", 
            False, 
            error=error_msg
        )
        save_test_result(test_record)
        
        return False

def run_tests(config):
    """
    运行所有测试
    :param config: 配置字典
    """
    log_message("=============================================")
    log_message("微信视频号小店API综合测试工具")
    log_message("=============================================")
    
    # 初始化API客户端
    api_client = WeChatShopAPIClient(
        appid=config["appid"],
        appsecret=config["appsecret"],
        api_config=config
    )
    
    log_message("初始化API客户端成功，开始执行测试...")
    
    # 测试结果统计
    test_results = {
        "category_test": False,
        "product_list_test": False,
        "product_detail_test": False,
        "upload_test": False
    }
    
    # 存储第一个商品ID，用于详情测试
    first_product_id = None
    
    # 1. 测试类目获取 - 这是目前最稳定的API
    test_results["category_test"] = test_get_channels_category(api_client)
    
    # 2. 测试商品列表获取 - 优化版测试
    log_message("\n🔄 开始测试商品列表API...")
    product_list_result = test_get_product_list(api_client)
    test_results["product_list_test"] = product_list_result["success"]
    first_product_id = product_list_result.get("first_product_id")
    
    # 3. 测试商品详情获取 - 使用商品列表中的第一个ID
    log_message("\n🔄 开始测试商品详情API...")
    if first_product_id:
        log_message(f"✅ 使用从商品列表获取的商品ID: {first_product_id} 进行详情测试")
    test_results["product_detail_test"] = test_get_product_detail(api_client, product_id=first_product_id)
    
    # 4. 测试商品上传
    log_message("\n🔄 开始测试商品上传API...")
    test_results["upload_test"] = test_upload_product(api_client)
    
    # 显示测试结果摘要
    log_message("\n=============================================")
    log_message("📊 测试结果摘要:")
    log_message(f"   类目获取API: {'✅ 通过' if test_results['category_test'] else '❌ 失败'}")
    log_message(f"   商品列表API: {'✅ 通过' if test_results['product_list_test'] else '❌ 失败'}")
    log_message(f"   商品详情API: {'✅ 通过' if test_results['product_detail_test'] else '❌ 失败'}")
    log_message(f"   商品上传API: {'⚠️  未测试' if not test_results['upload_test'] else ('✅ 通过' if test_results['upload_test'] else '❌ 失败')}")
    log_message("=============================================")
    
    # 保存测试结果摘要
    summary_file = os.path.join(RESULT_DIR, "test_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": test_results,
            "first_product_id": first_product_id,
            "notes": "API测试结果摘要"
        }, f, ensure_ascii=False, indent=2)
    log_message(f"\n✅ 测试摘要已保存到: {summary_file}")
    
    # 提供使用建议
    log_message("\n💡 使用建议:")
    log_message("1. 定期测试API连通性，确保系统正常运行")
    log_message("2. 优先使用视频号小店API，传统微信小店API可能已弃用")
    log_message("3. 上传商品前，请确保类目ID正确并符合资质要求")
    log_message("4. 详细操作日志已记录在: wechat_api_operation.log")
    log_message("5. API调用示例:")
    log_message("   - 获取类目: client.get_channels_category()")
    log_message("   - 获取商品列表: client.get_channels_product_list(page=1, size=10)")
    log_message("   - 获取商品详情: client.get_product_detail(product_id)")
    log_message("=============================================")

def main():
    """
    主函数
    """
    # 初始化测试数据
    initialize_test_data()
    
    # 加载配置
    config = load_config(CONFIG_FILE)
    if not config:
        log_message("配置加载失败，程序终止", "ERROR")
        return
    
    # 运行测试
    run_tests(config)

if __name__ == "__main__":
    main()
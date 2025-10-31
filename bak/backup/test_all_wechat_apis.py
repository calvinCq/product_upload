#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信小店API综合测试工具
测试所有可用的API接口，包括商品类目、商品列表、商品详情等
注意：此测试不会实际上架商品
"""

import os
import json
import time
from datetime import datetime
from wechat_shop_api import WeChatShopAPIClient, log_message, load_api_paths, load_wechat_api_config

# 测试结果目录
TEST_RESULTS_DIR = 'test_results'

# 确保测试结果目录存在
def ensure_test_results_dir():
    if not os.path.exists(TEST_RESULTS_DIR):
        os.makedirs(TEST_RESULTS_DIR)
        log_message(f"创建测试结果目录: {TEST_RESULTS_DIR}")

# 保存测试结果
def save_test_result(filename, data):
    ensure_test_results_dir()
    filepath = os.path.join(TEST_RESULTS_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log_message(f"测试结果已保存到: {filepath}")
        return True
    except Exception as e:
        log_message(f"保存测试结果失败: {str(e)}", "ERROR")
        return False

# 生成测试时间戳
def get_timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

class WeChatShopAPITester:
    """
    微信小店API测试类
    测试所有可用的API接口
    """
    
    def __init__(self):
        """
        初始化测试器
        """
        # 加载配置
        self.api_config = load_wechat_api_config()
        self.api_paths = load_api_paths()
        
        # 初始化API客户端
        self.client = WeChatShopAPIClient(
            appid=self.api_config.get("appid"),
            appsecret=self.api_config.get("appsecret"),
            api_config=self.api_config
        )
        
        # 测试结果汇总
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "appid": self.api_config.get("appid"),
            "api_base_url": self.api_config.get("api_base_url"),
            "results": {}
        }
    
    def test_access_token(self):
        """
        测试access_token获取功能
        """
        log_message("\n==================================")
        log_message("开始测试: access_token获取")
        log_message("==================================")
        
        try:
            # 调用refresh_access_token获取token
            access_token = self.client._refresh_access_token()
            
            result = {
                "success": access_token is not None,
                "access_token_exists": access_token is not None,
                "token_length": len(access_token) if access_token else 0,
                "error": None
            }
            
            if result["success"]:
                log_message("✅ access_token获取成功")
            else:
                log_message("❌ access_token获取失败", "ERROR")
                result["error"] = "无法获取有效的access_token"
            
            self.test_results["results"]["access_token"] = result
            return result
        except Exception as e:
            error_msg = f"access_token测试异常: {str(e)}"
            log_message(error_msg, "ERROR")
            result = {
                "success": False,
                "error": error_msg
            }
            self.test_results["results"]["access_token"] = result
            return result
    
    def test_category_apis(self):
        """
        测试所有类目相关API
        """
        log_message("\n==================================")
        log_message("开始测试: 类目API")
        log_message("==================================")
        
        results = {}
        category_apis = [
            {"name": "get_all_category", "method": self.client.get_all_category},
            {"name": "get_channels_category", "method": self.client.get_channels_category},
            {"name": "get_category", "method": self.client.get_category}
        ]
        
        for api in category_apis:
            log_message(f"测试API: {api['name']}")
            try:
                # 调用API
                result = api['method']()
                
                # 分析结果
                is_success = result.get("success", False)
                data = result.get("data", {})
                
                # 统计类目数量（如果有）
                category_count = 0
                if is_success and data:
                    # 检查不同的数据格式
                    if isinstance(data, list):
                        category_count = len(data)
                    elif isinstance(data, dict):
                        # 检查是否有嵌套的data字段
                        nested_data = data.get("data")
                        if nested_data:
                            if isinstance(nested_data, list):
                                category_count = len(nested_data)
                            elif isinstance(nested_data, dict) and "cats" in nested_data:
                                category_count = len(nested_data["cats"])
                        # 直接检查cats字段
                        elif "cats" in data:
                            category_count = len(data["cats"])
                        # 检查errcode为0的情况
                        elif data.get("errcode") == 0:
                            # 可能是成功但没有返回数据
                            log_message(f"  API调用成功，但未返回类目数据")
                
                # 构建结果
                api_result = {
                    "success": is_success,
                    "error": result.get("error"),
                    "data_sample": json.dumps(data, ensure_ascii=False)[:200] + "..." if data else None,
                    "category_count": category_count
                }
                
                # 记录结果
                results[api['name']] = api_result
                
                # 保存详细结果（如果成功）
                if is_success and category_count > 0:
                    filename = f"wechat_shop_{api['name']}_result_{get_timestamp()}.json"
                    save_test_result(filename, data)
                    log_message(f"  ✅ 测试成功，获取到 {category_count} 个类目")
                elif is_success:
                    log_message(f"  ✅ 测试成功，但未返回类目数据")
                else:
                    log_message(f"  ❌ 测试失败: {result.get('error', '未知错误')}", "ERROR")
                
                # 避免请求过于频繁
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"  ❌ {api['name']}测试异常: {str(e)}"
                log_message(error_msg, "ERROR")
                results[api['name']] = {
                    "success": False,
                    "error": error_msg
                }
        
        self.test_results["results"]["category_apis"] = results
        return results
    
    def test_product_list_api(self):
        """
        测试获取商品列表API
        """
        log_message("\n==================================")
        log_message("开始测试: 商品列表API")
        log_message("==================================")
        
        try:
            # 调用API
            result = self.client.get_channels_product_list(page=1, size=10)
            
            # 分析结果
            is_success = result.get("success", False) if isinstance(result, dict) else False
            product_count = 0
            total_products = 0
            
            if is_success:
                # 获取商品数量
                if "product_ids" in result:
                    product_count = len(result["product_ids"])
                # 获取总商品数
                if "total_num" in result:
                    total_products = result["total_num"]
                
                log_message(f"✅ 商品列表API测试成功")
                log_message(f"  获取到 {product_count} 个商品，共 {total_products} 个商品")
                
                # 保存结果
                filename = f"wechat_shop_product_list_result_{get_timestamp()}.json"
                save_test_result(filename, result)
            else:
                error_msg = result.get("error", "未知错误") if isinstance(result, dict) else str(result)
                log_message(f"❌ 商品列表API测试失败: {error_msg}", "ERROR")
            
            api_result = {
                "success": is_success,
                "error": error_msg if not is_success else None,
                "product_count": product_count,
                "total_products": total_products
            }
            
            self.test_results["results"]["product_list"] = api_result
            return api_result
            
        except Exception as e:
            error_msg = f"商品列表API测试异常: {str(e)}"
            log_message(error_msg, "ERROR")
            result = {
                "success": False,
                "error": error_msg
            }
            self.test_results["results"]["product_list"] = result
            return result
    
    def test_shop_info_api(self):
        """
        测试获取店铺信息API
        """
        log_message("\n==================================")
        log_message("开始测试: 店铺信息API")
        log_message("==================================")
        
        try:
            # 调用API
            result = self.client.get_shop_info()
            
            # 分析结果
            is_success = result.get("success", False)
            
            if is_success:
                log_message("✅ 店铺信息API测试成功")
                # 保存结果
                filename = f"wechat_shop_info_result_{get_timestamp()}.json"
                save_test_result(filename, result.get("data", {}))
            else:
                error_msg = result.get("error", "未知错误")
                log_message(f"❌ 店铺信息API测试失败: {error_msg}", "ERROR")
            
            api_result = {
                "success": is_success,
                "error": error_msg if not is_success else None
            }
            
            self.test_results["results"]["shop_info"] = api_result
            return api_result
            
        except Exception as e:
            error_msg = f"店铺信息API测试异常: {str(e)}"
            log_message(error_msg, "ERROR")
            result = {
                "success": False,
                "error": error_msg
            }
            self.test_results["results"]["shop_info"] = result
            return result
    
    def test_upload_image_dry_run(self):
        """
        测试图片上传API（仅验证功能，不执行实际上传）
        """
        log_message("\n==================================")
        log_message("开始测试: 图片上传API (dry run)")
        log_message("==================================")
        
        try:
            # 检查API路径是否配置
            if 'upload_image' not in self.api_paths:
                log_message("⚠️  upload_image API路径未配置", "WARNING")
                result = {
                    "success": False,
                    "error": "upload_image API路径未配置",
                    "dry_run": True
                }
                self.test_results["results"]["upload_image"] = result
                return result
            
            log_message(f"✅ 图片上传API路径已配置: {self.api_paths['upload_image']}")
            log_message(f"⚠️  注意：此测试仅验证API路径配置，不会实际上传图片")
            
            # 检查是否有测试图片文件（可选）
            test_image = os.path.join('test_images', 'test.jpg')
            has_test_image = os.path.exists(test_image)
            
            result = {
                "success": True,
                "dry_run": True,
                "api_path": self.api_paths['upload_image'],
                "has_test_image": has_test_image
            }
            
            if has_test_image:
                log_message(f"  发现测试图片: {test_image}")
                result["test_image_path"] = test_image
            else:
                log_message("  未发现测试图片")
            
            self.test_results["results"]["upload_image"] = result
            return result
            
        except Exception as e:
            error_msg = f"图片上传API测试异常: {str(e)}"
            log_message(error_msg, "ERROR")
            result = {
                "success": False,
                "error": error_msg,
                "dry_run": True
            }
            self.test_results["results"]["upload_image"] = result
            return result
    
    def test_product_upload_dry_run(self):
        """
        测试商品上传API（仅验证功能，不执行实际上传）
        """
        log_message("\n==================================")
        log_message("开始测试: 商品上传API (dry run)")
        log_message("==================================")
        
        try:
            # 检查API路径是否配置
            if 'add_product' not in self.api_paths:
                log_message("⚠️  add_product API路径未配置", "WARNING")
                result = {
                    "success": False,
                    "error": "add_product API路径未配置",
                    "dry_run": True
                }
                self.test_results["results"]["add_product"] = result
                return result
            
            log_message(f"✅ 商品上传API路径已配置: {self.api_paths['add_product']}")
            log_message(f"⚠️  注意：此测试仅验证API路径配置，不会实际上传商品")
            
            # 验证商品上传所需的必填字段
            log_message("验证商品上传必填字段:")
            
            # 视频号小店商品必填字段
            required_fields = ['title', 'desc', 'category_id1', 'category_id2', 'sku_list']
            log_message(f"  视频号小店必填字段: {', '.join(required_fields)}")
            
            # 传统微信小店商品必填字段
            from wechat_shop_api import WECHAT_SHOP_REQUIRED_FIELDS
            log_message(f"  传统微信小店必填字段: {', '.join(WECHAT_SHOP_REQUIRED_FIELDS[:5])} ...")
            
            result = {
                "success": True,
                "dry_run": True,
                "api_path": self.api_paths['add_product'],
                "video_shop_required_fields": required_fields,
                "traditional_shop_required_fields": WECHAT_SHOP_REQUIRED_FIELDS
            }
            
            self.test_results["results"]["add_product"] = result
            return result
            
        except Exception as e:
            error_msg = f"商品上传API测试异常: {str(e)}"
            log_message(error_msg, "ERROR")
            result = {
                "success": False,
                "error": error_msg,
                "dry_run": True
            }
            self.test_results["results"]["add_product"] = result
            return result
    
    def run_all_tests(self):
        """
        运行所有测试
        """
        log_message("\n==================================")
        log_message("开始微信小店API综合测试")
        log_message(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_message(f"AppID: {self.api_config.get('appid')}")
        log_message(f"API基础URL: {self.api_config.get('api_base_url')}")
        log_message("==================================")
        
        # 确保测试结果目录存在
        ensure_test_results_dir()
        
        # 运行所有测试
        self.test_access_token()
        self.test_category_apis()
        self.test_product_list_api()
        self.test_shop_info_api()
        self.test_upload_image_dry_run()
        self.test_product_upload_dry_run()
        
        # 统计测试结果
        self._summarize_results()
        
        # 保存总体测试结果
        filename = f"wechat_shop_api_test_summary_{get_timestamp()}.json"
        save_test_result(filename, self.test_results)
        
        return self.test_results
    
    def _summarize_results(self):
        """
        总结测试结果
        """
        log_message("\n==================================")
        log_message("微信小店API测试结果汇总")
        log_message("==================================")
        
        results = self.test_results["results"]
        success_count = 0
        failed_count = 0
        
        for api_name, result in results.items():
            # 对于类目API，需要单独处理（因为包含多个API）
            if api_name == "category_apis":
                log_message(f"\n{api_name}:")
                for sub_api, sub_result in result.items():
                    status = "✅ 成功" if sub_result.get("success") else "❌ 失败"
                    log_message(f"  {sub_api}: {status}")
                    if "category_count" in sub_result and sub_result["category_count"] > 0:
                        log_message(f"    - 类目数量: {sub_result['category_count']}")
                    if not sub_result.get("success"):
                        log_message(f"    - 错误: {sub_result.get('error')}", "ERROR")
            else:
                status = "✅ 成功" if result.get("success") else "❌ 失败"
                log_message(f"{api_name}: {status}")
                
                # 特殊字段显示
                if api_name == "product_list" and "total_products" in result:
                    log_message(f"  总商品数: {result['total_products']}")
                
                if result.get("dry_run"):
                    log_message(f"  (仅验证配置，未执行实际操作)")
                
                if not result.get("success"):
                    log_message(f"  错误: {result.get('error')}", "ERROR")
        
        log_message("\n==================================")
        log_message("测试完成！")
        log_message(f"详细结果已保存到: {TEST_RESULTS_DIR}")
        log_message("==================================")

# 主函数
def main():
    """
    主函数，运行微信小店API综合测试
    """
    try:
        # 创建测试器并运行所有测试
        tester = WeChatShopAPITester()
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        log_message("\n测试被用户中断", "WARNING")
    except Exception as e:
        log_message(f"测试过程中发生异常: {str(e)}", "ERROR")

if __name__ == "__main__":
    main()
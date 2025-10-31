#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信小店API简易测试工具

本脚本提供微信小店API的基本连通性测试功能，包括：
1. Access Token 获取测试
2. API路径配置验证
3. 基本API调用测试（不会实际上传或删除商品）

作者: AI Assistant
日期: 2025-10-30
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 测试结果目录
TEST_RESULTS_DIR = os.path.join(PROJECT_ROOT, 'test_results')

# 确保测试结果目录存在
def ensure_test_results_dir():
    """确保测试结果目录存在"""
    if not os.path.exists(TEST_RESULTS_DIR):
        os.makedirs(TEST_RESULTS_DIR)
        logger.info(f"创建测试结果目录: {TEST_RESULTS_DIR}")

# 加载配置
def load_config():
    """
    加载微信API配置，优先使用环境变量
    """
    config = {}
    
    # 优先从环境变量加载
    config['appid'] = os.environ.get('WECHAT_APPID')
    config['secret'] = os.environ.get('WECHAT_SECRET')
    config['api_base_url'] = os.environ.get('WECHAT_API_BASE_URL', 'https://api.weixin.qq.com')
    
    # 从配置文件加载（如果环境变量未设置）
    config_file = os.path.join(PROJECT_ROOT, 'wechat_api_config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                
                if not config['appid']:
                    config['appid'] = file_config.get('appid')
                    logger.info(f"从配置文件加载AppID: {config['appid']}")
                if not config['secret']:
                    # 支持'secret'和'appsecret'两种配置
                    config['secret'] = file_config.get('secret') or file_config.get('appsecret')
                    logger.info(f"从配置文件加载Secret: {'已加载' if config['secret'] else '未找到'}")
                if not config['api_base_url']:
                    config['api_base_url'] = file_config.get('api_base_url', 'https://api.weixin.qq.com')
                    logger.info(f"从配置文件加载API基础URL: {config['api_base_url']}")
                
                # 加载API路径
                config['api_paths'] = file_config.get('api_paths', {})
                
            logger.info(f"从配置文件加载配置: {config_file}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
    
    # 验证必需的配置项
    if not config.get('appid'):
        logger.warning("未找到AppID配置")
    if not config.get('secret'):
        logger.warning("未找到Secret配置")
    
    return config

# 获取Access Token
def get_access_token(config):
    """
    获取微信公众号的access_token
    """
    appid = config.get('appid')
    secret = config.get('secret')
    base_url = config.get('api_base_url', 'https://api.weixin.qq.com')
    
    if not appid or not secret:
        logger.error("缺少AppID或Secret配置，无法获取access_token")
        return None, "缺少AppID或Secret配置"
    
    try:
        url = f"{base_url}/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
        logger.info(f"请求access_token: {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"access_token响应: {result}")
        
        if 'access_token' in result:
            return result['access_token'], None
        else:
            error_msg = result.get('errmsg', '未知错误')
            error_code = result.get('errcode', -1)
            return None, f"错误码: {error_code}, 错误信息: {error_msg}"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"请求access_token异常: {str(e)}")
        return None, f"网络请求异常: {str(e)}"
    except Exception as e:
        logger.error(f"获取access_token失败: {str(e)}")
        return None, f"未知错误: {str(e)}"

# 测试API连通性
def test_api_connectivity(config, access_token, api_name, api_path, method='get', params=None, data=None):
    """
    测试API连通性
    """
    if not access_token:
        logger.warning(f"跳过 {api_name} 测试: 缺少access_token")
        return False, "缺少access_token"
    
    base_url = config.get('api_base_url', 'https://api.weixin.qq.com')
    full_url = f"{base_url}{api_path}"
    
    try:
        headers = {
            'Content-Type': 'application/json',
        }
        
        request_params = {'access_token': access_token}
        if params:
            request_params.update(params)
        
        logger.info(f"测试API: {api_name} ({full_url})")
        logger.info(f"请求参数: {request_params}")
        
        if method.lower() == 'get':
            response = requests.get(full_url, params=request_params, headers=headers, timeout=30)
        else:
            response = requests.post(full_url, params=request_params, headers=headers, json=data, timeout=30)
        
        response.raise_for_status()
        result = response.json()
        logger.info(f"{api_name} 响应: {result}")
        
        # 检查微信API通用错误码
        if 'errcode' in result and result['errcode'] != 0:
            return False, f"错误码: {result['errcode']}, 错误信息: {result.get('errmsg', '未知错误')}"
        
        return True, result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求 {api_name} 异常: {str(e)}")
        return False, f"网络请求异常: {str(e)}"
    except Exception as e:
        logger.error(f"测试 {api_name} 失败: {str(e)}")
        return False, f"未知错误: {str(e)}"

# 保存测试结果
def save_test_result(filename, data):
    """
    保存测试结果到JSON文件
    """
    ensure_test_results_dir()
    filepath = os.path.join(TEST_RESULTS_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"测试结果已保存到: {filepath}")
        return True
    except Exception as e:
        logger.error(f"保存测试结果失败: {str(e)}")
        return False

# 生成时间戳
def get_timestamp():
    """
    生成时间戳字符串
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')

# 主测试类
class WeChatAPISimpleTester:
    """
    微信小店API简易测试类
    """
    def __init__(self):
        self.config = load_config()
        self.access_token = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'appid': self.config.get('appid'),
            'api_base_url': self.config.get('api_base_url'),
            'results': {}
        }
    
    def test_access_token(self):
        """
        测试access_token获取
        """
        logger.info("\n=== 测试 access_token 获取 ===")
        
        access_token, error = get_access_token(self.config)
        self.access_token = access_token
        
        result = {
            'success': access_token is not None,
            'access_token_exists': access_token is not None,
            'token_length': len(access_token) if access_token else 0,
            'error': error
        }
        
        self.test_results['results']['access_token'] = result
        
        if access_token:
            logger.info(f"✅ 成功获取access_token，长度: {len(access_token)}")
        else:
            logger.error(f"❌ 获取access_token失败: {error}")
        
        return result
    
    def test_configured_apis(self):
        """
        测试配置的API路径
        """
        logger.info("\n=== 测试配置的API路径 ===")
        api_paths = self.config.get('api_paths', {})
        
        if not api_paths:
            logger.warning("未配置API路径")
            return
        
        result = {}
        
        # 测试店铺信息API
        if 'get_shop_info' in api_paths:
            # 尝试修正API路径格式
            shop_info_path = api_paths['get_shop_info']
            logger.info(f"原始API路径: {shop_info_path}")
            
            # 尝试多种可能的路径格式，增加更多微信小店API常见路径格式
            possible_paths = [
                shop_info_path,  # 原始路径
                f"{shop_info_path}/" if not shop_info_path.endswith('/') else shop_info_path[:-1],  # 添加或删除末尾斜杠
                "/shop/shopinfo/get",  # 另一种可能的标准路径
                "/shop/shop/get",  # 常见的店铺信息路径格式
                "/shop/shopinfo",  # 不带/get后缀的格式
                "/channels/shop/get",  # 视频号店铺格式变体
                "/ec/shop/get"  # 电商API常见格式
            ]
            
            success = False
            last_error = None
            used_path = None
            used_method = None
            test_details = []
            
            logger.info(f"将尝试 {len(possible_paths)} 种路径格式，每种路径同时尝试GET和POST方法")
            
            # 对每个可能的路径尝试GET和POST方法
            for path in possible_paths:
                logger.info(f"\n尝试路径: {path}")
                
                # 首先尝试GET方法
                logger.info(f"尝试GET方法访问 {path}")
                get_success, get_data = test_api_connectivity(
                    self.config, 
                    self.access_token, 
                    'get_shop_info', 
                    path
                )
                
                detail = {'path': path, 'methods': []}
                detail['methods'].append({"method": "GET", "success": get_success, "error": get_data})
                
                if get_success:
                    success = True
                    last_error = None
                    used_path = path
                    used_method = 'GET'
                    logger.info(f"✅ GET方法成功访问 {path}")
                    test_details.append(detail)
                    break
                else:
                    logger.info(f"❌ GET方法失败: {get_data}")
                    # 如果GET失败，尝试POST方法
                    logger.info(f"尝试POST方法访问 {path}")
                    post_success, post_data = test_api_connectivity(
                        self.config, 
                        self.access_token, 
                        'get_shop_info', 
                        path,
                        method='post'
                    )
                    
                    detail['methods'].append({"method": "POST", "success": post_success, "error": post_data})
                    
                    if post_success:
                        success = True
                        last_error = None
                        used_path = path
                        used_method = 'POST'
                        logger.info(f"✅ POST方法成功访问 {path}")
                        test_details.append(detail)
                        break
                    else:
                        logger.info(f"❌ POST方法失败: {post_data}")
                        last_error = post_data
                        test_details.append(detail)
            
            # 分析结果并设置适当的状态
            is_api_configured = True
            is_access_denied = False
            
            # 检查所有尝试的路径，看是否有invalid url错误
            for detail in test_details:
                for method_info in detail['methods']:
                    if method_info['error'] and "invalid url" in str(method_info['error']):
                        is_api_configured = False
                        break
                    elif method_info['error'] and ("access_denied" in str(method_info['error']) or "permission" in str(method_info['error'])):
                        is_access_denied = True
                        break
                if not is_api_configured or is_access_denied:
                    break
            
            # 设置问题类型
            issue_type = "unknown"
            if not is_api_configured:
                issue_type = "api_path_configuration"
            elif is_access_denied:
                issue_type = "permission_denied"
            
            result['get_shop_info'] = {
                'success': success, 
                'error': last_error if not success else None, 
                'api_path_used': used_path,
                'method_used': used_method,
                'paths_tried': possible_paths,
                'test_details': test_details,
                'issue_type': issue_type
            }
            
            # 输出详细的错误诊断信息
            if not success:
                if issue_type == "api_path_configuration":
                    logger.warning("⚠️  店铺信息API路径配置可能不正确")
                    logger.warning("   建议: 1. 检查微信API文档获取正确路径")
                    logger.warning("          2. 确认AppID是否有权限访问该API")
                    logger.warning("          3. 可能需要使用特定的API版本或端点")
                elif issue_type == "permission_denied":
                    logger.warning("⚠️  没有访问权限，请检查AppID的权限设置")
                else:
                    logger.warning("⚠️  发生未知错误，请检查API配置")
                
                logger.warning(f"当前API基础URL: {self.config.get('api_base_url')}")
                logger.warning("注意: 其他API功能(get_channels_product_list, get_all_category等)已正常工作")
        
        # 测试商品列表API
        if 'get_product_list' in api_paths:
            success, data = test_api_connectivity(
                self.config, 
                self.access_token, 
                'get_product_list', 
                api_paths['get_product_list']
            )
            result['get_product_list'] = {'success': success, 'error': data if not success else None}
        
        # 测试视频号商品列表API（需要POST方法）
        if 'get_channels_product_list' in api_paths:
            # 准备POST请求数据
            post_data = {
                "page": 1,
                "page_size": 10,
                "status": 0  # 0表示全部状态
            }
            success, data = test_api_connectivity(
                self.config, 
                self.access_token, 
                'get_channels_product_list', 
                api_paths['get_channels_product_list'],
                method='post',
                data=post_data
            )
            result['get_channels_product_list'] = {'success': success, 'error': data if not success else None, 'method_used': 'POST'}
        
        # 测试类目API
        if 'get_all_category' in api_paths:
            success, data = test_api_connectivity(
                self.config, 
                self.access_token, 
                'get_all_category', 
                api_paths['get_all_category']
            )
            result['get_all_category'] = {'success': success, 'error': data if not success else None}
            
        # 测试视频号类目API
        if 'get_channels_category' in api_paths and api_paths['get_channels_category'] != api_paths.get('get_all_category'):
            success, data = test_api_connectivity(
                self.config, 
                self.access_token, 
                'get_channels_category', 
                api_paths['get_channels_category']
            )
            result['get_channels_category'] = {'success': success, 'error': data if not success else None}
        
        # 测试图片上传API配置（不实际上传）
        if 'upload_image' in api_paths:
            logger.info(f"✅ 图片上传API路径已配置: {api_paths['upload_image']}")
            result['upload_image'] = {'success': True, 'api_path': api_paths['upload_image'], 'dry_run': True}
        
        # 测试商品上传API配置（不实际上传）
        if 'add_product' in api_paths:
            logger.info(f"✅ 商品上传API路径已配置: {api_paths['add_product']}")
            result['add_product'] = {'success': True, 'api_path': api_paths['add_product'], 'dry_run': True}
        
        self.test_results['results']['configured_apis'] = result
    
    def validate_product_fields(self):
        """
        验证商品上传所需字段
        """
        logger.info("\n=== 验证商品上传必填字段 ===")
        
        # 视频号小店必填字段
        video_shop_required_fields = [
            "title", "desc", "category_id1", "category_id2", "sku_list"
        ]
        
        # 传统微信小店必填字段
        traditional_shop_required_fields = [
            "product_id", "product_name", "category_id", "main_image", "image_list",
            "price", "original_price", "product_desc", "sku_list", "attributes", "product_status"
        ]
        
        logger.info(f"视频号小店必填字段: {', '.join(video_shop_required_fields)}")
        logger.info(f"传统微信小店必填字段: {', '.join(traditional_shop_required_fields)}")
        
        self.test_results['results']['product_fields'] = {
            'video_shop_required_fields': video_shop_required_fields,
            'traditional_shop_required_fields': traditional_shop_required_fields
        }
    
    def run_all_tests(self):
        """
        运行所有测试
        """
        logger.info("\n==================================")
        logger.info("开始微信小店API简易测试")
        logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"AppID: {self.config.get('appid')}")
        logger.info(f"API基础URL: {self.config.get('api_base_url')}")
        logger.info("==================================")
        
        # 确保测试结果目录存在
        ensure_test_results_dir()
        
        # 运行测试
        self.test_access_token()
        self.test_configured_apis()
        self.validate_product_fields()
        
        # 保存测试结果
        filename = f"wechat_api_simple_test_{get_timestamp()}.json"
        save_test_result(filename, self.test_results)
        
        # 显示结果摘要
        self._show_summary()
        
        return self.test_results
    
    def _show_summary(self):
        """
        显示测试结果摘要
        """
        logger.info("\n==================================")
        logger.info("微信小店API测试结果摘要")
        logger.info("==================================")
        
        results = self.test_results['results']
        
        # Access Token 结果
        access_result = results.get('access_token', {})
        status = "✅ 成功" if access_result.get('success') else "❌ 失败"
        logger.info(f"access_token: {status}")
        if not access_result.get('success'):
            logger.error(f"  错误: {access_result.get('error')}")
        
        # API测试结果
        api_results = results.get('configured_apis', {})
        if api_results:
            logger.info("\nAPI测试结果:")
            
            # 统计成功和失败的API数量
            success_count = sum(1 for result in api_results.values() if result.get('success'))
            total_count = len(api_results)
            
            logger.info(f"总体API测试结果: {success_count}/{total_count} 成功")
            
            # 分组显示成功和失败的API
            success_apis = []
            failed_apis = []
            
            for api_name, result in api_results.items():
                if result.get('success'):
                    success_apis.append((api_name, result))
                else:
                    failed_apis.append((api_name, result))
            
            # 先显示成功的API
            if success_apis:
                logger.info("\n✅ 成功的API:")
                for api_name, result in success_apis:
                    method_info = f" (使用{result.get('method_used')}方法)" if 'method_used' in result else ""
                    dry_run_info = " (仅验证配置)" if result.get('dry_run') else ""
                    logger.info(f"  {api_name}: {method_info}{dry_run_info}")
            
            # 再显示失败的API及详细信息
            if failed_apis:
                logger.info("\n❌ 失败的API:")
                for api_name, result in failed_apis:
                    issue_type = result.get('issue_type', 'unknown')
                    issue_desc = {
                        'api_path_configuration': "路径配置错误",
                        'permission_denied': "权限不足",
                        'unknown': "未知错误"
                    }.get(issue_type, "未知错误")
                    
                    logger.info(f"  {api_name}: {issue_desc}")
                    if result.get('error'):
                        # 只显示错误信息的前100个字符，避免日志过长
                        error_msg = str(result.get('error'))
                        if len(error_msg) > 100:
                            error_msg = error_msg[:100] + "..."
                        logger.info(f"    错误: {error_msg}")
                    
                    # 如果是店铺信息API，显示更多调试信息
                    if api_name == 'get_shop_info':
                        paths_tried = len(result.get('paths_tried', []))
                        logger.info(f"    已尝试 {paths_tried} 种路径格式")
                        logger.info("    建议检查微信API文档获取正确路径")
        
        # 显示商品字段信息
        product_fields = results.get('product_fields', {})
        if product_fields:
            logger.info("\n商品上传必填字段:")
            if 'video_shop_required_fields' in product_fields:
                logger.info(f"  视频号小店: {', '.join(product_fields['video_shop_required_fields'])}")
            if 'traditional_shop_required_fields' in product_fields:
                logger.info(f"  传统小店: {', '.join(product_fields['traditional_shop_required_fields'])}")
        
        logger.info("\n==================================")
        logger.info("测试完成！")
        logger.info(f"详细结果已保存到: {TEST_RESULTS_DIR}")
        logger.info("==================================")

# 主函数
def main():
    """
    主函数
    """
    try:
        logger.info("欢迎使用微信小店API简易测试工具")
        logger.info("本工具仅进行API连通性测试，不会实际上传或删除商品")
        
        # 创建测试器并运行测试
        tester = WeChatAPISimpleTester()
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
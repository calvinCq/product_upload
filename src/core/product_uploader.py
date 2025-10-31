#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商品上传器模块
负责将生成的商品数据上传到微信小店API
"""

import os
import sys
import time
import json
from src.utils.config_manager import get_config_value
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入工具类和配置管理器
from src.utils.logger import log_message
from src.utils.config_manager import ConfigManager, get_config_value

# 尝试导入微信小店API客户端
from src.api.wechat_shop_api import WeChatShopAPIClient


class ProductUploader:
    """
    商品上传器类
    负责将商品数据上传到微信小店
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化商品上传器
        
        :param config_manager: 配置管理器实例
        :param config: 上传配置字典（优先使用config_manager）
        """
        # 使用配置管理器或创建新实例
        self.config_manager = config_manager or ConfigManager()
        
        if config:
            self.config = config
        else:
            # 从配置管理器获取上传相关配置
            self.config = {
                'api': {
                    'appid': get_config_value('wechat_shop.app_id', ''),
                    'appsecret': get_config_value('wechat_shop.app_secret', ''),
                    'api_base_url': get_config_value('wechat_shop.api_base_url', 'https://api.weixin.qq.com')
                },
                'upload': {
                    'batch_size': get_config_value('upload.batch_size', 10),
                    'request_interval': get_config_value('upload.request_interval', 1),
                    'max_retries': get_config_value('upload.max_retries', 3),
                    'timeout': get_config_value('upload.timeout', 30),
                    'max_concurrency': get_config_value('upload.max_concurrency', 5)
                }
            }
            log_message("成功从配置管理器加载配置")
        
        self.api_client = None
        self._initialize_api_client()
        self._validate_config()
        
        # 初始化统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }
    
    def _initialize_api_client(self):
        """
        初始化API客户端
        """
        try:
            if WeChatShopAPIClient is None:
                raise ImportError("WeChatShopAPIClient未找到")
            
            # 确保api_config有值
            api_config = self.config.get('api', {})
            if not api_config:
                api_config = {
                    'appid': get_config_value('wechat_shop.app_id', ''),
                    'appsecret': get_config_value('wechat_shop.app_secret', ''),
                    'api_base_url': get_config_value('wechat_shop.api_base_url', 'https://api.weixin.qq.com')
                }
                self.config['api'] = api_config
            
            # 检查必需的配置项
            required_fields = ['appid', 'appsecret']
            missing_fields = [field for field in required_fields if field not in api_config]
            
            if missing_fields:
                raise ValueError(f"API配置不完整，缺少以下字段: {', '.join(missing_fields)}")
            
            # 初始化API客户端
            app_id = api_config.get('appid', '')
            app_secret = api_config.get('appsecret', '')
            self.api_client = WeChatShopAPIClient(appid=app_id, appsecret=app_secret, api_config=api_config)
            
            log_message("微信小店API客户端初始化成功")
            
        except Exception as e:
            error_msg = f"初始化API客户端失败: {str(e)}"
            log_message(error_msg, "ERROR")
            # 在测试环境可以不抛出异常，允许继续执行
            use_sandbox = api_config.get('use_sandbox', False) if 'api_config' in locals() else False
            if not use_sandbox:
                raise Exception(error_msg)
    
    def _validate_config(self):
        """
        验证上传配置的有效性
        """
        # 设置默认值
        if 'upload' not in self.config:
            self.config['upload'] = {}
        
        upload_config = self.config['upload']
        
        # 设置默认值并验证范围
        defaults = {
            'batch_size': 10,
            'request_interval': 1,  # 秒
            'max_retries': 3,
            'timeout': 30,  # 秒
            'max_concurrency': 5
        }
        
        ranges = {
            'batch_size': (1, 100),
            'request_interval': (0.1, 60),
            'max_retries': (0, 10),
            'timeout': (5, 300),
            'max_concurrency': (1, 20)
        }
        
        # 应用默认值并验证范围
        for key, default in defaults.items():
            if key not in upload_config:
                upload_config[key] = default
                log_message(f"配置项 '{key}' 未设置，使用默认值: {default}")
            else:
                # 验证范围
                if key in ranges:
                    min_val, max_val = ranges[key]
                    if not (min_val <= upload_config[key] <= max_val):
                        log_message(f"配置项 '{key}' 值 {upload_config[key]} 超出有效范围 [{min_val}, {max_val}]，调整为默认值: {default}", "WARNING")
                        upload_config[key] = default
        
        log_message(f"上传配置验证完成: {upload_config}")
    
    def _validate_product_data(self, product_data: Dict[str, Any]) -> bool:
        """
        验证商品数据的有效性
        
        :param product_data: 商品数据
        :return: 是否有效
        """
        required_fields = ['title', 'head_imgs', 'price', 'cats']
        
        # 检查必填字段
        for field in required_fields:
            if field not in product_data or not product_data[field]:
                log_message(f"商品数据缺少必填字段: {field}", "ERROR")
                return False
        
        # 检查主图数量
        if len(product_data.get('head_imgs', [])) == 0:
            log_message("商品缺少主图", "ERROR")
            return False
        
        # 检查价格格式
        if 'price' in product_data:
            try:
                float(product_data['price'])
            except (ValueError, TypeError):
                log_message("商品价格格式无效", "ERROR")
                return False
        
        log_message(f"商品数据验证通过: {product_data.get('title', '未知标题')}")
        return True
    
    def upload_single_product(self, product: Dict[str, Any], retry_count: int = 0) -> tuple:
        """
        上传单个商品
        
        :param product: 商品数据
        :param retry_count: 当前重试次数
        :return: (是否成功, 响应结果)
        """
        # 验证商品数据
        if not self._validate_product_data(product):
            return False, {'error': '商品数据验证失败'}
        
        try:
            if not self.api_client:
                self._initialize_api_client()
            
            max_retries = self.config['upload'].get('max_retries', 3)
            
            # 调用API上传商品
            log_message(f"开始上传商品: {product.get('title', '未知标题')}, 第{retry_count + 1}次尝试")
            response = self.api_client.add_product(product)
            
            # 检查上传结果
            if response and isinstance(response, dict):
                if response.get('errcode') == 0:
                    product_id = response.get('product_id', '')
                    log_message(f"商品上传成功: {product['title']} (商品ID: {product_id})")
                    return True, response
                else:
                    error_code = response.get('errcode')
                    error_msg = response.get('errmsg', '未知错误')
                    log_message(f"商品上传失败: {product['title']}, 错误码: {error_code}, 错误信息: {error_msg}", "ERROR")
                    
                    # 判断是否需要重试（某些错误码可能不适合重试）
                    non_retryable_codes = [400, 401, 403]  # 示例：添加不需要重试的错误码
                    if retry_count < max_retries and error_code not in non_retryable_codes:
                        wait_time = (retry_count + 1) * 2  # 指数退避
                        log_message(f"准备第{retry_count + 1}次重试，等待{wait_time}秒", "WARNING")
                        time.sleep(wait_time)
                        return self.upload_single_product(product, retry_count + 1)
            else:
                log_message(f"API返回异常响应: {str(response)}", "ERROR")
            
            return False, response or {'error': '未知错误'}
            
        except Exception as e:
            error_msg = f"上传商品时发生异常: {str(e)}"
            log_message(error_msg, "ERROR")
            
            # 异常情况下也尝试重试
            if retry_count < max_retries:
                wait_time = (retry_count + 1) * 2
                log_message(f"因异常准备第{retry_count + 1}次重试，等待{wait_time}秒", "WARNING")
                time.sleep(wait_time)
                return self.upload_single_product(product, retry_count + 1)
            
            return False, {'error': str(e)}
    
    def test_connection(self) -> bool:
        """
        测试与上传服务器的连接
        
        :return: 连接是否成功
        """
        try:
            if not self.api_client:
                self._initialize_api_client()
            
            # 这里假设WeChatShopAPIClient有test_connection方法
            # 如果没有，可以实现一个简单的token获取或其他轻量级操作
            log_message("测试微信小店API连接")
            
            # 尝试获取access_token作为连接测试
            if hasattr(self.api_client, 'get_access_token'):
                try:
                    # 调用get_access_token方法
                    token_result = self.api_client.get_access_token()
                    
                    # 检查结果是否有效
                    # 注意：由于_get_refresh_access_token返回的是访问令牌本身或None
                    # 而不是字典结果，我们需要调整判断逻辑
                    if token_result:
                        log_message(f"成功获取access_token，连接测试通过")
                        return True
                    else:
                        log_message("获取access_token失败，可能是配置不完整或网络问题", "WARNING")
                        return False
                except Exception as token_error:
                    log_message(f"获取access_token时发生异常: {str(token_error)}", "WARNING")
                    return False
            else:
                log_message("无法测试连接，API客户端缺少get_access_token方法", "WARNING")
                return False
                
        except Exception as e:
            log_message(f"连接测试失败: {str(e)}", "ERROR")
            return False
    
    def upload_products(self, products):
        """
        批量上传商品
        
        :param products: 商品列表
        :return: 上传结果统计和详细记录
        """
        if not products:
            log_message("没有需要上传的商品", "WARNING")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'details': []
            }
        
        log_message(f"开始批量上传{len(products)}个商品")
        
        upload_config = self.config['upload']
        batch_size = upload_config['batch_size']
        request_interval = upload_config['request_interval']
        
        results = {
            'total': len(products),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        start_time = time.time()
        
        # 分批处理
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            batch_start = i + 1
            batch_end = min(i + batch_size, len(products))
            
            log_message(f"处理批次 {batch_start}-{batch_end}/{len(products)}")
            
            for j, product in enumerate(batch):
                current_index = i + j + 1
                log_message(f"上传商品 {current_index}/{len(products)}: {product['title']}")
                
                success, response = self.upload_single_product(product)
                
                # 记录结果
                detail = {
                    'index': current_index,
                    'title': product['title'],
                    'out_product_id': product.get('out_product_id', ''),
                    'success': success,
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                }
                results['details'].append(detail)
                
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                
                # 避免请求过于频繁
                if j < len(batch) - 1:  # 不是批次中最后一个商品
                    log_message(f"请求间隔: {request_interval}秒")
                    time.sleep(request_interval)
        
        # 计算统计信息
        results['duration'] = round(time.time() - start_time, 2)
        if results['total'] > 0:
            results['success_rate'] = round(results['success'] / results['total'] * 100, 2)
        else:
            results['success_rate'] = 0
        
        log_message(f"批量上传完成，总商品数: {results['total']}, 成功: {results['success']}, 失败: {results['failed']}, "
                   f"成功率: {results['success_rate']}%, 耗时: {results['duration']}秒")
        
        return results
    
    async def upload_products_async(self, products):
        """
        异步批量上传商品
        
        :param products: 商品列表
        :return: 上传结果统计和详细记录
        """
        if not products:
            log_message("没有需要上传的商品", "WARNING")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'details': []
            }
        
        log_message(f"开始异步批量上传{len(products)}个商品")
        
        # 限制并发数
        max_concurrency = min(self.config['upload'].get('max_concurrency', 5), len(products))
        semaphore = asyncio.Semaphore(max_concurrency)
        
        results = {
            'total': len(products),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        async def upload_with_semaphore(product, index):
            async with semaphore:
                log_message(f"异步上传商品 {index}/{len(products)}: {product['title']}")
                
                # 使用线程池执行同步的上传操作
                loop = asyncio.get_event_loop()
                success, response = await loop.run_in_executor(
                    None, self.upload_single_product, product
                )
                
                detail = {
                    'index': index,
                    'title': product['title'],
                    'out_product_id': product.get('out_product_id', ''),
                    'success': success,
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                }
                
                return detail
        
        start_time = time.time()
        
        # 创建所有任务
        tasks = [
            upload_with_semaphore(product, i + 1)
            for i, product in enumerate(products)
        ]
        
        # 等待所有任务完成
        details = await asyncio.gather(*tasks)
        
        # 统计结果
        for detail in details:
            results['details'].append(detail)
            if detail['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
        
        # 计算统计信息
        results['duration'] = round(time.time() - start_time, 2)
        if results['total'] > 0:
            results['success_rate'] = round(results['success'] / results['total'] * 100, 2)
        else:
            results['success_rate'] = 0
        
        log_message(f"异步批量上传完成，总商品数: {results['total']}, 成功: {results['success']}, 失败: {results['failed']}, "
                   f"成功率: {results['success_rate']}%, 耗时: {results['duration']}秒")
        
        return results
    
    def save_upload_results(self, results=None, file_path=None) -> bool:
        """
        保存上传结果到文件
        
        :param results: 上传结果（如果不提供则使用内部stats）
        :param file_path: 文件路径（如果不提供则自动生成）
        :return: 是否成功
        """
        # 使用提供的结果或内部stats
        results_to_save = results or self.stats
        
        # 生成文件名
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
            
            # 创建目录
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                except OSError as e:
                    log_message(f"创建结果目录失败: {e}", "ERROR")
                    return False
            
            file_path = os.path.join(output_dir, f'upload_results_{timestamp}.json')
        
        try:
            # 为了保存到文件，需要处理可能无法序列化的对象
            serializable_results = self._make_results_serializable(results_to_save)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            log_message(f"成功保存上传结果到文件: {file_path}")
            return True
            
        except Exception as e:
            log_message(f"保存上传结果失败: {str(e)}", "ERROR")
            return False
    
    def close(self):
        """
        关闭资源
        """
        # 如果API客户端有close方法，调用它
        if hasattr(self.api_client, 'close'):
            try:
                self.api_client.close()
                log_message("API客户端已关闭")
            except Exception:
                pass
    
    def __enter__(self):
        """
        支持上下文管理器
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器时关闭资源
        """
        self.close()
    
    def _make_results_serializable(self, results):
        """
        将结果转换为可序列化的格式
        
        :param results: 原始结果
        :return: 可序列化的结果
        """
        serializable = results.copy()
        
        # 处理详情列表中的每个条目
        if 'details' in serializable:
            for detail in serializable['details']:
                if 'response' in detail:
                    # 确保响应是字典格式
                    if not isinstance(detail['response'], dict):
                        detail['response'] = {'result': str(detail['response'])}
        
        return serializable
    
    def generate_upload_report(self, results, file_path=None):
        """
        生成上传报告
        
        :param results: 上传结果
        :param file_path: 报告文件路径，如果为None则只返回报告内容
        :return: 报告内容
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("微信小店商品上传报告")
        report_lines.append("=" * 60)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"总商品数: {results.get('total', 0)}")
        report_lines.append(f"成功数量: {results.get('success', 0)}")
        report_lines.append(f"失败数量: {results.get('failed', 0)}")
        report_lines.append(f"成功率: {results.get('success_rate', 0)}%")
        report_lines.append(f"总耗时: {results.get('duration', 0)}秒")
        
        # 按成功率计算评级
        success_rate = results.get('success_rate', 0)
        if success_rate >= 95:
            rating = "优秀"
        elif success_rate >= 80:
            rating = "良好"
        elif success_rate >= 60:
            rating = "一般"
        else:
            rating = "较差"
        report_lines.append(f"上传评级: {rating}")
        
        report_lines.append("\n" + "=" * 60)
        report_lines.append("失败商品详情:")
        report_lines.append("=" * 60)
        
        # 统计失败原因
        failed_count = 0
        error_codes = {}
        
        for detail in results.get('details', []):
            if not detail.get('success'):
                failed_count += 1
                response = detail.get('response', {})
                error_code = response.get('errcode', '未知')
                error_msg = response.get('errmsg', '未知错误')
                
                error_codes[error_code] = error_codes.get(error_code, 0) + 1
                
                report_lines.append(f"商品 {detail.get('index')}: {detail.get('title')}")
                report_lines.append(f"  错误码: {error_code}")
                report_lines.append(f"  错误信息: {error_msg}")
                report_lines.append("-" * 60)
        
        if failed_count == 0:
            report_lines.append("无失败商品")
        
        report_lines.append("\n" + "=" * 60)
        report_lines.append("错误码统计:")
        report_lines.append("=" * 60)
        
        for code, count in error_codes.items():
            report_lines.append(f"错误码 {code}: {count}次")
        
        report_content = "\n".join(report_lines)
        
        # 保存到文件
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                log_message(f"成功生成上传报告: {file_path}")
            except Exception as e:
                log_message(f"保存上传报告失败: {str(e)}", "ERROR")
        
        return report_content


def test_product_uploader():
    """
    测试商品上传器功能
    """
    print("商品上传器测试")
    
    # 优先使用配置管理器
    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        
        # 创建上传器
        uploader = ProductUploader(config_manager)
        
        # 测试连接
        print("\n测试连接...")
        connected = uploader.test_connection()
        print(f"连接测试: {'成功' if connected else '失败'}")
        
        # 创建测试商品数据
        test_product = {
            "title": "测试商品 - Python数据分析课程",
            "sub_title": "限时促销 - 数据分析实战",
            "short_title": "Python数据分析",
            "desc_info": {
                "imgs": ["https://example.com/course_detail.jpg"],
                "desc": "本课程从零基础开始，系统讲解Python数据分析的核心技能。"
            },
            "head_imgs": [
                "https://example.com/course_main.jpg"
            ],
            "deliver_method": 0,
            "cats": [
                {"cat_id": "100"}  # 示例分类ID
            ],
            "cats_v2": [
                {"cat_id": "100"}
            ],
            "extra_service": {
                "service_tags": []
            },
            "skus": [
                {
                    "price": 299,
                    "stock_num": 100,
                    "out_sku_id": "SKU_COURSE_001"
                }
            ],
            "listing": 0,  # 不上架，仅用于测试
            "out_product_id": "TEST_COURSE_001",
            "express_info": {
                "express_type": 0,
                "template_id": "default_template"
            }
        }
        
        # 如果连接成功，提示用户配置API信息
        if connected:
            print("\n连接成功！如需实际测试上传功能，请确保:")
            print("1. 配置文件中已设置有效的appid和appsecret")
            print("2. 测试商品数据中的分类ID在微信小店中存在")
            print("3. 图片URL可正常访问")
        else:
            print("\n连接失败，请检查API配置信息")
            print("您可以在.env文件或配置文件中设置API密钥")
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        print("请检查配置文件和依赖项")
    
    print("\n测试完成")


def main():
    """
    主函数
    """
    test_product_uploader()


if __name__ == "__main__":
    main()
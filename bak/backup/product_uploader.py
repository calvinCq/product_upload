#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商品上传模块
负责将生成的商品数据上传到微信小店API
"""

import time
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 导入现有的API客户端和日志功能
from wechat_shop_api import WeChatShopAPIClient, log_message


class ProductUploader:
    """
    商品上传器类
    负责将商品数据上传到微信小店
    """
    
    def __init__(self, config):
        """
        初始化商品上传器
        
        :param config: 上传配置字典
        """
        self.config = config
        self.api_client = None
        self._initialize_api_client()
        self._validate_config()
    
    def _initialize_api_client(self):
        """
        初始化API客户端
        """
        try:
            api_config = self.config.get('api', {})
            if not api_config or 'appid' not in api_config or 'appsecret' not in api_config:
                raise ValueError("API配置不完整，缺少appid或appsecret")
            
            self.api_client = WeChatShopAPIClient(
                appid=api_config['appid'],
                appsecret=api_config['appsecret']
            )
            log_message("API客户端初始化成功")
            
        except Exception as e:
            error_msg = f"初始化API客户端失败: {str(e)}"
            log_message(error_msg, "ERROR")
            raise
    
    def _validate_config(self):
        """
        验证上传配置的有效性
        """
        # 设置默认值
        if 'upload' not in self.config:
            self.config['upload'] = {}
        
        upload_config = self.config['upload']
        if 'batch_size' not in upload_config:
            upload_config['batch_size'] = 10
        if 'request_interval' not in upload_config:
            upload_config['request_interval'] = 1  # 秒
        if 'max_retries' not in upload_config:
            upload_config['max_retries'] = 3
        if 'timeout' not in upload_config:
            upload_config['timeout'] = 30  # 秒
        
        # 验证配置范围
        if upload_config['batch_size'] < 1 or upload_config['batch_size'] > 100:
            log_message("批量大小超出范围，调整为默认值10", "WARNING")
            upload_config['batch_size'] = 10
        
        if upload_config['request_interval'] < 0.1:
            log_message("请求间隔过小，调整为默认值1秒", "WARNING")
            upload_config['request_interval'] = 1
    
    def upload_single_product(self, product, retry_count=0):
        """
        上传单个商品
        
        :param product: 商品数据
        :param retry_count: 当前重试次数
        :return: (是否成功, 响应结果)
        """
        try:
            if not self.api_client:
                self._initialize_api_client()
            
            max_retries = self.config['upload'].get('max_retries', 3)
            
            # 调用API上传商品
            response = self.api_client.add_product(product)
            
            # 检查上传结果
            if response and isinstance(response, dict):
                if response.get('errcode') == 0:
                    product_id = response.get('product_id', '')
                    log_message(f"商品上传成功: {product['title']} (商品ID: {product_id})")
                    return True, response
                else:
                    error_msg = f"商品上传失败: {product['title']}, 错误码: {response.get('errcode')}, 错误信息: {response.get('errmsg')}"
                    log_message(error_msg, "ERROR")
                    
                    # 判断是否需要重试
                    if retry_count < max_retries:
                        wait_time = (retry_count + 1) * 2  # 指数退避
                        log_message(f"准备第{retry_count + 1}次重试，等待{wait_time}秒", "WARNING")
                        time.sleep(wait_time)
                        return self.upload_single_product(product, retry_count + 1)
            
            return False, response
            
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
    
    def save_upload_results(self, results, file_path):
        """
        保存上传结果到文件
        
        :param results: 上传结果
        :param file_path: 文件路径
        :return: 是否成功
        """
        try:
            # 为了保存到文件，需要处理可能无法序列化的对象
            serializable_results = self._make_results_serializable(results)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            log_message(f"成功保存上传结果到文件: {file_path}")
            return True
            
        except Exception as e:
            log_message(f"保存上传结果失败: {str(e)}", "ERROR")
            return False
    
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


def main():
    """
    测试商品上传器功能（仅用于测试，需要配置有效的API信息）
    """
    # 测试配置
    test_config = {
        'api': {
            'appid': 'YOUR_APPID',  # 需要替换为实际的appid
            'secret': 'YOUR_SECRET',  # 需要替换为实际的secret
            'use_sandbox': False
        },
        'upload': {
            'batch_size': 5,
            'request_interval': 2,
            'max_retries': 3,
            'timeout': 30,
            'max_concurrency': 3
        }
    }
    
    # 测试数据（仅用于测试）
    test_product = {
        "title": "测试商品 - 电子产品",
        "sub_title": "限时促销",
        "short_title": "测试商品",
        "desc_info": {
            "imgs": ["https://example.com/detail1.jpg"],
            "desc": "这是一个测试商品描述"
        },
        "head_imgs": [
            "https://example.com/product1.jpg",
            "https://example.com/product2.jpg",
            "https://example.com/product3.jpg"
        ],
        "deliver_method": 0,
        "cats": [
            {"cat_id": "381003"},
            {"cat_id": "380003"},
            {"cat_id": "517050"}
        ],
        "cats_v2": [
            {"cat_id": "381003"},
            {"cat_id": "380003"},
            {"cat_id": "517050"}
        ],
        "extra_service": {
            "service_tags": []
        },
        "skus": [
            {
                "price": 999,
                "stock_num": 100,
                "out_sku_id": "SKU_TEST_1"
            }
        ],
        "listing": 0,  # 不上架，仅用于测试
        "out_product_id": "TEST_PROD_001",
        "express_info": {
            "express_type": 0,
            "template_id": "default_template"
        }
    }
    
    # 创建上传器（仅用于测试）
    print("商品上传器测试")
    print("注意：请先配置有效的API信息")
    print("如需实际测试，请修改test_config中的appid和secret")
    print("\n测试功能将使用模拟数据进行演示")
    
    # 创建上传器并执行实际上传
    print("\n开始实际上传测试:")
    uploader = ProductUploader(test_config)
    
    # 注意：执行实际上传需要配置有效的API信息
    # 这里使用一个简化的商品列表进行演示
    test_products = [test_product]
    
    try:
        # 执行实际的上传操作
        print(f"准备上传{len(test_products)}个商品")
        results = uploader.upload_products(test_products)
        
        # 生成并显示报告
        print("\n上传结果报告:")
        report = uploader.generate_upload_report(results)
        print(report)
    except Exception as e:
        print(f"上传过程中发生错误: {str(e)}")
        print("请确保已正确配置API信息(appid和secret)")


if __name__ == "__main__":
    main()
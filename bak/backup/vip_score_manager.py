#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
积分查询模块
负责调用微信小店的get_vip_user_score接口查询用户积分
"""

import time
import json
from datetime import datetime

# 导入现有的API客户端、日志功能和API路径配置
from wechat_shop_api import WeChatShopAPIClient, log_message, API_PATHS


class VipScoreManager:
    """
    VIP积分管理器类
    负责查询和管理用户的VIP积分信息
    """
    
    def __init__(self, config):
        """
        初始化积分管理器
        
        :param config: 配置字典
        """
        self.config = config
        self.api_client = None
        self._initialize_api_client()
        self._validate_config()
        
        # 使用统一的API路径配置
        self.api_paths = API_PATHS.copy()
    
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
            log_message("积分查询API客户端初始化成功")
            
        except Exception as e:
            error_msg = f"初始化积分查询API客户端失败: {str(e)}"
            log_message(error_msg, "ERROR")
            raise
    
    def _validate_config(self):
        """
        验证积分查询配置的有效性
        """
        # 初始化积分配置
        if 'points' not in self.config:
            self.config['points'] = {}
        
        vip_config = self.config['points']
        
        # 设置默认值
        if 'enabled' not in vip_config:
            vip_config['enabled'] = False
        if 'request_interval' not in vip_config:
            vip_config['request_interval'] = 1  # 秒
        if 'max_retries' not in vip_config:
            vip_config['max_retries'] = 3
        if 'timeout' not in vip_config:
            vip_config['timeout'] = 30  # 秒
        
        # 如果未启用积分功能，记录警告
        if not vip_config['enabled']:
            log_message("积分查询功能未启用，请在配置中设置enabled=true以启用", "WARNING")
    
    def get_vip_user_score(self, openid, retry_count=0):
        """
        查询单个用户的积分信息
        参考API文档: https://developers.weixin.qq.com/doc/store/shop/API/vip/api_getvipuserscore.html
        
        :param openid: 用户的openid
        :param retry_count: 当前重试次数
        :return: (是否成功, 积分信息或错误信息)
        """
        # 检查是否启用积分功能
        if not self.config['points'].get('enabled', False):
            log_message("积分查询功能未启用", "WARNING")
            return False, {"error": "积分查询功能未启用"}
        
        try:
            if not self.api_client:
                self._initialize_api_client()
            
            # 验证openid参数
            if not openid or not isinstance(openid, str):
                log_message(f"无效的openid参数: {openid}", "ERROR")
                return False, {"error": "无效的openid参数"}
            
            max_retries = self.config['points'].get('max_retries', 3)
            request_interval = self.config['points'].get('request_interval', 1)
            
            # 构建请求参数
            params = {
                'openid': openid
            }
            
            # 调用API
            api_path = self.api_paths['get_vip_user_score']
            response = self.api_client._api_request('GET', api_path, params=params)
            
            # 检查响应结果
            if response and isinstance(response, dict):
                if response.get('errcode') == 0:
                    # 成功响应格式: {"errcode": 0, "errmsg": "success", "score": 100}
                    score = response.get('score', 0)
                    log_message(f"查询用户 {openid} 积分成功: {score} 分")
                    
                    # 返回结构化的积分信息
                    score_info = {
                        'openid': openid,
                        'score': score,
                        'query_time': datetime.now().isoformat(),
                        'raw_response': response
                    }
                    return True, score_info
                else:
                    # 错误响应
                    error_msg = f"查询用户 {openid} 积分失败: 错误码 {response.get('errcode')}, 错误信息 {response.get('errmsg')}"
                    log_message(error_msg, "ERROR")
                    
                    # 判断是否需要重试
                    if retry_count < max_retries:
                        # 某些错误不适合重试
                        error_code = response.get('errcode')
                        no_retry_codes = [40013, 40001]  # invalid credential, invalid access_token
                        
                        if error_code not in no_retry_codes:
                            wait_time = (retry_count + 1) * 2  # 指数退避
                            log_message(f"准备第{retry_count + 1}次重试，等待{wait_time}秒", "WARNING")
                            time.sleep(wait_time)
                            return self.get_vip_user_score(openid, retry_count + 1)
            
            return False, response or {"error": "未知错误"}
            
        except Exception as e:
            error_msg = f"查询用户积分时发生异常: {str(e)}"
            log_message(error_msg, "ERROR")
            
            # 异常情况下尝试重试
            if retry_count < max_retries:
                wait_time = (retry_count + 1) * 2
                log_message(f"因异常准备第{retry_count + 1}次重试，等待{wait_time}秒", "WARNING")
                time.sleep(wait_time)
                return self.get_vip_user_score(openid, retry_count + 1)
            
            return False, {"error": str(e)}
    
    def batch_get_vip_user_scores(self, openids):
        """
        批量查询多个用户的积分信息
        
        :param openids: 用户openid列表
        :return: 查询结果统计和详细记录
        """
        # 检查是否启用积分功能
        if not self.config['points'].get('enabled', False):
            log_message("积分查询功能未启用", "WARNING")
            return {
                'total': len(openids),
                'success': 0,
                'failed': len(openids),
                'details': [],
                'error': "积分查询功能未启用"
            }
        
        if not openids or not isinstance(openids, list):
            log_message("无效的openid列表", "ERROR")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'details': [],
                'error': "无效的openid列表"
            }
        
        log_message(f"开始批量查询{len(openids)}个用户的积分信息")
        
        request_interval = self.config['points'].get('request_interval', 1)
        
        results = {
            'total': len(openids),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        start_time = time.time()
        
        # 逐个查询用户积分（注意：API不支持批量查询，需要逐个调用）
        for i, openid in enumerate(openids):
            log_message(f"查询用户 {i+1}/{len(openids)}: {openid}")
            
            success, score_info = self.get_vip_user_score(openid)
            
            # 记录结果
            detail = {
                'index': i + 1,
                'openid': openid,
                'success': success,
                'score': score_info.get('score', None) if success else None,
                'error': score_info.get('error', None) if not success else None,
                'query_time': datetime.now().isoformat()
            }
            results['details'].append(detail)
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            # 避免请求过于频繁
            if i < len(openids) - 1:  # 不是列表中最后一个用户
                log_message(f"请求间隔: {request_interval}秒")
                time.sleep(request_interval)
        
        # 计算统计信息
        results['duration'] = round(time.time() - start_time, 2)
        if results['total'] > 0:
            results['success_rate'] = round(results['success'] / results['total'] * 100, 2)
        else:
            results['success_rate'] = 0
        
        # 计算总积分和平均积分（仅成功的查询）
        if results['success'] > 0:
            total_score = sum(detail['score'] for detail in results['details'] if detail['success'])
            results['total_score'] = total_score
            results['average_score'] = round(total_score / results['success'], 2)
        else:
            results['total_score'] = 0
            results['average_score'] = 0
        
        log_message(f"批量查询完成，总用户数: {results['total']}, 成功: {results['success']}, 失败: {results['failed']}, "
                   f"成功率: {results['success_rate']}%, 总积分: {results.get('total_score', 0)}, "
                   f"平均积分: {results.get('average_score', 0)}, 耗时: {results['duration']}秒")
        
        return results
    
    def save_score_results(self, results, file_path):
        """
        保存积分查询结果到文件
        
        :param results: 查询结果
        :param file_path: 文件路径
        :return: 是否成功
        """
        try:
            # 为了保存到文件，需要处理可能无法序列化的对象
            serializable_results = self._make_results_serializable(results)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            log_message(f"成功保存积分查询结果到文件: {file_path}")
            return True
            
        except Exception as e:
            log_message(f"保存积分查询结果失败: {str(e)}", "ERROR")
            return False
    
    def _make_results_serializable(self, results):
        """
        将结果转换为可序列化的格式
        
        :param results: 原始结果
        :return: 可序列化的结果
        """
        serializable = results.copy()
        
        # 移除可能无法序列化的字段
        if 'details' in serializable:
            for detail in serializable['details']:
                if 'raw_response' in detail:
                    del detail['raw_response']
        
        return serializable
    
    def generate_score_report(self, results, file_path=None):
        """
        生成积分查询报告
        
        :param results: 查询结果
        :param file_path: 报告文件路径，如果为None则只返回报告内容
        :return: 报告内容
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("微信小店用户积分查询报告")
        report_lines.append("=" * 60)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"总查询用户数: {results.get('total', 0)}")
        report_lines.append(f"成功查询数: {results.get('success', 0)}")
        report_lines.append(f"失败查询数: {results.get('failed', 0)}")
        report_lines.append(f"成功率: {results.get('success_rate', 0)}%")
        report_lines.append(f"总耗时: {results.get('duration', 0)}秒")
        
        if results.get('success', 0) > 0:
            report_lines.append(f"总积分: {results.get('total_score', 0)}")
            report_lines.append(f"平均积分: {results.get('average_score', 0)}")
            
            # 找出积分最高的用户
            max_score = -1
            max_score_user = None
            for detail in results.get('details', []):
                if detail.get('success') and detail.get('score', 0) > max_score:
                    max_score = detail.get('score', 0)
                    max_score_user = detail.get('openid')
            
            if max_score_user:
                report_lines.append(f"积分最高用户: {max_score_user} ({max_score}分)")
        
        report_lines.append("\n" + "=" * 60)
        report_lines.append("查询失败用户详情:")
        report_lines.append("=" * 60)
        
        failed_count = 0
        error_types = {}
        
        for detail in results.get('details', []):
            if not detail.get('success'):
                failed_count += 1
                error_msg = detail.get('error', '未知错误')
                
                # 简单的错误类型分类
                error_key = self._categorize_error(error_msg)
                error_types[error_key] = error_types.get(error_key, 0) + 1
                
                report_lines.append(f"用户 {detail.get('openid')}")
                report_lines.append(f"  错误信息: {error_msg}")
                report_lines.append("-" * 60)
        
        if failed_count == 0:
            report_lines.append("无失败查询")
        
        report_lines.append("\n" + "=" * 60)
        report_lines.append("错误类型统计:")
        report_lines.append("=" * 60)
        
        for error_type, count in error_types.items():
            report_lines.append(f"{error_type}: {count}次")
        
        report_content = "\n".join(report_lines)
        
        # 保存到文件
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                log_message(f"成功生成积分查询报告: {file_path}")
            except Exception as e:
                log_message(f"保存积分查询报告失败: {str(e)}", "ERROR")
        
        return report_content
    
    def _categorize_error(self, error_msg):
        """
        对错误信息进行简单分类
        
        :param error_msg: 错误信息
        :return: 错误类型
        """
        error_categories = [
            ("token", "Token错误"),
            ("credential", "凭证错误"),
            ("permission", "权限错误"),
            ("not found", "未找到错误"),
            ("invalid", "参数无效"),
            ("limit", "频率限制"),
            ("system", "系统错误")
        ]
        
        error_msg_lower = str(error_msg).lower()
        for keyword, category in error_categories:
            if keyword in error_msg_lower:
                return category
        
        return "其他错误"
    
    def validate_integration_with_product(self, product, user_score_info):
        """
        验证积分与商品的集成（例如根据积分提供折扣）
        此功能可以根据业务需求扩展
        
        :param product: 商品信息
        :param user_score_info: 用户积分信息
        :return: 集成验证结果
        """
        if not product or not user_score_info:
            return False, {"error": "无效的商品或积分信息"}
        
        try:
            # 简单的示例逻辑：根据积分决定是否可以购买
            score = user_score_info.get('score', 0)
            min_score_required = product.get('min_score_required', 0)
            
            if score >= min_score_required:
                result = {
                    'can_purchase': True,
                    'score': score,
                    'min_required': min_score_required,
                    'message': "积分满足要求"
                }
                return True, result
            else:
                result = {
                    'can_purchase': False,
                    'score': score,
                    'min_required': min_score_required,
                    'message': f"积分不足，需要{min_score_required}分，当前只有{score}分"
                }
                return False, result
                
        except Exception as e:
            log_message(f"积分与商品集成验证失败: {str(e)}", "ERROR")
            return False, {"error": str(e)}


def main():
    """
    测试积分管理器功能（仅用于测试，需要配置有效的API信息）
    """
    # 测试配置
    test_config = {
        'api': {
            'appid': 'YOUR_APPID',  # 需要替换为实际的appid
            'appsecret': 'YOUR_SECRET',  # 需要替换为实际的appsecret
            'use_sandbox': False
        },
        'points': {
            'enabled': True,
            'request_interval': 1,
            'max_retries': 3,
            'timeout': 30
        }
    }
    
    print("积分管理器测试")
    print("注意：请先配置有效的API信息")
    print("如需实际测试，请修改test_config中的appid和appsecret")
    print("\n测试功能将执行实际的API调用")
    
    # 准备测试用的openid
    test_openids = [
        'oUser1',  # 测试用户1
        'oUser2',  # 测试用户2
        'oUser3'   # 测试用户3
    ]
    
    # 创建积分管理器
    score_manager = VipScoreManager(test_config)
    
    # 示例1：单用户积分查询
    print("\n=== 示例1：单用户积分查询 ===")
    print(f"查询用户{test_openids[0]}的积分")
    
    # 执行实际的API查询
    success, result_data = score_manager.get_vip_user_score(test_openids[0])
    print(f"查询成功: {success}")
    if success:
        print(f"用户ID: {result_data['openid']}")
        print(f"积分: {result_data['score']}")
        print(f"查询时间: {result_data['query_time']}")
        print(f"响应原始数据: {json.dumps(result_data['raw_response'], ensure_ascii=False, indent=2)}")
    else:
        print(f"查询失败: {result_data}")
    
    # 示例2：批量用户积分查询
    print("\n=== 示例2：批量用户积分查询 ===")
    print("查询多个用户的积分信息")
    
    # 执行实际的批量查询
    batch_results = score_manager.batch_get_vip_user_scores(test_openids)
    print(f"总计查询: {batch_results['total']}")
    print(f"成功查询: {batch_results['success']}")
    print(f"失败查询: {batch_results['failed']}")
    print(f"成功率: {batch_results['success_rate']}%")
    print(f"总耗时: {batch_results['duration']}秒")
    if batch_results['total_score'] is not None:
        print(f"总积分: {batch_results['total_score']}")
        print(f"平均积分: {batch_results['average_score']}")
    
    print("\n详细结果:")
    for detail in batch_results['details']:
        status = "成功" if detail['success'] else "失败"
        score_info = f"积分: {detail['score']}" if detail['success'] else f"错误: {detail['error']}"
        print(f"[{detail['index']}] 用户: {detail['openid']} - {status}, {score_info}, 查询时间: {detail['query_time']}")
    
    # 示例3：生成积分查询报告
    print("\n=== 示例3：生成积分查询报告 ===")
    report = score_manager.generate_score_report(batch_results)
    print(report)
    
    # 示例4：积分与商品集成验证
    print("\n=== 示例4：积分与商品集成验证 ===")
    test_product = {
        'title': '高级商品',
        'min_score_required': 450
    }
    success, result = score_manager.validate_integration_with_product(
        test_product, result_data if success else {}
    )
    print(f"验证结果: {success}")
    print(f"详细信息: {result}")
    
    # 示例5：保存查询结果
    print("\n=== 示例5：保存查询结果 ===")
    file_path = f"score_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_success = score_manager.save_score_results(batch_results, file_path)
    print(f"保存结果: {'成功' if save_success else '失败'}")
    if save_success:
        print(f"结果已保存至: {file_path}")


if __name__ == "__main__":
    main()
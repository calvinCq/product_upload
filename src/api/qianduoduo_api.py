#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
钱多多API客户端模块
负责与钱多多API进行交互，实现图片生成等功能
"""

import os
import sys
import time
import requests
import json
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入日志功能
from src.utils.logger import log_message


class QianduoDuoAPI:
    """
    钱多多API客户端类
    封装与钱多多API的所有交互操作
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化钱多多API客户端
        
        :param config: API配置字典，包含API密钥、基础URL等信息
        """
        # 从环境变量读取配置
        env_config = {
            'api_key': os.environ.get('QIANDUODUO_API_KEY', ''),
            'base_url': os.environ.get('QIANDUODUO_API_BASE_URL', 'https://api2.aigcbest.top'),
            'timeout': int(os.environ.get('QIANDUODUO_TIMEOUT', '30')),
            'image_model': os.environ.get('QIANDUODUO_IMAGE_MODEL', 'doubao-seedream-4-0-250828'),
            'text_model': os.environ.get('QIANDUODUO_TEXT_MODEL', 'DeepSeek-V3.1')
        }
        
        # 默认配置
        default_config = {
            'api_key': '',
            'api_secret': '',
            'base_url': 'https://api2.aigcbest.top',
            'timeout': 30,
            'retry_count': 3,
            'image_model': 'doubao-seedream-4-0-250828',  # 图片生成模型
            'text_model': 'DeepSeek-V3.1',  # 文案提取模型
            'model_name': 'doubao-seedream-4-0-250828',  # 保持向后兼容
            'image_endpoint': '/v1/images/generations',  # 与实际API端点对齐
            'image_params': {
                'width': 1024,
                'height': 1024,
                'steps': 30,
                'guidance_scale': 7.5,
                'negative_prompt': '模糊，扭曲，低质量，水印，签名'
            }
        }
        
        # 合并配置：默认配置 -> 环境变量配置 -> 用户传入配置
        self.config = {**default_config, **env_config, **(config or {})}
        
        # 验证必要配置
        if not self.config.get('api_key'):
            log_message("警告：钱多多API密钥未配置，部分功能可能受限", "WARNING")
        
        # 初始化session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.config.get('api_key', '')}"
        })
        
        log_message(f"钱多多API客户端初始化完成，使用图片模型: {self.config.get('image_model')}, 文案模型: {self.config.get('text_model')}")
    
    def _request(self, endpoint: str, method: str = 'POST', 
                data: Optional[Dict[str, Any]] = None,
                params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        通用API请求方法
        
        :param endpoint: API端点路径
        :param method: HTTP方法（GET或POST）
        :param data: 请求体数据
        :param params: URL查询参数
        :return: API响应数据字典，如果请求失败则返回None
        """
        url = urljoin(self.config['base_url'], endpoint)
        timeout = self.config.get('timeout', 30)
        retry_count = self.config.get('retry_count', 3)
        
        for attempt in range(retry_count):
            try:
                log_message(f"发送API请求到 {url}，尝试 {attempt + 1}/{retry_count}")
                
                if method.upper() == 'POST':
                    response = self.session.post(url, json=data, params=params, timeout=timeout)
                else:
                    response = self.session.get(url, params=params, timeout=timeout)
                
                # 检查响应状态
                response.raise_for_status()
                
                # 解析JSON响应
                result = response.json()
                
                # 检查业务状态
                if 'code' in result and result['code'] != 0:
                    error_msg = result.get('message', 'Unknown error')
                    log_message(f"API返回错误代码 {result['code']}: {error_msg}", "ERROR")
                    return None
                
                log_message(f"API请求成功，响应状态码: {response.status_code}")
                return result
                
            except requests.exceptions.RequestException as e:
                error_msg = f"API请求异常: {str(e)}"
                log_message(error_msg, "ERROR")
                
                # 最后一次尝试失败则返回None
                if attempt == retry_count - 1:
                    log_message(f"API请求失败，已达最大重试次数 {retry_count}", "ERROR")
                    return None
                
                # 重试前等待，使用指数退避策略
                wait_time = (2 ** attempt) * 0.5
                log_message(f"将在 {wait_time} 秒后重试...")
                time.sleep(wait_time)
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        """
        生成图片
        
        :param prompt: 图片生成提示词
        :param kwargs: 其他图片生成参数（覆盖默认配置）
        :return: 生成的图片URL，如果生成失败则返回None
        """
        log_message(f"开始生成图片，提示词: {prompt}")
        
        # 准备请求参数
        endpoint = self.config['image_endpoint']
        image_params = {**self.config['image_params'], **kwargs}
        
        # 创建请求数据
        request_data = {
            'prompt': prompt,
            'model': self.config.get('image_model', self.config.get('model_name', 'doubao-seedream-4-0-250828')),
            **image_params
        }
        
        # 发送请求
        response = self._request(endpoint, method='POST', data=request_data)
        
        if response:
            # 详细记录响应结构以便调试
            log_message(f"API响应结构: {list(response.keys())}")
            
            # 首先检查是否有data字段
            if 'data' in response:
                log_message(f"响应data字段结构: {list(response['data'].keys()) if isinstance(response['data'], dict) else type(response['data'])}")
                
                # 尝试多种可能的图片URL路径
                if isinstance(response['data'], dict):
                    # 主要路径
                    if 'image_url' in response['data']:
                        image_url = response['data']['image_url']
                        log_message(f"成功生成图片: {image_url}")
                        return image_url
                    # 可能的替代路径
                    elif 'url' in response['data']:
                        image_url = response['data']['url']
                        log_message(f"成功从url字段获取图片: {image_url}")
                        return image_url
                    elif 'images' in response['data'] and isinstance(response['data']['images'], list) and response['data']['images']:
                        if 'url' in response['data']['images'][0]:
                            image_url = response['data']['images'][0]['url']
                            log_message(f"成功从images数组获取图片: {image_url}")
                            return image_url
                # 如果data是列表且不为空
                elif isinstance(response['data'], list) and response['data']:
                    first_item = response['data'][0]
                    if isinstance(first_item, dict):
                        if 'image_url' in first_item:
                            image_url = first_item['image_url']
                            log_message(f"成功从data数组获取图片: {image_url}")
                            return image_url
                        elif 'url' in first_item:
                            image_url = first_item['url']
                            log_message(f"成功从data数组的url字段获取图片: {image_url}")
                            return image_url
            
            # 如果直接在响应中有image_url
            elif 'image_url' in response:
                image_url = response['image_url']
                log_message(f"成功从响应根级获取图片: {image_url}")
                return image_url
            
            # 记录完整响应以便调试
            log_message(f"API返回完整响应: {json.dumps(response, ensure_ascii=False)[:500]}...", "ERROR")
            log_message("API返回中未找到图片URL", "ERROR")
        
        return None
    
    def generate_images_batch(self, prompts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        批量生成图片
        
        :param prompts: 提示词列表
        :param kwargs: 其他图片生成参数
        :return: 生成结果列表，每项包含提示词和图片URL（如果成功）
        """
        log_message(f"开始批量生成 {len(prompts)} 张图片")
        results = []
        
        for i, prompt in enumerate(prompts):
            log_message(f"正在生成第 {i+1}/{len(prompts)} 张图片")
            image_url = self.generate_image(prompt, **kwargs)
            
            results.append({
                'prompt': prompt,
                'image_url': image_url,
                'success': image_url is not None
            })
            
            # 避免请求过于频繁
            if i < len(prompts) - 1:
                time.sleep(2)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        log_message(f"批量生成完成，成功 {success_count}/{len(prompts)} 张图片")
        
        return results
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        获取API状态信息
        
        :return: API状态信息字典
        """
        log_message("获取API状态信息")
        
        # 尝试发送简单请求检查API状态
        test_endpoint = '/status'  # 假设的状态端点，可能需要根据实际API调整
        response = self._request(test_endpoint, method='GET')
        
        if response:
            return response.get('data', {})
        
        # 如果状态检查失败，返回基本状态信息
        return {
            'status': 'unknown',
            'config_valid': bool(self.config.get('api_key')),
            'error': '无法连接到API服务器'
        }
    
    def close(self):
        """
        关闭会话，释放资源
        """
        self.session.close()
        log_message("钱多多API客户端会话已关闭")
    
    def __enter__(self):
        """
        支持上下文管理器
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器时关闭会话
        """
        self.close()


def test_qianduoduo_api():
    """
    测试钱多多API客户端功能
    """
    # 直接使用环境变量配置，不再指定覆盖配置
    api_client = QianduoDuoAPI()
    
    try:
        # 检查API状态
        status = api_client.get_api_status()
        print(f"API状态: {status}")
        
        # 生成测试图片
        if api_client.config['api_key']:
            test_prompt = "专业的Python课程封面，高清品质，现代设计风格，蓝色调"
            print(f"\n测试生成图片，提示词: {test_prompt}")
            print(f"使用模型: {api_client.config.get('image_model')}")
            image_url = api_client.generate_image(test_prompt)
            
            if image_url:
                print(f"成功生成图片: {image_url}")
            else:
                print("图片生成失败，可能API密钥无效或服务不可用")
        else:
            print("未配置API密钥，跳过图片生成测试")
            
    finally:
        # 关闭客户端
        api_client.close()


if __name__ == '__main__':
    # 运行测试
    test_qianduoduo_api()
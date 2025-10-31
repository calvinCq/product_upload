#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

# 直接打印环境变量状态，用于调试
print(f"[DEBUG] Current working directory: {os.getcwd()}")
print(f"[DEBUG] Does .env file exist: {os.path.exists('.env')}")

# 尝试从.env文件加载环境变量
api_key = None

# 1. 首先尝试从环境变量直接获取
api_key = os.environ.get("VOLCANO_API_KEY")
print(f"[DEBUG] API Key from os.environ: {'Exists' if api_key else 'None'}")

# 2. 尝试导入dotenv并加载
if not api_key:
    try:
        from dotenv import load_dotenv
        print("[DEBUG] Imported dotenv successfully")
        load_dotenv()
        print("[DEBUG] Called load_dotenv()")
        api_key = os.environ.get("VOLCANO_API_KEY")
        print(f"[DEBUG] API Key after load_dotenv: {'Exists' if api_key else 'None'}")
    except ImportError:
        print("[DEBUG] Error: python-dotenv not installed")

# 3. 尝试直接读取.env文件
if not api_key:
    try:
        print("[DEBUG] Trying to read .env file directly")
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('VOLCANO_API_KEY='):
                    api_key = line.strip().split('=', 1)[1].strip().strip('"')
                    print(f"[DEBUG] API Key from direct .env read: {'Exists' if api_key else 'None'}")
                    break
    except Exception as e:
        print(f"[DEBUG] Error reading .env file directly: {e}")

# 设置日志
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class VolcanoImageGenerator:
    """
    图片生成器 - 使用钱多多模型API
    负责调用API生成商品图片
    """
    
    def __init__(self, config=None):
        """
        初始化图片生成API客户端（仅使用钱多多API）
        
        Args:
            config: 配置对象（ConfigManager实例或配置字典）
        """
        self.logger = logging.getLogger('VolcanoImageGenerator')
        self.use_qianduoduo = True  # 强制使用钱多多API
        
        # 如果传入的是ConfigManager实例，获取钱多多API配置
        if hasattr(config, 'get_qianduoduo_api_config'):
            qianduoduo_config = config.get_qianduoduo_api_config()
            self.api_key = qianduoduo_config.get('api_key', '')
            self.api_base_url = qianduoduo_config.get('api_base_url', "https://api2.aigcbest.top")
            self.image_generation_endpoint = qianduoduo_config.get('image_generation_endpoint', "/v1/images/generations")
            self.timeout = qianduoduo_config.get('timeout', 60)
            self.retry_count = qianduoduo_config.get('retry_count', 3)
            self.retry_delay = qianduoduo_config.get('retry_delay', 3)
            self.main_images_count = qianduoduo_config.get('main_images_count', 3)
            self.detail_images_count = qianduoduo_config.get('detail_images_count', 2)
            self.image_save_dir = qianduoduo_config.get('image_save_dir', './temp_images')
        else:
            # 使用全局加载的api_key作为默认值
            global_api_key = globals().get('api_key')
            
            if config:
                self.api_key = config.get('api_key', global_api_key)
                if not self.api_key:
                    # 钱多多API默认密钥
                    self.api_key = "sk-T3PbJoofAo22v5CzDhrFUhlVuX3MmPdUTRTswa7phYdZ6Q5g"
                    # 尝试从环境变量覆盖
                    self.api_key = os.environ.get("QIANDUODUO_API_KEY", self.api_key)
                
                # 设置API基础URL和端点
                self.api_base_url = config.get('api_base_url', "https://api2.aigcbest.top")
                self.image_generation_endpoint = "/v1/images/generations"
                
                self.timeout = config.get('timeout', 60)
                self.retry_count = config.get('retry_count', 3)
                self.retry_delay = config.get('retry_delay', 3)
                self.main_images_count = config.get('main_images_count', 3)
                self.detail_images_count = config.get('detail_images_count', 2)
                self.image_save_dir = config.get('image_save_dir', './temp_images')
            else:
                # 钱多多API默认密钥
                self.api_key = "sk-T3PbJoofAo22v5CzDhrFUhlVuX3MmPdUTRTswa7phYdZ6Q5g"
                # 尝试从环境变量覆盖
                self.api_key = os.environ.get("QIANDUODUO_API_KEY", self.api_key)
                self.api_base_url = "https://api2.aigcbest.top"
                self.image_generation_endpoint = "/v1/images/generations"
                
                self.timeout = 60
                self.retry_count = 3
                self.retry_delay = 3
                self.main_images_count = 3
                self.detail_images_count = 2
                self.image_save_dir = './temp_images'
        
        self.logger.info("VolcanoImageGenerator initialized with API Key: {'Exists' if self.api_key else 'Missing'}")
            
        self.model_name = "doubao-seedream-4-0-250828"  # 使用最新模型
        # 初始化会话
        self.session = requests.Session()
        # 头部信息将在请求时根据API类型动态设置
        
        # 创建图片保存目录
        os.makedirs(self.image_save_dir, exist_ok=True)
    
    def generate_product_images(self, product_description: str, count: int = 3, 
                               image_type: str = "main", save_dir: str = None) -> List[str]:
        """
        生成商品图片
        
        Args:
            product_description: 商品描述文本或包含商品描述的文件路径
            count: 生成图片数量
            image_type: 图片类型 ("main" 或 "detail")
            save_dir: 图片保存目录，默认使用初始化时的配置
        
        Returns:
            生成的图片文件路径列表
        """
        # 使用指定的保存目录或默认目录
        if save_dir is None:
            save_dir = self.image_save_dir
            
        # 检查是否为文件路径，如果是则读取文件内容
        if os.path.isfile(product_description):
            try:
                with open(product_description, 'r', encoding='utf-8') as f:
                    product_description = f.read().strip()
                logger.info(f"已从文件中读取商品描述: {product_description[:50]}...")
            except Exception as e:
                logger.error(f"读取商品描述文件失败: {str(e)}")
                raise ValueError(f"无法读取商品描述文件: {str(e)}")
                
        if not self.api_key:
            raise ValueError("缺少火山大模型API密钥")
        
        if not product_description:
            raise ValueError("商品描述不能为空")
        os.makedirs(save_dir, exist_ok=True)
        
        generated_image_paths = []
        
        for i in range(count):
            try:
                # 构建提示词
                prompt = self._build_prompt(product_description, image_type)
                
                # 发送图片生成请求
                image_url = self._request_image_generation(prompt)
                
                # 保存图片
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{image_type}_{timestamp}_{i+1}.jpg"
                image_path = os.path.join(save_dir, image_filename)
                
                self._save_image_from_url(image_url, image_path)
                generated_image_paths.append(image_path)
                logger.info(f"成功生成{image_type}图片: {image_path}")
                
                # 避免请求过快
                if i < count - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"生成第{i+1}张{image_type}图片失败: {str(e)}")
                # 如果是最后一次尝试，则跳过
                if i == count - 1:
                    continue
        
        if not generated_image_paths:
            raise Exception(f"未能生成任何{image_type}图片")
        
        return generated_image_paths
    
    def _build_prompt(self, product_description: str, image_type: str) -> str:
        """
        构建提示词
        
        Args:
            product_description: 商品描述文本
            image_type: 图片类型 ("main" 或 "detail")
        
        Returns:
            构建好的提示词字符串
        """
        if image_type == "main":
            # 主图提示词模板
            template = """
            请生成一张高质量的商品主图，展示: {product_description}
            要求:
            - 产品居中，清晰可见
            - 专业的光线和阴影效果
            - 简洁干净的背景
            - 真实的产品质感
            - 适合电商平台的展示风格
            - 高分辨率，细节清晰
            - 无文字水印
            """
        else:  # detail
            # 详情图提示词模板
            template = """
            请生成一张商品细节展示图，展示: {product_description}的细节特点
            要求:
            - 展示商品的重要细节和功能特点
            - 清晰的产品纹理和材质
            - 适当的角度，突出产品特性
            - 专业的产品摄影风格
            - 高分辨率，细节丰富
            - 无文字水印
            """
        
        return template.format(product_description=product_description).strip()
    
    def _request_image_generation(self, prompt: str) -> str:
        """
        发送图片生成请求
        
        Args:
            prompt: 提示词
        
        Returns:
            图片URL
        """
        url = f"{self.api_base_url}{self.image_generation_endpoint}"
        
        # 根据API类型构建请求参数
        if self.use_qianduoduo:
            # 钱多多API参数格式
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",  # 钱多多API支持的常见尺寸
                "response_format": "url"
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:
            # 火山大模型API参数格式
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "size": "2K",  # 使用预定义尺寸
                "sequential_image_generation": "disabled",
                "stream": False,
                "response_format": "url",  # 请求返回图片URL
                "watermark": True
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        
        # 实现重试逻辑
        for attempt in range(self.retry_count):
            try:
                logger.info(f"发送图片生成请求 (尝试 {attempt + 1}/{self.retry_count})")
                logger.info(f"使用API: {'钱多多' if self.use_qianduoduo else '火山大模型'}")
                
                # 发送请求
                response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                
                # 打印响应内容前1000字符用于调试
                response_text = response.text[:1000]
                logger.info(f"响应内容前1000字符: {response_text}")
                
                # 解析响应
                result = response.json()
                logger.info(f"响应JSON解析成功，键: {list(result.keys())}")
                
                # 检查是否包含图片URL - 兼容两种API响应格式
                if "data" in result and isinstance(result["data"], list):
                    if len(result["data"]) > 0 and "url" in result["data"][0]:
                        image_url = result["data"][0]["url"]
                        logger.info(f"成功获取图片URL: {image_url}")
                        return image_url
                else:
                    raise Exception(f"响应中未找到有效的图片URL: {result}")
                    
            except requests.RequestException as e:
                logger.error(f"请求失败: {str(e)}")
                if attempt < self.retry_count - 1:
                    wait_time = self.retry_delay
                    logger.info(f"{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"图片生成请求失败: {str(e)}")
            except Exception as e:
                logger.error(f"图片生成失败: {str(e)}")
                if attempt < self.retry_count - 1:
                    wait_time = self.retry_delay
                    logger.info(f"{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise
    
    def _save_image_from_url(self, image_url: str, image_path: str) -> None:
        """
        从URL下载图片并保存到文件
        
        Args:
            image_url: 图片URL
            image_path: 保存路径
        """
        try:
            # 下载图片
            logger.info(f"开始下载图片: {image_url}")
            response = requests.get(image_url, timeout=self.timeout)
            response.raise_for_status()
            
            # 获取图片数据
            image_data = response.content
            logger.info(f"图片下载完成，大小: {len(image_data) / 1024:.2f} KB")
            
            # 保存图片
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
        except Exception as e:
            logger.error(f"保存图片失败: {str(e)}")
            raise
    
    def _save_image(self, image_data: bytes, image_path: str) -> None:
        """
        保存图片数据到文件
        
        Args:
            image_data: 图片二进制数据
            image_path: 保存路径
        """
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        # 检查文件大小是否符合要求
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if file_size_mb > 1:
            logger.warning(f"图片大小 {file_size_mb:.2f}MB 超过了1MB的限制")


def main():
    """
    测试图片生成功能 - 默认使用钱多多API
    """
    # 创建生成器实例 - 默认使用钱多多API
    # 钱多多API密钥已在类中内置
    generator = VolcanoImageGenerator(use_qianduoduo=True)
    print("使用钱多多API进行图片生成测试...")
    
    # 测试生成商品主图
    product_description = "一款时尚的智能手机，黑色机身，全面屏设计，高清摄像头"
    try:
        print(f"生成商品图片: {product_description}")
        main_images = generator.generate_product_images(
            product_description=product_description,
            count=1,
            image_type="main",
            save_dir="./test_images"
        )
        print(f"成功生成主图: {main_images}")
        
        # 测试生成详情图
        detail_images = generator.generate_product_images(
            product_description=product_description,
            count=1,
            image_type="detail",
            save_dir="./test_images"
        )
        print(f"成功生成详情图: {detail_images}")
        
    except Exception as e:
        print(f"错误: {str(e)}")


if __name__ == "__main__":
    main()
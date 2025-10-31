#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import requests
import json
from typing import Dict, Any, Optional
import logging
from config_manager import ConfigManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class VolcanoTextGenerator:
    """
    文本生成器 - 仅使用钱多多模型API
    负责调用API进行文本信息提取和生成
    """
    
    def __init__(self, config_file=None, use_qianduoduo: bool = True):
        """
        初始化文本生成器（仅使用钱多多API）
        
        Args:
            config_file: 配置文件路径
            use_qianduoduo: 是否使用钱多多API（默认True，必须使用）
        """
        self.use_qianduoduo = True  # 强制使用钱多多API
        self.logger = logging.getLogger('VolcanoTextGenerator')
        
        # 初始化配置管理器
        self.config_manager = ConfigManager(config_file)
        if config_file and os.path.exists(config_file):
            self.config_manager.load_config()
        else:
            # 使用默认配置文件或空配置
            default_config = 'product_generator_config.json'
            if os.path.exists(default_config):
                self.config_manager = ConfigManager(default_config)
                self.config_manager.load_config()
            else:
                # 如果没有配置文件，创建一个空的配置管理器
                self.config_manager = ConfigManager('')
        
        # 获取钱多多API配置
        qianduoduo_config = self.config_manager.get_qianduoduo_api_config()
        self.api_key = qianduoduo_config.get('api_key', '')
        self.api_base_url = qianduoduo_config.get('api_base_url', '')
        self.endpoint = qianduoduo_config.get('text_generation_endpoint', '/v1/chat/completions')
        self.model_name = qianduoduo_config.get('model_name', 'DeepSeek-V3.1')
        
        # 设置默认值
        self.timeout = qianduoduo_config.get('timeout', 60)
        self.max_retries = qianduoduo_config.get('retry_count', 3)
        self.retry_delay = qianduoduo_config.get('retry_delay', 3)
        
        # 钱多多API固定配置
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.logger.info(f"TextGenerator initialized with API Key: {'Exists' if self.api_key else 'Missing'}")
        self.logger.info(f"使用钱多多API模型: {self.model_name}")
        
        self.session = requests.Session()
    
    def extract_content_info(self, document_content: str) -> Dict[str, Any]:
        """
        从内容中提取结构化信息（使用钱多多API的DeepSeek-V3.1模型）
        
        Args:
            document_content: 输入的文本内容
            
        Returns:
            提取的结构化信息字典
        """
        if not self.api_key:
            raise ValueError("缺少钱多多API密钥")
        
        if not document_content:
            raise ValueError("文档内容不能为空")
        
        # 构建提取课程信息的提示词
        prompt = self._build_extraction_prompt(document_content)
        
        # 调用钱多多API生成响应
        response_text = self.generate_text(prompt)
        self.logger.info("成功获取钱多多API响应")
        
        # 解析响应
        extracted_info = self._parse_extracted_info(response_text)
        self.logger.info(f"成功提取结构化信息: {extracted_info.get('course_name', '')}")
        
        return extracted_info
    
    def _build_extraction_prompt(self, document_content: str) -> str:
        """
        构建信息提取提示词
        
        Args:
            document_content: 文档内容
        
        Returns:
            构建好的提示词字符串
        """
        template = """
        请从以下文档内容中提取关键信息，以JSON格式返回：
        
        文档内容：
        {document_content}
        
        请提取以下字段：
        1. course_name: 课程名称
        2. teacher_name: 老师姓名
        3. teacher_title: 老师职称或职位
        4. teacher_company: 老师所在公司
        5. teacher_bio: 老师简介
        6. course_description: 课程描述
        7. course_outline: 课程大纲（数组格式）
        8. target_audience: 适用人群（数组格式）
        9. learning_outcomes: 学习成果（数组格式）
        10. course_features: 课程特色（数组格式）
        
        请严格按照JSON格式返回，不要包含任何其他文本。如果某个字段在文档中未找到，请设置为空字符串或空数组。
        """
        
        return template.format(document_content=document_content)
    
    def generate_text(self, prompt: str) -> str:
        """
        生成文本（使用钱多多API的DeepSeek-V3.1模型）
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的文本
        """
        url = f"{self.api_base_url}{self.endpoint}"
        
        # 构建钱多多API请求数据
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "你是一位专业的文档解析专家。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2048,
            "temperature": 0.7
        }
        
        # 重试逻辑
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"正在调用钱多多API，尝试次数: {attempt + 1}")
                response = self.session.post(
                    url, 
                    headers=self.headers, 
                    json=data, 
                    timeout=self.timeout
                )
                
                # 检查响应状态
                response.raise_for_status()
                
                # 解析响应
                result = response.json()
                
                # 钱多多API响应格式
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    return content
                else:
                    raise ValueError(f"Invalid API response format: {result}")
                    
            except Exception as e:
                self.logger.error(f"钱多多API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    self.logger.info(f"将在 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # 指数退避
                else:
                    self.logger.error("达到最大重试次数，请求失败")
                    raise
    
    def _parse_extracted_info(self, extracted_text: str) -> Dict[str, Any]:
        """
        解析从大模型提取的信息
        
        Args:
            extracted_text: 大模型返回的文本
        
        Returns:
            解析后的信息字典
        """
        try:
            # 清理文本，确保是纯JSON格式
            # 移除可能的前后文本
            if "```json" in extracted_text:
                extracted_text = extracted_text.split("```json")[1]
            if "```" in extracted_text:
                extracted_text = extracted_text.split("```")[0]
            
            # 解析JSON
            info = json.loads(extracted_text.strip())
            
            # 标准化返回的数据结构
            standard_info = {
                "course_name": info.get("course_name", ""),
                "teacher": {
                    "name": info.get("teacher_name", ""),
                    "title": info.get("teacher_title", ""),
                    "company": info.get("teacher_company", ""),
                    "bio": info.get("teacher_bio", "")
                },
                "description": info.get("course_description", ""),
                "outline": info.get("course_outline", []),
                "target_audience": info.get("target_audience", []),
                "learning_outcomes": info.get("learning_outcomes", []),
                "features": info.get("course_features", [])
            }
            
            return standard_info
        except Exception as e:
            logger.error(f"解析提取的信息失败: {str(e)}")
            # 如果解析失败，尝试使用默认结构
            return {
                "course_name": "",
                "teacher": {
                    "name": "",
                    "title": "",
                    "company": "",
                    "bio": ""
                },
                "description": "",
                "outline": [],
                "target_audience": [],
                "learning_outcomes": [],
                "features": []
            }


def main():
    """
    测试文本生成功能 - 默认使用钱多多API
    """
    # 创建生成器实例 - 默认使用钱多多API
    # 钱多多API密钥已在类中内置
    generator = VolcanoTextGenerator(use_qianduoduo=True)
    print("使用钱多多API进行文本生成测试...")
    
    # 测试文档内容
    test_document = """
    洪总亲授：30 分钟解锁大健康行业前沿观察，开启认知升级之路
    
    讲师介绍：
    洪总，资深投资人，专注于合成生物科技领域的投资与研究，拥有10年以上行业经验，曾主导多个成功的投资案例。
    
    课程大纲：
    1. 行业变革观察：大健康产业现状与未来趋势
    2. 前沿科技解读：合成生物技术在医疗健康领域的应用
    3. 投资机会分析：如何识别大健康领域的优质项目
    4. 实战案例分享：成功投资案例剖析
    
    适用人群：
    - 大健康领域的创业者和企业家
    - 对合成生物技术感兴趣的投资人
    - 医疗健康行业的从业者
    - 希望了解行业发展趋势的相关人士
    
    学完收获：
    - 深入了解大健康行业的发展趋势和市场前景
    - 掌握合成生物技术的基础知识和应用场景
    - 学习如何评估大健康领域的投资机会
    - 获取实用的行业洞察和投资策略
    """
    
    try:
        print("正在提取文档信息...")
        extracted_info = generator.extract_content_info(test_document)
        print("信息提取成功！")
        print(json.dumps(extracted_info, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {str(e)}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户资料管理器模块

负责处理和验证客户输入的资料，确保输入数据的完整性和有效性。
"""

import json
from typing import Dict, Any, List, Optional


class ClientDataError(Exception):
    """
    客户资料错误异常
    
    当客户资料格式不正确或不完整时抛出
    """
    pass


class ClientDataManager:
    """
    客户资料管理器类
    
    用于验证和处理客户提供的资料，提取关键信息用于生成商品详情。
    """
    
    def __init__(self):
        """
        初始化客户资料管理器
        """
        # 定义必需的字段
        self.required_fields = [
            'course_name',
            'teacher_info',
            'course_content',
            'target_audience',
            'learning_outcomes'
        ]
        
        # 定义老师信息必需的字段
        self.teacher_info_required_fields = [
            'name',
            'title',
            'experience',
            'background'
        ]
    
    def validate_client_data(self, client_data: Dict[str, Any]) -> bool:
        """
        验证客户资料的完整性和格式
        
        Args:
            client_data: 客户资料字典
            
        Returns:
            True if 客户资料有效，否则 False
            
        Raises:
            ClientDataError: 当客户资料无效时
        """
        if not isinstance(client_data, dict):
            raise ClientDataError("客户资料必须是字典格式")
        
        # 检查必需字段是否存在
        missing_fields = []
        for field in self.required_fields:
            if field not in client_data or not client_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ClientDataError(f"缺少必需字段: {', '.join(missing_fields)}")
        
        # 检查老师信息
        teacher_info = client_data.get('teacher_info')
        if not isinstance(teacher_info, dict):
            raise ClientDataError("老师信息必须是字典格式")
        
        # 检查老师信息的必需字段
        teacher_missing_fields = []
        for field in self.teacher_info_required_fields:
            if field not in teacher_info or not teacher_info[field]:
                teacher_missing_fields.append(field)
        
        if teacher_missing_fields:
            raise ClientDataError(f"老师信息缺少必需字段: {', '.join(teacher_missing_fields)}")
        
        # 可选字段验证：课程特色
        if 'course_features' in client_data and client_data['course_features']:
            if not isinstance(client_data['course_features'], list):
                raise ClientDataError("课程特色必须是列表格式")
        
        return True
    
    def process_client_data(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理客户资料，提取关键信息并标准化
        
        Args:
            client_data: 原始客户资料
            
        Returns:
            处理后的客户资料
            
        Raises:
            ClientDataError: 当客户资料无效时
        """
        # 首先验证客户资料
        self.validate_client_data(client_data)
        
        # 创建处理后的资料副本
        processed_data = client_data.copy()
        
        # 标准化课程名称
        processed_data['course_name'] = self._standardize_text(
            client_data['course_name']
        )
        
        # 标准化老师信息
        if 'teacher_info' in client_data:
            teacher_info = client_data['teacher_info'].copy()
            teacher_info['name'] = self._standardize_text(teacher_info['name'])
            teacher_info['title'] = self._standardize_text(teacher_info['title'])
            teacher_info['experience'] = self._standardize_text(teacher_info['experience'])
            teacher_info['background'] = self._standardize_text(teacher_info['background'])
            processed_data['teacher_info'] = teacher_info
        
        # 标准化课程内容
        processed_data['course_content'] = self._standardize_text(
            client_data['course_content']
        )
        
        # 标准化目标受众
        processed_data['target_audience'] = self._standardize_text(
            client_data['target_audience']
        )
        
        # 标准化学习成果
        processed_data['learning_outcomes'] = self._standardize_text(
            client_data['learning_outcomes']
        )
        
        # 标准化课程特色
        if 'course_features' in client_data and client_data['course_features']:
            processed_data['course_features'] = [
                self._standardize_text(feature) for feature in client_data['course_features']
            ]
        else:
            processed_data['course_features'] = []
        
        # 添加额外的处理信息
        processed_data['processed'] = True
        processed_data['extracted_keywords'] = self._extract_keywords(processed_data)
        
        return processed_data
    
    def _standardize_text(self, text: str) -> str:
        """
        标准化文本，去除多余空格和特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            标准化后的文本
        """
        if not isinstance(text, str):
            text = str(text)
        
        # 去除首尾空格
        text = text.strip()
        
        # 替换连续的空格为单个空格
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # 移除多余的标点符号（可选）
        # text = re.sub(r'[\s\u3000]+', ' ', text)
        
        return text
    
    def _extract_keywords(self, processed_data: Dict[str, Any]) -> List[str]:
        """
        从处理后的客户资料中提取关键词
        
        Args:
            processed_data: 处理后的客户资料
            
        Returns:
            关键词列表
        """
        keywords = []
        
        # 从课程名称提取关键词
        course_name = processed_data.get('course_name', '')
        if course_name:
            # 简单的关键词提取，实际应用中可使用更复杂的算法
            name_parts = course_name.split()
            keywords.extend(name_parts[:3])  # 取前3个部分
        
        # 从课程内容提取关键词（简化版）
        course_content = processed_data.get('course_content', '')
        if course_content:
            # 简单的关键词提取，这里仅作为示例
            # 实际应用中可以使用NLP技术进行关键词提取
            content_words = set(course_content.split()[:10])  # 取前10个词并去重
            keywords.extend(list(content_words)[:3])  # 再取前3个
        
        # 从课程特色中提取
        course_features = processed_data.get('course_features', [])
        if course_features:
            # 从每个特色中提取第一个词
            for feature in course_features[:2]:  # 取前2个特色
                if feature:
                    feature_words = feature.split()
                    if feature_words:
                        keywords.append(feature_words[0])
        
        # 去重并限制数量
        keywords = list(dict.fromkeys(keywords))  # 保持顺序去重
        return keywords[:8]  # 最多返回8个关键词
    
    def generate_client_data_template(self) -> Dict[str, Any]:
        """
        生成客户资料模板
        
        Returns:
            客户资料模板字典
        """
        template = {
            'course_name': '课程名称',
            'teacher_info': {
                'name': '老师姓名',
                'title': '职称/职位',
                'experience': '教学经验描述',
                'background': '教育背景描述'
            },
            'course_content': '课程主要内容描述',
            'target_audience': '目标受众描述',
            'learning_outcomes': '预期学习成果描述',
            'course_features': ['特色1', '特色2', '特色3']
        }
        return template
    
    def save_client_data(self, client_data: Dict[str, Any], file_path: str) -> None:
        """
        保存客户资料到文件
        
        Args:
            client_data: 客户资料
            file_path: 文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(client_data, f, ensure_ascii=False, indent=2)
    
    def load_client_data(self, file_path: str) -> Dict[str, Any]:
        """
        从文件加载客户资料
        
        Args:
            file_path: 文件路径
            
        Returns:
            客户资料字典
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)


# 测试代码
if __name__ == "__main__":
    # 创建客户资料管理器实例
    manager = ClientDataManager()
    
    # 生成并打印模板
    print("客户资料模板:")
    print(json.dumps(manager.generate_client_data_template(), ensure_ascii=False, indent=2))
    print("\n" + "="*50 + "\n")
    
    # 创建测试数据
    test_data = {
        'course_name': 'Python编程入门到精通',
        'teacher_info': {
            'name': '张教授',
            'title': '高级软件工程师',
            'experience': '10年Python教学经验',
            'background': '计算机科学博士'
        },
        'course_content': '本课程从零基础开始，全面讲解Python编程基础、数据结构、算法、Web开发等内容。',
        'target_audience': '对编程感兴趣的零基础学员，希望转行IT行业的在职人士。',
        'learning_outcomes': '掌握Python基础语法，能够编写实用的Python程序，理解软件开发流程。',
        'course_features': ['零基础友好', '实战项目丰富', '就业指导']
    }
    
    try:
        # 验证客户资料
        is_valid = manager.validate_client_data(test_data)
        print(f"验证结果: {'通过' if is_valid else '失败'}")
        
        # 处理客户资料
        processed_data = manager.process_client_data(test_data)
        print("\n处理后的客户资料:")
        print(json.dumps(processed_data, ensure_ascii=False, indent=2))
        
    except ClientDataError as e:
        print(f"验证错误: {e}")
    
    # 测试无效数据
    invalid_data = {
        'course_name': 'Java编程课程',
        # 缺少teacher_info
        'course_content': '学习Java编程',
        'target_audience': '编程爱好者'
        # 缺少learning_outcomes
    }
    
    print("\n" + "="*50 + "\n")
    print("测试无效数据:")
    try:
        manager.validate_client_data(invalid_data)
    except ClientDataError as e:
        print(f"验证错误: {e}")
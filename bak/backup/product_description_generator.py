#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品详情生成器模块

负责根据客户资料生成符合微信小店教育培训类目规则的商品详情页文案。
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from client_data_manager import ClientDataManager
from sensitive_word_filter import SensitiveWordFilter


class ProductDescriptionError(Exception):
    """
    商品详情生成错误异常
    
    当商品详情生成过程中出现错误时抛出
    """
    pass


class ProductDescriptionGenerator:
    """
    商品详情生成器类
    
    根据客户资料生成包含五个部分的教育培训类商品详情页文案。
    """
    
    def __init__(self):
        """
        初始化商品详情生成器
        """
        # 初始化客户资料管理器和敏感词过滤器
        self.client_data_manager = ClientDataManager()
        self.sensitive_word_filter = SensitiveWordFilter()
        
        # 详情页五个部分的标题
        self.section_titles = {
            'title': '【课程名称】',
            'teacher': '【老师简介】',
            'content': '【课程大纲】',
            'audience': '【适用人群】',
            'outcomes': '【学完收获】'
        }
    
    def generate_product_description(self, client_data: Dict[str, Any]) -> Dict[str, str]:
        """
        生成完整的商品详情页文案
        
        Args:
            client_data: 客户资料
            
        Returns:
            包含五个部分的商品详情字典
        """
        try:
            # 处理客户资料
            processed_data = self.client_data_manager.process_client_data(client_data)
            
            # 生成各个部分的文案
            description = {
                'title': self._generate_title(processed_data),
                'teacher': self._generate_teacher_section(processed_data),
                'content': self._generate_content_section(processed_data),
                'audience': self._generate_audience_section(processed_data),
                'outcomes': self._generate_outcomes_section(processed_data)
            }
            
            # 过滤敏感词
            filtered_description = {}
            for section, text in description.items():
                filtered_description[section] = self.sensitive_word_filter.filter_text(text)
            
            return filtered_description
            
        except Exception as e:
            raise ProductDescriptionError(f"生成商品详情失败: {str(e)}")
    
    def _generate_title(self, processed_data: Dict[str, Any]) -> str:
        """
        生成课程标题部分
        
        Args:
            processed_data: 处理后的客户资料
            
        Returns:
            标题部分文案
        """
        course_name = processed_data.get('course_name', '')
        keywords = processed_data.get('extracted_keywords', [])
        
        # 构建标题部分
        title_section = f"{self.section_titles['title']}{course_name}\n\n"
        
        # 如果有课程特色，添加到标题部分
        course_features = processed_data.get('course_features', [])
        if course_features:
            title_section += "课程特色：\n"
            for i, feature in enumerate(course_features, 1):
                title_section += f"• {feature}\n"
            title_section += "\n"
        
        # 添加课程关键词
        if keywords:
            title_section += f"关键词：{', '.join(keywords[:5])}\n"
        
        return title_section.strip()
    
    def _generate_teacher_section(self, processed_data: Dict[str, Any]) -> str:
        """
        生成老师简介部分
        
        Args:
            processed_data: 处理后的客户资料
            
        Returns:
            老师简介部分文案
        """
        teacher_info = processed_data.get('teacher_info', {})
        
        teacher_section = f"{self.section_titles['teacher']}\n"
        teacher_section += f"姓名：{teacher_info.get('name', '未知')}\n"
        teacher_section += f"职称：{teacher_info.get('title', '未知')}\n"
        teacher_section += f"教学经验：{teacher_info.get('experience', '未知')}\n"
        teacher_section += f"教育背景：{teacher_info.get('background', '未知')}\n"
        
        return teacher_section.strip()
    
    def _generate_content_section(self, processed_data: Dict[str, Any]) -> str:
        """
        生成课程大纲部分
        
        Args:
            processed_data: 处理后的客户资料
            
        Returns:
            课程大纲部分文案
        """
        course_content = processed_data.get('course_content', '')
        
        content_section = f"{self.section_titles['content']}\n\n"
        
        # 将课程内容拆分为要点并格式化
        # 这里使用简单的处理，实际应用中可以根据具体格式进行更复杂的解析
        if course_content:
            # 检查是否已经包含列表标记
            if any(marker in course_content for marker in ['•', '1.', '一、']):
                content_section += course_content
            else:
                # 如果没有列表标记，尝试分段并添加项目符号
                paragraphs = course_content.split('。')
                for i, para in enumerate(paragraphs, 1):
                    para = para.strip()
                    if para:
                        content_section += f"{i}. {para}。\n"
        else:
            content_section += "详细课程大纲将在课程开始前提供。"
        
        return content_section.strip()
    
    def _generate_audience_section(self, processed_data: Dict[str, Any]) -> str:
        """
        生成适用人群部分
        
        Args:
            processed_data: 处理后的客户资料
            
        Returns:
            适用人群部分文案
        """
        target_audience = processed_data.get('target_audience', '')
        
        audience_section = f"{self.section_titles['audience']}\n\n"
        
        if target_audience:
            # 将目标受众拆分为要点
            audience_points = self._split_into_points(target_audience)
            for point in audience_points:
                audience_section += f"• {point}\n"
        else:
            audience_section += "本课程面向对相关领域感兴趣的所有学习者。"
        
        return audience_section.strip()
    
    def _generate_outcomes_section(self, processed_data: Dict[str, Any]) -> str:
        """
        生成学完收获部分
        
        Args:
            processed_data: 处理后的客户资料
            
        Returns:
            学完收获部分文案
        """
        learning_outcomes = processed_data.get('learning_outcomes', '')
        
        outcomes_section = f"{self.section_titles['outcomes']}\n\n"
        
        if learning_outcomes:
            # 将学习成果拆分为要点
            outcome_points = self._split_into_points(learning_outcomes)
            for point in outcome_points:
                outcomes_section += f"• {point}\n"
        else:
            outcomes_section += "完成本课程后，学员将掌握相关领域的核心知识和技能。"
        
        return outcomes_section.strip()
    
    def _split_into_points(self, text: str) -> List[str]:
        """
        将文本拆分为要点列表
        
        Args:
            text: 原始文本
            
        Returns:
            要点列表
        """
        # 简单的拆分逻辑，可以根据实际需求调整
        points = []
        
        # 尝试根据标点符号拆分
        for delimiter in ['。', '；', ';', '，', ',']:
            if delimiter in text:
                parts = text.split(delimiter)
                # 确保每个部分都不为空
                points = [part.strip() for part in parts if part.strip()]
                if len(points) > 1:
                    break
        
        # 如果没有成功拆分，将整个文本作为一个要点
        if not points or len(points) == 1 and not points[0]:
            points = [text.strip()]
        
        return points[:5]  # 最多返回5个要点
    
    def generate_full_description_text(self, description_parts: Dict[str, str]) -> str:
        """
        将各部分详情组合成完整的文本
        
        Args:
            description_parts: 各部分详情字典
            
        Returns:
            完整的详情文本
        """
        sections = [
            description_parts.get('title', ''),
            description_parts.get('teacher', ''),
            description_parts.get('content', ''),
            description_parts.get('audience', ''),
            description_parts.get('outcomes', '')
        ]
        
        # 使用换行符连接各部分，并在部分之间添加分隔
        return '\n\n' + '\n\n'.join(section for section in sections if section)
    
    def format_for_wechat_shop(self, description_parts: Dict[str, str]) -> str:
        """
        格式化详情页文案以适应微信小店
        
        Args:
            description_parts: 各部分详情字典
            
        Returns:
            格式化后的文案
        """
        # 生成完整文本
        full_text = self.generate_full_description_text(description_parts)
        
        # 添加微信小店要求的格式
        formatted_text = f"<div class='product-description'>\n{full_text}\n</div>"
        
        # 添加生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_text += f"\n\n*文案生成时间: {timestamp}*"
        
        return formatted_text
    
    def validate_description(self, description_parts: Dict[str, str]) -> bool:
        """
        验证生成的详情文案是否符合要求
        
        Args:
            description_parts: 各部分详情字典
            
        Returns:
            是否符合要求
        """
        # 检查所有必需部分是否存在
        required_sections = ['title', 'teacher', 'content', 'audience', 'outcomes']
        for section in required_sections:
            if section not in description_parts or not description_parts[section]:
                return False
        
        # 检查是否包含敏感词
        for section, text in description_parts.items():
            if self.sensitive_word_filter.contains_sensitive(text):
                return False
        
        # 检查内容长度是否合适
        full_text = self.generate_full_description_text(description_parts)
        if len(full_text) < 100 or len(full_text) > 5000:
            return False
        
        return True


# 测试代码
if __name__ == "__main__":
    # 创建商品详情生成器实例
    generator = ProductDescriptionGenerator()
    
    # 测试数据
    test_client_data = {
        'course_name': 'Python数据分析与可视化实战',
        'teacher_info': {
            'name': '李教授',
            'title': '数据科学专家',
            'experience': '8年数据分析教学经验，曾在多家科技公司担任数据分析师',
            'background': '统计学博士，专注于机器学习和数据挖掘领域'
        },
        'course_content': '本课程分为四个模块：Python基础、NumPy与Pandas数据处理、Matplotlib与Seaborn数据可视化、实战项目。学员将学习如何使用Python进行数据清洗、转换、分析和可视化，掌握数据驱动决策的核心技能。',
        'target_audience': '对数据分析感兴趣的初学者和进阶学习者，希望提升数据处理能力的职场人士，需要进行数据可视化的研究人员。',
        'learning_outcomes': '掌握Python数据分析库的使用方法，能够独立完成数据清洗和预处理，熟练运用多种图表展示数据，具备解决实际业务问题的能力。',
        'course_features': ['零基础入门', '实战项目驱动', '就业技能培养', '终身学习支持']
    }
    
    try:
        # 生成商品详情
        description = generator.generate_product_description(test_client_data)
        
        # 打印生成的各部分详情
        print("生成的商品详情页文案:")
        print("=" * 60)
        
        for section_name, section_title in generator.section_titles.items():
            if section_name in description:
                print(f"\n【{section_name.upper()}】")
                print(description[section_name])
                print("-" * 40)
        
        # 生成完整的格式化文案
        formatted_text = generator.format_for_wechat_shop(description)
        print("\n【完整格式化文案】")
        print(formatted_text)
        
        # 验证文案
        is_valid = generator.validate_description(description)
        print(f"\n文案验证结果: {'通过' if is_valid else '不通过'}")
        
    except ProductDescriptionError as e:
        print(f"生成错误: {e}")
    except Exception as e:
        print(f"发生意外错误: {e}")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成整合器模块

负责整合客户资料处理、商品详情生成和图片生成功能，提供统一的接口。
"""

from typing import Dict, Any, List, Tuple
import os
import json
import traceback
import logging
from datetime import datetime
from config_manager import ConfigManager

from client_data_manager import ClientDataManager
from product_description_generator import ProductDescriptionGenerator
# 导入之前的火山图片生成器
from volcano_image_generator import VolcanoImageGenerator


class ImageGenerationIntegratorError(Exception):
    """
    图片生成整合器错误异常
    """
    pass


class ImageGenerationIntegrator:
    """
    图片生成整合器类
    
    整合客户资料处理、商品详情生成和图片生成功能，提供完整的商品创建流程。
    """
    
    def __init__(self, config_file=None, config: Dict[str, Any] = None):
        """
        初始化图片生成整合器
        
        Args:
            config_file: 配置文件路径
            config: 配置字典
        """
        # 初始化日志记录器
        self.logger = logging.getLogger('generate_educational_product')
        
        # 初始化配置管理器
        if config_file and os.path.exists(config_file):
            self.config_manager = ConfigManager(config_file)
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
        
        # 设置默认配置并合并传入的配置
        self.config = config or {}
        # 从ConfigManager获取的配置优先级高于传入的config字典
        if qianduoduo_config:
            self.config.update(qianduoduo_config)
        
        # 确保API密钥设置正确
        if 'api_key' not in self.config:
            self.config['api_key'] = 'sk-T3PbJoofAo22v5CzDhrFUhlVuX3MmPdUTRTswa7phYdZ6Q5g'  # 内置默认密钥
        
        # 初始化各个组件
        self.client_data_manager = ClientDataManager()
        self.product_description_generator = ProductDescriptionGenerator()
        self.volcano_image_generator = VolcanoImageGenerator(config=self.config)
        self.logger.info("图片生成器初始化完成，使用钱多多API")
        
        # 设置输出目录
        self.output_dir = self.config.get('output_dir', './output')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 设置图片数量配置
        self.main_images_count = self.config.get('main_images_count', 3)
        self.detail_images_count = self.config.get('detail_images_count', 2)
    
    def process_client_request(self, client_data: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """
        处理完整的客户请求
        
        包括：验证客户资料、生成商品详情、生成主图和详情页图片
        
        Args:
            client_data: 客户资料
            progress_callback: 进度回调函数，接收两个参数：阶段名称和进度百分比(0-100)
            
        Returns:
            包含所有生成内容的结果字典
        """
        try:
            # 记录开始时间
            start_time = datetime.now()
            
            # 进度回调函数包装器
            def update_progress(phase, progress):
                if progress_callback:
                    progress_callback(phase, progress)
            
            # 1. 处理客户资料
            update_progress("验证客户资料", 10)
            processed_data = self.client_data_manager.process_client_data(client_data)
            
            # 2. 生成商品详情
            update_progress("生成商品详情", 30)
            description_parts = self.product_description_generator.generate_product_description(processed_data)
            
            # 生成主图
            update_progress("生成主图", 50)
            main_images = []
            try:
                main_images = self._generate_main_images(processed_data)
                self.logger.info(f"成功生成{len(main_images)}张主图")
            except Exception as e:
                self.logger.error(f"主图生成失败: {str(e)}")
                self.logger.error(traceback.format_exc())
            update_progress("生成主图", 70)
            
            # 生成详情页图片
            update_progress("生成详情页图片", 80)
            detail_images = []
            try:
                detail_images = self._generate_detail_images(description_parts)
                self.logger.info(f"成功生成{len(detail_images)}张详情页图片")
            except Exception as e:
                self.logger.error(f"详情页图片生成失败: {str(e)}")
                self.logger.error(traceback.format_exc())
            update_progress("生成详情页图片", 90)
            
            # 计算总耗时
            total_time = (datetime.now() - start_time).total_seconds()
            
            # 构建结果字典
            result = {
                'timestamp': datetime.now().isoformat(),
                'total_time_seconds': round(total_time, 2),
                'processed_client_data': processed_data,
                'product_description': description_parts,
                'full_description_text': self.product_description_generator.generate_full_description_text(description_parts),
                'main_images': main_images,
                'detail_images': detail_images,
                'title': description_parts.get('title', '').split('】')[-1].strip(),
                'validation_result': {
                    'description_valid': self.product_description_generator.validate_description(description_parts),
                    'main_images_count': len(main_images),
                    'detail_images_count': len(detail_images),
                    'images_valid': all(os.path.exists(img) and os.path.getsize(img) > 0 for img in main_images + detail_images)
                }
            }
            
            # 保存结果到文件
            self._save_result(result)
            
            update_progress("完成", 100)
            return result
            
        except Exception as e:
            if progress_callback:
                progress_callback("错误", -1)
            raise ImageGenerationIntegratorError(f"处理客户请求失败: {str(e)}")
    
    def _generate_main_images(self, processed_data: Dict[str, Any]) -> List[str]:
        """
        生成主图
        
        Args:
            processed_data: 处理后的客户资料
            
        Returns:
            生成的主图文件路径列表
        """
        print("[DEBUG] _generate_main_images called")
        self.logger.info("开始生成主图")
        
        try:
            # 从客户资料构建提示词
            course_name = processed_data.get('course_name', '')
            keywords = processed_data.get('extracted_keywords', [])
            course_features = processed_data.get('course_features', [])
            
            self.logger.info(f"课程名称: {course_name}")
            self.logger.info(f"关键词: {keywords}")
            self.logger.info(f"课程特色: {course_features}")
            
            print(f"[DEBUG] 课程名称: {course_name}")
        except Exception as e:
            self.logger.error(f"构建主图提示词时出错: {str(e)}")
            return []
        
        # 构建主图提示词 - 优化版
        main_prompts = []
        for i in range(self.main_images_count):
            if i == 0:
                prompt = f"高质量教育培训课程主图，主题：{course_name}，现代简约风格，专业感强，教育科技感设计"
            elif i == 1:
                feature_text = '、'.join(course_features[:3]) if course_features else '专业教学'
                highlight_text = ' '.join(keywords[:5]) if keywords else '核心知识点'
                prompt = f"教育培训课程宣传图，展示课程特色：{feature_text}，突出关键内容：{highlight_text}"
            else:
                prompt = f"教育培训课程价值展示图，展示{course_name}学习成果，专业学习环境"
            
            print(f"[DEBUG] 主图{i+1}提示词已构建")
            main_prompts.append(prompt)
        
        # 调用火山图片生成器生成图片
        main_images = []
        for i, prompt in enumerate(main_prompts):
            print(f"[DEBUG] 正在生成第{i+1}张主图")
            try:
                # 设置输出文件名
                output_filename = f"main_image_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # 生成图片
                print(f"[DEBUG] 调用图片生成器")
                image_paths = self.volcano_image_generator.generate_product_images(
                    product_description=prompt,
                    count=1,
                    image_type="main",
                    save_dir=self.output_dir
                )
                
                print(f"[DEBUG] 生成器返回类型: {type(image_paths)}")
                
                # 检查是否成功生成图片
                if image_paths and isinstance(image_paths, list) and len(image_paths) > 0:
                    original_path = image_paths[0]
                    print(f"[DEBUG] 原始图片路径: {original_path}")
                    if os.path.exists(original_path):
                        # 重命名生成的图片文件
                        os.rename(original_path, output_path)
                        print(f"[DEBUG] 图片已重命名为: {os.path.basename(output_path)}")
                        
                        # 验证图片大小并添加到结果
                        if os.path.getsize(output_path) > 100 * 1024:  # 至少100KB
                            main_images.append(output_path)
                            print(f"[DEBUG] 主图{i+1}已添加到结果列表")
                        else:
                            print(f"[DEBUG] 警告: 主图{i+1}文件过小")
                    else:
                        print(f"[DEBUG] 错误: 生成的图片文件不存在")
                else:
                    print(f"[DEBUG] 警告: 未能生成图片")
                
            except Exception as e:
                print(f"[DEBUG] 错误: 生成主图{i+1}失败 - {str(e)}")
        
        print(f"[DEBUG] 主图生成完成，成功数量: {len(main_images)}")
        return main_images
    
    def _generate_detail_images(self, description_parts: Dict[str, Any]) -> List[str]:
        """
        生成详情页图片
        
        Args:
            description_parts: 商品详情部分
            
        Returns:
            生成的详情页图片文件路径列表
        """
        print("[DEBUG] _generate_detail_images called")
        self.logger.info("开始生成详情页图片")
        try:
            pass
        except Exception as e:
            self.logger.error(f"生成详情页图片时出错: {str(e)}")
            return []
        # 从商品详情构建提示词
        title = description_parts.get('title', '')
        content = description_parts.get('content', '')
        target_audience = description_parts.get('target_audience', '')
        learning_outcomes = description_parts.get('learning_outcomes', '')
        
        print(f"[DEBUG] 课程标题: {title}")
        
        # 构建详情页图片提示词 - 简化版
        detail_prompts = []
        
        # 第一张详情页图片
        content_summary = content[:100]
        prompt1 = f"教育培训课程详情页图片，展示{title}的课程大纲和核心学习内容，{content_summary}"
        detail_prompts.append(prompt1)
        print(f"[DEBUG] 详情图1提示词已构建")
        
        # 第二张详情页图片
        audience_summary = target_audience[:50] if target_audience else '广泛适合学习者'
        outcomes_summary = learning_outcomes[:50] if learning_outcomes else '显著学习成效'
        prompt2 = f"教育培训课程价值展示图，展示{title}的学习效果和适合人群：{audience_summary}"
        detail_prompts.append(prompt2)
        print(f"[DEBUG] 详情图2提示词已构建")
        
        # 调用火山图片生成器生成图片
        detail_images = []
        for i, prompt in enumerate(detail_prompts[:self.detail_images_count]):
            print(f"[DEBUG] 正在生成第{i+1}张详情图")
            try:
                # 设置输出文件名
                output_filename = f"detail_image_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # 生成图片
                print(f"[DEBUG] 调用图片生成器")
                image_paths = self.volcano_image_generator.generate_product_images(
                    product_description=prompt,
                    count=1,
                    image_type="detail",
                    save_dir=self.output_dir
                )
                
                print(f"[DEBUG] 生成器返回类型: {type(image_paths)}")
                
                # 检查是否成功生成图片
                if image_paths and isinstance(image_paths, list) and len(image_paths) > 0:
                    original_path = image_paths[0]
                    print(f"[DEBUG] 原始图片路径: {original_path}")
                    if os.path.exists(original_path):
                        # 重命名生成的图片文件
                        os.rename(original_path, output_path)
                        print(f"[DEBUG] 图片已重命名为: {os.path.basename(output_path)}")
                        
                        # 验证图片大小并添加到结果
                        if os.path.getsize(output_path) > 100 * 1024:  # 至少100KB
                            detail_images.append(output_path)
                            print(f"[DEBUG] 详情图{i+1}已添加到结果列表")
                        else:
                            print(f"[DEBUG] 警告: 详情图{i+1}文件过小")
                    else:
                        print(f"[DEBUG] 错误: 生成的图片文件不存在")
                else:
                    print(f"[DEBUG] 警告: 未能生成图片")
                
            except Exception as e:
                print(f"[DEBUG] 错误: 生成详情图{i+1}失败 - {str(e)}")
        
        print(f"[DEBUG] 详情图生成完成，成功数量: {len(detail_images)}")
        return detail_images
    
    def _save_result(self, result: Dict[str, Any]) -> str:
        """
        保存处理结果到文件
        
        Args:
            result: 处理结果
            
        Returns:
            保存的文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"integration_result_{timestamp}.json"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # 保存结果
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # 转换路径为相对路径以便于查看
                result_copy = result.copy()
                if 'main_images' in result_copy:
                    result_copy['main_images'] = [os.path.basename(path) for path in result_copy['main_images']]
                if 'detail_images' in result_copy:
                    result_copy['detail_images'] = [os.path.basename(path) for path in result_copy['detail_images']]
                
                json.dump(result_copy, f, ensure_ascii=False, indent=2)
            
            return output_path
        
        except Exception as e:
            print(f"保存结果失败: {str(e)}")
            return None
    
    def load_client_data_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从文件加载客户资料
        
        Args:
            file_path: 文件路径
            
        Returns:
            客户资料
        """
        return self.client_data_manager.load_client_data(file_path)
    
    def generate_client_data_template_file(self, output_path: str = None) -> str:
        """
        生成客户资料模板文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            保存的文件路径
        """
        if not output_path:
            output_path = os.path.join(self.output_dir, 'client_data_template.json')
        
        template = self.client_data_manager.generate_client_data_template()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def validate_configuration(self) -> bool:
        """
        验证配置是否正确
        
        Returns:
            是否配置正确
        """
        # 检查输出目录
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                print(f"无法创建输出目录: {str(e)}")
                return False
        
        # 检查输出目录写权限
        try:
            test_file = os.path.join(self.output_dir, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            print(f"输出目录无写权限: {str(e)}")
            return False
        
        # 检查火山图片生成器配置
        try:
            # 检查API密钥
            api_key = os.environ.get('VOLCANO_API_KEY')
            if not api_key:
                print("警告: 未设置VOLCANO_API_KEY环境变量")
                # 不立即返回失败，允许在运行时处理
            
            # 验证图片数量配置
            if self.main_images_count <= 0 or self.detail_images_count <= 0:
                print("错误: 图片数量配置必须大于0")
                return False
            
            # 验证客户端管理器和生成器
            if not isinstance(self.client_data_manager, ClientDataManager):
                print("错误: 客户数据管理器初始化失败")
                return False
            
            if not isinstance(self.product_description_generator, ProductDescriptionGenerator):
                print("错误: 商品描述生成器初始化失败")
                return False
            
            if not isinstance(self.volcano_image_generator, VolcanoImageGenerator):
                print("错误: 火山图片生成器初始化失败")
                return False
            
            return True
        except Exception as e:
            print(f"配置验证失败: {str(e)}")
            return False


# 测试代码
if __name__ == "__main__":
    # 创建整合器实例
    config = {
        'output_dir': './test_output',
        'main_images_count': 3,
        'detail_images_count': 2
    }
    
    integrator = ImageGenerationIntegrator(config)
    
    # 验证配置
    if integrator.validate_configuration():
        print("配置验证通过")
    else:
        print("配置验证失败")
        exit(1)
    
    # 生成客户资料模板
    template_path = integrator.generate_client_data_template_file()
    print(f"客户资料模板已生成: {template_path}")
    
    # 进度回调函数
    def show_progress(phase, progress):
        if progress >= 0:
            print(f"进度: {phase} - {progress}%")
        else:
            print(f"进度: {phase} - 处理失败")
    
    # 测试数据
    test_client_data = {
        'course_name': '人工智能与机器学习基础',
        'teacher_info': {
            'name': '王教授',
            'title': 'AI研究专家',
            'experience': '12年人工智能教学与研究经验，曾主持多项国家级AI项目',
            'background': '计算机科学博士，斯坦福大学访问学者'
        },
        'course_content': '本课程系统介绍人工智能和机器学习的基本概念、算法和应用。内容包括：人工智能概述、机器学习基础、监督学习算法、无监督学习算法、深度学习简介、人工智能伦理与社会影响等。课程注重理论与实践相结合，通过案例分析和编程实践帮助学生掌握核心技能。',
        'target_audience': '计算机相关专业的学生，希望了解AI技术的职场人士，对人工智能感兴趣的初学者。',
        'learning_outcomes': '理解人工智能和机器学习的基本概念，掌握常用机器学习算法的原理和应用，能够使用Python实现简单的机器学习模型，了解人工智能的发展趋势和应用前景。',
        'course_features': ['系统全面', '案例丰富', '实战导向', '专家授课', '就业指导']
    }
    
    print("\n开始处理客户请求...")
    try:
        # 处理完整的客户请求，使用进度回调
        result = integrator.process_client_request(test_client_data, progress_callback=show_progress)
        
        # 打印结果摘要
        print("\n处理完成！")
        print(f"总耗时: {result['total_time_seconds']} 秒")
        print(f"生成标题: {result['title']}")
        print(f"生成主图数量: {len(result['main_images'])}")
        for i, img in enumerate(result['main_images']):
            if os.path.exists(img):
                size = os.path.getsize(img) / (1024 * 1024)
                print(f"  主图{i+1}: {os.path.basename(img)} ({size:.2f} MB)")
        
        print(f"生成详情图数量: {len(result['detail_images'])}")
        for i, img in enumerate(result['detail_images']):
            if os.path.exists(img):
                size = os.path.getsize(img) / (1024 * 1024)
                print(f"  详情图{i+1}: {os.path.basename(img)} ({size:.2f} MB)")
        
        # 检查验证结果
        validation = result['validation_result']
        print(f"\n验证结果:")
        print(f"描述有效: {validation['description_valid']}")
        print(f"图片文件有效: {validation['images_valid']}")
        print(f"主图数量符合要求: {validation['main_images_count'] >= 3}")
        print(f"详情图数量符合要求: {validation['detail_images_count'] >= 2}")
        
    except ImageGenerationIntegratorError as e:
        print(f"处理失败: {e}")
    except Exception as e:
        print(f"发生意外错误: {e}")
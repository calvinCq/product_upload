#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试脚本

验证教育培训商品详情生成系统的各个组件和整体功能。
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入系统组件
from client_data_manager import ClientDataManager, ClientDataError
from product_description_generator import ProductDescriptionGenerator, ProductDescriptionError
from sensitive_word_filter import SensitiveWordFilter
from image_generation_integrator import ImageGenerationIntegrator, ImageGenerationIntegratorError


class TestResult:
    """
    测试结果类
    """
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.start_time = datetime.now()
        self.end_time = None
    
    def add_test_result(self, test_name: str, passed: bool, message: str = ""):
        """
        添加测试结果
        """
        self.tests.append({
            'name': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def finish(self):
        """
        完成测试
        """
        self.end_time = datetime.now()
    
    def get_summary(self) -> str:
        """
        获取测试总结
        """
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        summary = f"\n=== 测试总结 ===\n"
        summary += f"总测试数: {len(self.tests)}\n"
        summary += f"通过: {self.passed}\n"
        summary += f"失败: {self.failed}\n"
        summary += f"耗时: {duration:.2f} 秒\n"
        summary += f"通过率: {(self.passed / len(self.tests) * 100) if self.tests else 0:.1f}%\n"
        summary += "=================\n"
        
        # 添加失败的测试详情
        failed_tests = [test for test in self.tests if not test['passed']]
        if failed_tests:
            summary += "\n失败的测试:\n"
            for test in failed_tests:
                summary += f"- {test['name']}: {test['message']}\n"
        
        return summary


def test_sensitive_word_filter(result: TestResult):
    """
    测试敏感词过滤器
    """
    test_name = "敏感词过滤器测试"
    try:
        filter = SensitiveWordFilter()
        
        # 测试检测功能
        text_with_sensitive = "这是一段包含敏感词赌博的文本"
        has_sensitive = filter.has_sensitive_words(text_with_sensitive)
        
        # 测试过滤功能
        filtered_text = filter.filter_text(text_with_sensitive)
        
        # 验证结果
        if has_sensitive and "***" in filtered_text:
            result.add_test_result(test_name, True, "敏感词过滤功能正常")
        else:
            result.add_test_result(test_name, False, "敏感词检测或过滤失败")
            
    except Exception as e:
        result.add_test_result(test_name, False, f"异常: {str(e)}")


def test_client_data_manager(result: TestResult):
    """
    测试客户资料管理器
    """
    test_name = "客户资料管理器测试"
    try:
        manager = ClientDataManager()
        
        # 测试有效数据
        valid_data = {
            'course_name': '测试课程',
            'teacher_info': {
                'name': '测试老师',
                'title': '讲师',
                'experience': '5年经验',
                'background': '相关专业背景'
            },
            'course_content': '课程内容描述',
            'target_audience': '目标受众描述',
            'learning_outcomes': '学习成果描述'
        }
        
        # 验证有效数据
        is_valid = manager.validate_client_data(valid_data)
        if not is_valid:
            result.add_test_result(test_name, False, "有效数据验证失败")
            return
        
        # 处理数据
        processed = manager.process_client_data(valid_data)
        if 'processed' not in processed or not processed['processed']:
            result.add_test_result(test_name, False, "数据处理失败")
            return
        
        # 测试无效数据
        invalid_data = {
            'course_name': '缺少必填字段',
            # 缺少teacher_info
            'course_content': '内容'
        }
        
        try:
            manager.validate_client_data(invalid_data)
            result.add_test_result(test_name, False, "未能检测到无效数据")
            return
        except ClientDataError:
            # 预期会抛出异常
            pass
        
        result.add_test_result(test_name, True, "客户资料管理器功能正常")
        
    except Exception as e:
        result.add_test_result(test_name, False, f"异常: {str(e)}")


def test_product_description_generator(result: TestResult):
    """
    测试商品详情生成器
    """
    test_name = "商品详情生成器测试"
    try:
        generator = ProductDescriptionGenerator()
        
        # 测试数据
        test_data = {
            'course_name': '测试课程名称',
            'teacher_info': {
                'name': '测试老师',
                'title': '高级讲师',
                'experience': '10年经验',
                'background': '博士学位'
            },
            'course_content': '这是课程内容描述，包括多个模块的内容。模块一：基础知识，模块二：进阶技巧，模块三：实战应用。',
            'target_audience': '初学者，进阶学习者，专业人士',
            'learning_outcomes': '掌握基础知识，熟练应用技巧，能够独立完成项目。',
            'course_features': ['特色1', '特色2']
        }
        
        # 生成详情
        description = generator.generate_product_description(test_data)
        
        # 验证生成的各个部分
        required_sections = ['title', 'teacher', 'content', 'audience', 'outcomes']
        for section in required_sections:
            if section not in description or not description[section]:
                result.add_test_result(test_name, False, f"缺少必需部分: {section}")
                return
        
        # 验证详情格式
        is_valid = generator.validate_description(description)
        if not is_valid:
            result.add_test_result(test_name, False, "生成的详情验证失败")
            return
        
        result.add_test_result(test_name, True, "商品详情生成器功能正常")
        
    except Exception as e:
        result.add_test_result(test_name, False, f"异常: {str(e)}")


def test_integrator_without_image_generation(result: TestResult):
    """
    测试整合器（不包含图片生成）
    """
    test_name = "整合器基础功能测试（不含图片生成）"
    try:
        from unittest.mock import patch, MagicMock
        
        # 创建整合器
        config = {'output_dir': './test_integrator_output'}
        integrator = ImageGenerationIntegrator(config)
        
        # 模拟图片生成器
        with patch.object(integrator.volcano_image_generator, 'generate_product_images') as mock_generate:
            # 设置模拟返回值
            mock_generate.return_value = {
                'status': 'success',
                'image_path': '/mock/path/image.png'
            }
            
            # 测试数据
            test_data = {
                'course_name': '整合测试课程',
                'teacher_info': {
                    'name': '测试老师',
                    'title': '讲师',
                    'experience': '5年经验',
                    'background': '相关背景'
                },
                'course_content': '课程内容',
                'target_audience': '目标受众',
                'learning_outcomes': '学习成果'
            }
            
            # 处理请求
            result_data = integrator.process_client_request(test_data)
            
            # 验证结果
            if ('product_description' in result_data and 
                'main_images' in result_data and 
                'detail_images' in result_data):
                result.add_test_result(test_name, True, "整合器基础功能正常")
            else:
                result.add_test_result(test_name, False, "整合器返回的结果不完整")
                
    except ImportError:
        result.add_test_result(test_name, False, "缺少unittest.mock模块")
    except Exception as e:
        result.add_test_result(test_name, False, f"异常: {str(e)}")


def run_full_integration_test(result: TestResult):
    """
    运行完整的集成测试（包含实际图片生成）
    """
    test_name = "完整集成测试（包含图片生成）"
    
    # 检查VOLCANO_API_KEY环境变量
    if not os.environ.get('VOLCANO_API_KEY'):
        result.add_test_result(test_name, False, "未设置VOLCANO_API_KEY环境变量，跳过图片生成测试")
        return
    
    try:
        # 创建整合器
        config = {
            'output_dir': './full_test_output',
            'main_images_count': 1,  # 为了测试减少图片数量
            'detail_images_count': 1
        }
        integrator = ImageGenerationIntegrator(config)
        
        # 完整的测试数据
        test_data = {
            'course_name': 'Python Web开发实战',
            'teacher_info': {
                'name': '张教授',
                'title': '资深全栈工程师',
                'experience': '8年Python开发和教学经验',
                'background': '计算机科学硕士'
            },
            'course_content': '本课程从零开始教授Python Web开发，包括：Flask框架基础、数据库操作、RESTful API开发、前端交互、项目部署等内容。通过实战项目学习，掌握完整的Web开发流程。',
            'target_audience': '零基础学习编程的学生，希望转行Web开发的职场人士，需要提升技能的IT从业者。',
            'learning_outcomes': '掌握Python Web开发核心技能，能够独立开发Web应用，理解前后端交互原理，具备项目实战能力。',
            'course_features': ['零基础友好', '实战项目驱动', '就业指导', '终身学习支持']
        }
        
        print("\n开始完整集成测试（包含实际图片生成）...")
        print("注意：这可能需要几分钟时间...")
        
        # 处理请求
        result_data = integrator.process_client_request(test_data)
        
        # 验证结果
        validation = result_data.get('validation_result', {})
        
        # 检查是否生成了足够的图片
        main_images_count = len(result_data.get('main_images', []))
        detail_images_count = len(result_data.get('detail_images', []))
        
        if (validation.get('description_valid', False) and 
            main_images_count >= 1 and 
            detail_images_count >= 1):
            result.add_test_result(
                test_name, 
                True, 
                f"成功生成{main_images_count}张主图和{detail_images_count}张详情图"
            )
            
            # 打印详细结果
            print(f"\n测试成功！")
            print(f"生成标题: {result_data.get('title', '无')}")
            print(f"主图路径: {', '.join(result_data.get('main_images', []))}")
            print(f"详情图路径: {', '.join(result_data.get('detail_images', []))}")
            print(f"总耗时: {result_data.get('total_time_seconds', 0)}秒")
            
        else:
            error_msg = []
            if not validation.get('description_valid', False):
                error_msg.append("商品描述无效")
            if main_images_count < 1:
                error_msg.append("未生成足够的主图")
            if detail_images_count < 1:
                error_msg.append("未生成足够的详情图")
            
            result.add_test_result(test_name, False, "; ".join(error_msg))
            
    except Exception as e:
        result.add_test_result(test_name, False, f"异常: {str(e)}")

def main():
    """
    主测试函数
    """
    print("===== 教育培训商品详情生成系统 - 综合测试 =====")
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建测试结果对象
    test_result = TestResult()
    
    # 运行各项测试
    print("1. 运行敏感词过滤器测试...")
    test_sensitive_word_filter(test_result)
    
    print("2. 运行客户资料管理器测试...")
    test_client_data_manager(test_result)
    
    print("3. 运行商品详情生成器测试...")
    test_product_description_generator(test_result)
    
    print("4. 运行整合器基础功能测试...")
    test_integrator_without_image_generation(test_result)
    
    # 询问是否运行完整集成测试（包含图片生成）
    run_full_test = False
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        run_full_test = True
    else:
        try:
            response = input("\n是否运行完整集成测试（包含实际图片生成）？这将消耗API额度。(y/n): ")
            run_full_test = response.lower() == 'y'
        except Exception:
            # 如果无法获取用户输入，默认不运行
            run_full_test = False
    
    if run_full_test:
        run_full_integration_test(test_result)
    else:
        test_result.add_test_result("完整集成测试", False, "跳过")
    
    # 完成测试
    test_result.finish()
    
    # 打印测试总结
    print(test_result.get_summary())
    
    # 保存测试报告
    try:
        report_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            report_data = {
                'start_time': test_result.start_time.isoformat(),
                'end_time': test_result.end_time.isoformat() if test_result.end_time else None,
                'passed': test_result.passed,
                'failed': test_result.failed,
                'total': len(test_result.tests),
                'tests': test_result.tests
            }
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"测试报告已保存至: {report_path}")
    except Exception as e:
        print(f"保存测试报告失败: {str(e)}")
    
    # 返回退出码
    return 0 if test_result.failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未预期的错误: {str(e)}")
        sys.exit(1)
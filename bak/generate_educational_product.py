#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教育培训商品生成脚本

使用钱多多API的DeepSeek-V3.1模型生成商品主图、详情页图片和商品详情文案。
"""

import os
import sys
import json
import re
import argparse
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入系统组件
from config_manager import ConfigManager
from image_generation_integrator import ImageGenerationIntegrator
from client_data_manager import ClientDataManager
from volcano_text_generator import VolcanoTextGenerator
from product_description_generator import ProductDescriptionGenerator
from output_formatter import OutputFormatter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('generate_educational_product')


def load_client_data(client_data_path: str, config_file=None) -> dict:
    """
    从文件加载客户资料（支持JSON和Markdown格式）
    
    Args:
        client_data_path: 客户资料文件路径
        config_file: 配置文件路径
        
    Returns:
        客户资料字典
    """
    if not os.path.exists(client_data_path):
        print(f"错误: 找不到输入文件 {client_data_path}")
        sys.exit(1)
    
    # 根据文件扩展名判断格式
    _, ext = os.path.splitext(client_data_path.lower())
    
    if ext == '.json':
        try:
            with open(client_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"错误: JSON文件格式无效 {e}")
            sys.exit(1)
    elif ext in ['.md', '.markdown']:
        try:
            # 使用钱多多API提取信息
            return load_content_with_llm(client_data_path, config_file)
        except Exception as e:
            print(f"错误: Markdown文件解析失败 {e}")
            # 如果大模型调用失败，回退到原始的正则提取方法
            print("回退到正则表达式提取方法")
            return load_markdown_data(client_data_path)
    else:
        print(f"错误: 不支持的文件格式 {ext}，请使用JSON或Markdown文件")
        sys.exit(1)

def load_content_with_llm(file_path: str, config_file=None) -> dict:
    """
    使用钱多多API从文档中提取内容信息
    
    Args:
        file_path: 文档文件路径
        config_file: 配置文件路径
        
    Returns:
        提取的客户资料字典
    """
    print(f"使用钱多多API提取文档信息: {file_path}")
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"成功读取文档文件: {file_path}")
    except Exception as e:
        logger.error(f"读取文档文件失败: {str(e)}")
        raise
    
    # 初始化配置管理器
    config_manager = ConfigManager(config_file)
    
    # 初始化钱多多API文本生成器
    try:
        text_generator = VolcanoTextGenerator(config_manager=config_manager)
        logger.info("钱多多API文本生成器初始化成功")
    except Exception as e:
        logger.error(f"初始化钱多多API文本生成器失败: {str(e)}")
        raise
    
    # 使用大模型提取信息
    try:
        print("使用钱多多API提取文档信息...")
        extracted_info = text_generator.extract_content_info(content)
        logger.info(f"成功提取文档信息，课程名称: {extracted_info.get('course_name', '未知')}")
        
        # 确保数据结构完整
        client_data = ensure_complete_client_data(extracted_info)
        return client_data
    except Exception as e:
        logger.error(f"使用钱多多API提取信息失败: {str(e)}")
        raise

def load_markdown_data(markdown_file: str) -> dict:
    """
    从Markdown文件加载和解析数据（回退方法）
    
    Args:
        markdown_file: Markdown文件路径
        
    Returns:
        转换后的客户资料字典
    """
    print(f"正在解析Markdown文件: {markdown_file}")
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题作为课程名称
    import re
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    course_name = title_match.group(1) if title_match else "销售话术百问百答"
    
    # 提取目录作为课程内容摘要
    toc_match = re.search(r'目\s*录\s*(.+?)\n[^\n]+\n', content, re.DOTALL)
    if toc_match:
        course_content = "\n" + toc_match.group(1).strip()
    else:
        # 如果没有明确的目录，提取所有标题作为内容结构
        sections = re.findall(r'^[一二三四五六七八九十]+、(.+?)$', content, re.MULTILINE)
        course_content = "本课程包含以下主题：\n" + "\n".join([f"- {section}" for section in sections])
    
    # 提取一些问题示例作为课程特色
    questions = re.findall(r'^[0-9]+、(.+?)$', content, re.MULTILINE)
    course_features = []
    for i, q in enumerate(questions[:3], 1):
        course_features.append(f"问答示例{i}：{q[:30]}...")
    
    # 构建客户数据字典
    client_data = {
        'course_name': course_name,
        'teacher_info': {
            'name': '资深顾问',
            'title': '销售培训专家',
            'experience': '5年以上销售培训经验',
            'background': '市场营销专业背景，丰富的一线销售经验'
        },
        'course_content': course_content + "\n\n本课程提供全面的销售话术问答，涵盖基础护理、痘痘问答、仪器问答、破皮项目问答、刷酸问答、脱毛问答、清洁卸妆问答、色素问答等多个方面，帮助销售人员快速应对客户各种疑问。",
        'target_audience': '化妆品销售人员、美容顾问、客户服务人员等需要提升沟通技巧和专业知识的相关人员。',
        'learning_outcomes': '通过本课程学习，学员将能够熟练掌握各类客户问题的专业回答技巧，提升销售转化率，增强客户信任度，建立专业形象，有效处理客户异议。',
        'course_features': course_features if course_features else ['全面的问答知识库', '专业的话术指导', '实用的销售技巧']
    }
    
    print(f"成功从Markdown文件生成客户资料")
    return client_data

def ensure_complete_client_data(data: dict) -> dict:
    """
    确保客户资料数据结构完整
    
    Args:
        data: 提取的原始数据
        
    Returns:
        完整的数据结构
    """
    # 确保所有必需字段都存在
    required_structure = {
        'course_name': data.get('course_name', '默认课程'),
        'teacher_info': {
            'name': data.get('teacher_info', {}).get('name', '资深顾问'),
            'title': data.get('teacher_info', {}).get('title', '销售培训专家'),
            'experience': data.get('teacher_info', {}).get('experience', '5年以上销售培训经验'),
            'background': data.get('teacher_info', {}).get('background', '市场营销专业背景，丰富的一线销售经验')
        },
        'course_content': data.get('course_content', f"本课程涵盖{data.get('course_name', '默认课程')}的核心知识点。"),
        'target_audience': data.get('target_audience', '相关行业从业人员及对此领域感兴趣的人士。'),
        'learning_outcomes': data.get('learning_outcomes', '通过本课程学习，学员将掌握相关领域的核心知识和技能。'),
        'course_features': data.get('course_features', []) if isinstance(data.get('course_features'), list) else ['专业的讲解和指导']
    }
    
    # 如果课程特色为空，添加默认项
    if not required_structure['course_features']:
        required_structure['course_features'] = ['全面的知识体系', '专业的话术指导', '实用的技能培训']
    
    return required_structure

def generate_client_data_template(output_file: str) -> None:
    """
    生成客户资料模板
    
    Args:
        output_file: 输出文件路径
    """
    manager = ClientDataManager()
    template = manager.generate_client_data_template()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    print(f"客户资料模板已生成: {output_file}")
    print("请根据模板填写客户资料后重新运行脚本")

def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='教育培训商品生成工具')
    parser.add_argument('--client_data', '-i', type=str, help='客户资料文件路径')
    parser.add_argument('--output_dir', '-o', type=str, default='./output', help='输出目录路径')
    parser.add_argument('--template', '-t', action='store_true', help='生成客户资料模板')
    parser.add_argument('--template-file', type=str, default='client_data_template.json', help='模板输出文件路径')
    parser.add_argument('--main-images', type=int, default=3, help='主图数量')
    parser.add_argument('--detail-images', type=int, default=2, help='详情页图片数量')
    parser.add_argument('--config_file', help='配置文件路径')
    parser.add_argument('--default-config', default='product_generator_config.json', help='默认配置文件路径')
    
    args = parser.parse_args()
    
    # 检查是否只生成模板
    if args.template:
        generate_client_data_template(args.template_file)
        return
    
    # 检查输入文件
    if not args.client_data:
        print("错误: 必须指定输入文件或使用--template选项生成模板")
        parser.print_help()
        sys.exit(1)
    
    # 使用配置管理器
    config_manager = ConfigManager(args.config_file or args.default_config)
    
    # 如果配置文件不存在，创建一个默认的
    if not os.path.exists(args.config_file or args.default_config):
        config_manager.save_default_config()
    else:
        config_manager.load_config()
    
    # 更新配置
    config_manager.update_config({
        'output_dir': args.output_dir,
        'main_images_count': args.main_images,
        'detail_images_count': args.detail_images,
        'use_qianduoduo': True  # 强制使用钱多多API
    })
    
    # 检查钱多多API配置
    print("正在检查钱多多API配置...")
    try:
        qianduoduo_config = config_manager.get_qianduoduo_api_config()
        print("钱多多API配置检查完成")
        print(f"使用模型: {qianduoduo_config.get('model_name', 'DeepSeek-V3.1')}")
        if not qianduoduo_config.get('api_key'):
            print("警告: 钱多多API密钥未配置，将使用默认密钥")
    except Exception as e:
        print(f"警告: 钱多多API配置检查失败: {str(e)}")
        print("将使用内置默认配置")
    
    # 创建输出目录
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"已创建输出目录: {args.output_dir}")
    
    print(f"===== 教育培训商品生成开始 =====")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输入文件: {args.client_data}")
    print(f"输出目录: {args.output_dir}")
    print(f"生成配置: 主图{args.main_images}张, 详情图{args.detail_images}张")
    print()
    
    # 加载客户资料
    print("加载客户资料: {args.client_data}")
    client_data = load_client_data(args.client_data, args.config_file)
    print("客户资料加载成功")
    print(f"课程名称: {client_data.get('course_name', '未指定')}")
    print(f"老师姓名: {client_data.get('teacher_info', {}).get('name', '未指定')}")
    print()
    
    # 创建整合器，使用配置管理器
    integrator = ImageGenerationIntegrator(config_manager=config_manager)
    
    # 验证配置
    if not integrator.validate_configuration():
        print("错误: 配置验证失败")
        sys.exit(1)
    
    try:
        # 处理客户请求
        print("开始生成商品内容...")
        print("这可能需要几分钟时间，请耐心等待...")
        print("=", end="", flush=True)
        
        # 这里使用一个简单的进度指示
        def progress_callback(step, total):
            nonlocal progress_shown
            if step % 2 == 0:  # 每2步显示一个进度符号
                print("=", end="", flush=True)
        
        progress_shown = False
        
        # 执行生成
        result = integrator.process_client_request(client_data)
        
        print("\n\n===== 生成完成！ =====")
        print(f"总耗时: {result['total_time_seconds']:.2f} 秒")
        print()
        
        # 显示生成结果摘要
        print("【生成结果摘要】")
        print(f"商品标题: {result.get('title', '无')}")
        print()
        
        # 显示商品详情各部分
        print("【商品详情文案】")
        description = result.get('product_description', {})
        for section_name, content in description.items():
            print(f"\n{section_name.upper()}:")
            # 只显示前100个字符作为预览
            preview = content[:100] + ("..." if len(content) > 100 else "")
            print(preview.replace("\n", " "))
        print()
        
        # 显示图片信息
        print("【生成图片信息】")
        main_images = result.get('main_images', [])
        detail_images = result.get('detail_images', [])
        
        print(f"主图 ({len(main_images)}张):")
        for i, img_path in enumerate(main_images, 1):
            print(f"  {i}. {os.path.basename(img_path)}")
        
        print(f"\n详情页图片 ({len(detail_images)}张):")
        for i, img_path in enumerate(detail_images, 1):
            print(f"  {i}. {os.path.basename(img_path)}")
        print()
        
        # 显示验证结果
        print("【验证结果】")
        validation = result.get('validation_result', {})
        print(f"描述有效性: {'✓ 通过' if validation.get('description_valid', False) else '✗ 未通过'}")
        print(f"主图数量: {'✓ 符合要求' if validation.get('main_images_count', 0) >= args.main_images else '✗ 不足'}")
        print(f"详情图数量: {'✓ 符合要求' if validation.get('detail_images_count', 0) >= args.detail_images else '✗ 不足'}")
        print()
        
        # 显示保存信息
        print("【文件保存信息】")
        # 保存完整结果
        result_file = os.path.join(args.output_dir, f"product_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"完整结果已保存: {result_file}")
        
        # 保存商品详情文本
        description_file = os.path.join(args.output_dir, f"product_description_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(description_file, 'w', encoding='utf-8') as f:
            f.write(result.get('full_description_text', ''))
        print(f"商品详情文本已保存: {description_file}")
        
        # 保存微信小店格式的详情
        wechat_file = os.path.join(args.output_dir, f"wechat_description_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        from product_description_generator import ProductDescriptionGenerator
        generator = ProductDescriptionGenerator()
        wechat_format = generator.format_for_wechat_shop(description)
        with open(wechat_file, 'w', encoding='utf-8') as f:
            f.write(wechat_format)
        print(f"微信小店格式详情已保存: {wechat_file}")
        
        print()
        print("===== 任务完成！ =====")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("生成的所有文件都保存在输出目录中，可以直接用于微信小店商品上架。")
        
    except Exception as e:
        print(f"\n错误: 生成过程中发生错误 - {str(e)}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生未预期的错误: {str(e)}")
        sys.exit(1)
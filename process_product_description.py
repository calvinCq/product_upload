#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
处理sample_product_description.txt，生成产品描述和图片，并上传商品
"""

import os
import sys
import json
import asyncio
import random
import argparse
from typing import Dict, Any, Optional, List

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入核心模块
from src.config.config_manager import ConfigManager
from src.utils.logger import log_message, get_logger, set_log_level
from src.utils.exceptions import ConfigError, ValidationError, APIError, handle_exception, catch_exceptions
from src.core.product_generator import ProductGenerator as CoreProductGenerator
from src.core.product_uploader import ProductUploader as CoreProductUploader

# 初始化日志记录器
logger = get_logger("process_product_description")

# 确保正确使用导入的CoreProductGenerator和CoreProductUploader

def parse_product_description_file(file_path: str) -> Dict[str, Any]:
    """
    解析产品描述文件
    
    :param file_path: 文件路径
    :return: 解析后的产品描述数据
    """
    logger.info(f"读取产品描述文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析文件内容
    sections = {
        'title': '',
        'teacher_intro': '',
        'course_outline': [],
        'target_audience': [],
        'learning_outcomes': []
    }
    
    # 提取标题
    title_section = content.split('## 1. 标题')[1].split('## 2. 老师简介')[0].strip()
    sections['title'] = title_section.strip()
    
    # 提取老师简介
    teacher_section = content.split('## 2. 老师简介')[1].split('## 3. 课程大纲')[0].strip()
    sections['teacher_intro'] = ' '.join([line.strip() for line in teacher_section.split('\n') if line.strip()])
    
    # 提取课程大纲
    outline_section = content.split('## 3. 课程大纲')[1].split('## 4. 适用人群')[0].strip()
    outline_items = []
    for line in outline_section.split('\n'):
        line = line.strip()
        if line and line[0].isdigit():
            # 提取大纲内容，去掉数字前缀
            item_content = line.split('. ', 1)[1].strip() if '. ' in line else line[2:].strip()
            outline_items.append(item_content)
    sections['course_outline'] = outline_items
    
    # 提取适用人群
    audience_section = content.split('## 4. 适用人群')[1].split('## 5. 学完收获')[0].strip()
    audience_items = []
    for line in audience_section.split('\n'):
        line = line.strip()
        if line.startswith('-'):
            audience_items.append(line[1:].strip())
    sections['target_audience'] = audience_items
    
    # 提取学完收获
    outcomes_section = content.split('## 5. 学完收获')[1].strip()
    outcome_items = []
    for line in outcomes_section.split('\n'):
        line = line.strip()
        if line.startswith('-'):
            outcome_items.append(line[1:].strip())
    sections['learning_outcomes'] = outcome_items
    
    logger.info(f"成功解析产品描述，提取了标题、老师简介、{len(outline_items)}项课程大纲、{len(audience_items)}项适用人群和{len(outcome_items)}项学习收获")
    return sections

def convert_to_client_data(sections: Dict[str, Any]) -> Dict[str, Any]:
    """
    将解析后的产品描述转换为客户数据格式
    
    :param sections: 解析后的产品描述部分
    :return: 客户数据格式
    """
    # 构建客户数据格式，使其适合ProductGenerator处理
    client_data = {
        "client_name": "洪总",
        "client_info": sections['teacher_intro'],
        "course_title": sections['title'],
        "course_outline": sections['course_outline'],
        "target_audience": sections['target_audience'],
        "learning_outcomes": sections['learning_outcomes'],
        "industry": "大健康",
        "product_type": "课程",
        "price_range": [299, 599],
        "category": "知识付费"
    }
    
    return client_data

def generate_and_save_product(client_data: Dict[str, Any], config_manager: ConfigManager, output_dir: str) -> Dict[str, Any]:
    """
    生成商品并保存
    
    :param client_data: 客户数据
    :param config_manager: 配置管理器
    :param output_dir: 输出目录
    :return: 生成的商品数据
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建商品生成器
        generator = CoreProductGenerator(config_manager=config_manager)
        
        # 生成单个商品
        logger.info("开始生成商品...")
        products = generator.generate_products(client_data, 1)
        
        # 更安全的结果检查和类型处理
        if not products:
            logger.error("商品生成失败: 没有返回商品数据")
            raise ValueError("商品生成失败: 没有返回商品数据")
        
        # 确保处理字典或列表格式
        if isinstance(products, dict):
            product = products
        elif isinstance(products, list) and products:
            product = products[0]
        else:
            logger.error("生成的商品数据格式无效")
            raise ValueError("生成的商品数据格式无效")
        
        # 保存商品数据
        product_file = os.path.join(output_dir, 'generated_product.json')
        with open(product_file, 'w', encoding='utf-8') as f:
            json.dump([product], f, ensure_ascii=False, indent=2)
        logger.info(f"商品数据已保存到: {product_file}")
        
        return product
    except Exception as e:
        logger.error(f"生成商品过程中出错: {str(e)}")
        raise

def upload_product(product: Dict[str, Any], config_manager: ConfigManager, output_dir: str) -> Dict[str, Any]:
    """
    上传商品
    
    :param product: 商品数据
    :param config_manager: 配置管理器
    :param output_dir: 输出目录
    :return: 上传结果
    """
    try:
        # 创建商品上传器
        uploader = CoreProductUploader(config_manager=config_manager)
        
        # 上传商品
        logger.info("开始上传商品...")
        results = uploader.upload_products([product])
        
        # 生成上传报告
        report = uploader.generate_upload_report(results)
        logger.info(f"上传报告:\n{report}")
        
        # 保存上传结果
        result_file = os.path.join(output_dir, 'upload_result.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"上传结果已保存到: {result_file}")
        
        # 保存报告文件
        report_file = os.path.join(output_dir, 'upload_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"上传报告已保存到: {report_file}")
        
        return results
    except ConnectionError:
        raise
    except Exception as e:
        logger.error(f"商品上传过程中出错: {str(e)}")
        raise Exception(f"商品上传失败: {str(e)}")

def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    :return: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='处理产品描述文件，生成并上传商品')
    
    # 输入选项
    parser.add_argument('--input-file', '-i', type=str, 
                       default='sample_product_description.txt',
                       help='产品描述文件路径（默认: sample_product_description.txt）')
    
    # 输出选项
    parser.add_argument('--output-dir', '-o', type=str, default='output', 
                       help='输出目录（默认: output）')
    
    # 处理选项
    parser.add_argument('--generate-only', action='store_true', help='仅生成商品，不上传')
    parser.add_argument('--use-sandbox', action='store_true', help='使用沙箱模式（不执行实际上传）')
    
    # 配置选项
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    
    # 日志选项
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='日志级别（默认: INFO）')
    
    args = parser.parse_args()
    
    # 应用日志级别
    set_log_level(args.log_level)
    
    return args

def main() -> None:
    """
    主函数
    """
    logger.info("开始处理产品描述文件...")
    
    # 解析命令行参数
    args = parse_args()
    
    # 初始化配置管理器
    try:
        config_manager = ConfigManager(config_path=args.config)
        logger.info("配置管理器初始化成功")
    except ConfigError as e:
        logger.error(f"配置初始化失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"配置管理器初始化失败: {str(e)}")
        sys.exit(1)
    
    try:
        # 解析产品描述文件
        if not os.path.exists(args.input_file):
            logger.error(f"产品描述文件不存在: {args.input_file}")
            sys.exit(1)
        
        sections = parse_product_description_file(args.input_file)
        
        # 转换为客户数据格式
        client_data = convert_to_client_data(sections)
        logger.debug(f"生成的客户数据: {json.dumps(client_data, ensure_ascii=False, indent=2)}")
        
        # 生成商品
        product = generate_and_save_product(client_data, config_manager, args.output_dir)
        
        # 上传商品（如果不是仅生成模式）
        if not args.generate_only:
            if args.use_sandbox:
                logger.info("使用沙箱模式，跳过实际上传")
            else:
                results = upload_product(product, config_manager, args.output_dir)
                
                # 检查上传结果
                if results.get('success') > 0:
                    logger.info("商品上传成功！")
                else:
                    logger.error("商品上传失败！")
                    sys.exit(1)
        
        logger.info("产品描述处理完成！")
        
    except KeyboardInterrupt:
        logger.warning("用户中断操作")
    except ValidationError as e:
        logger.error(f"数据验证失败: {e.message}")
        sys.exit(1)
    except APIError as e:
        logger.error(f"API调用失败: {e.message}")
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"连接失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
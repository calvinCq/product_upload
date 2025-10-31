#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山大模型图片生成与商品上传工具

此脚本提供命令行界面，用于测试火山大模型图片生成功能和商品上传流程。
"""

import os
import json
import argparse
import logging
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('volcano_generate_tool')

# 导入必要的模块
from config_manager import ConfigManager
from volcano_image_generator import VolcanoImageGenerator
from product_with_image_generator import ProductWithImageGenerator

def load_example_product_data(shop_type: str) -> Dict[str, Any]:
    """
    加载示例商品数据
    
    Args:
        shop_type: 店铺类型，'traditional' 或 'video_shop'
    
    Returns:
        示例商品数据字典
    """
    if shop_type == 'video_shop':
        # 视频号小店示例数据
        return {
            "title": "测试商品",
            "desc": "这是一个用于测试的商品描述",
            "category_id1": 1,
            "category_id2": 2,
            "price": 9990,
            "origin_price": 19990,
            "stock": 100,
            "main_img": [],
            "desc_img": [],
            "video_info": {}
        }
    else:
        # 传统小店示例数据
        return {
            "product_id": f"test_{int(time.time())}",
            "title": "测试商品",
            "price": 9990,
            "origin_price": 19990,
            "stock": 100,
            "main_img": [],
            "desc_img": []
        }

def interactive_mode():
    """
    交互式模式，引导用户输入必要信息并执行操作
    """
    print("=" * 60)
    print("火山大模型图片生成与商品上传工具")
    print("=" * 60)
    
    # 加载配置
    try:
        config_manager = ConfigManager()
        volcano_config = config_manager.get_volcano_api_config()
        logger.info("配置加载成功")
    except Exception as e:
        logger.error(f"配置加载失败: {str(e)}")
        return
    
    # 选择操作类型
    print("\n请选择操作类型：")
    print("1. 仅生成图片")
    print("2. 生成图片并上传商品")
    
    operation_choice = input("请输入选择 (1-2): ").strip()
    
    if operation_choice not in ['1', '2']:
        logger.error("无效的选择")
        return
    
    # 输入商品描述
    print("\n商品描述输入选项:")
    print("1. 直接输入商品描述文本")
    print("2. 输入商品描述文件路径")
    print("3. 上传商品描述文件")
    option = input("请选择(1-3): ").strip()
    
    product_description = ""
    if option == "1":
        print("请输入商品描述内容:")
        product_description = input().strip()
    elif option == "2":
        print("请输入商品描述文件路径:")
        file_path = input().strip()
        product_description = file_path
    elif option == "3":
        print("请输入要上传的文件路径:")
        file_path = input().strip()
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在: {file_path}")
            return
        product_description = file_path
    else:
        print("无效选项，默认使用直接输入模式")
        print("请输入商品描述内容:")
        product_description = input().strip()
        
    if not product_description:
        logger.error("商品描述不能为空")
        return
    
    # 初始化图片生成器
    try:
        image_generator = VolcanoImageGenerator(config=volcano_config)
        logger.info("火山大模型图片生成器初始化成功")
    except Exception as e:
        logger.error(f"火山大模型图片生成器初始化失败: {str(e)}")
        return
    
    # 执行仅生成图片操作
    if operation_choice == '1':
        try:
            # 生成图片
            main_count = volcano_config.get('main_images_count', 3)
            detail_count = volcano_config.get('detail_images_count', 2)
            
            print(f"\n正在生成 {main_count} 张主图和 {detail_count} 张详情图...")
            
            main_image_paths = image_generator.generate_product_images(
                product_description=product_description,
                count=main_count,
                image_type="main"
            )
            
            detail_image_paths = image_generator.generate_product_images(
                product_description=product_description,
                count=detail_count,
                image_type="detail"
            )
            
            print(f"\n图片生成成功！")
            print(f"主图列表 ({len(main_image_paths)}):")
            for i, path in enumerate(main_image_paths, 1):
                print(f"  {i}. {path}")
            
            print(f"\n详情图列表 ({len(detail_image_paths)}):")
            for i, path in enumerate(detail_image_paths, 1):
                print(f"  {i}. {path}")
                
        except Exception as e:
            logger.error(f"图片生成失败: {str(e)}")
            return
    
    # 执行生成图片并上传商品操作
    elif operation_choice == '2':
        # 选择店铺类型
        print("\n请选择店铺类型：")
        print("1. 传统小店")
        print("2. 视频号小店")
        
        shop_choice = input("请输入选择 (1-2): ").strip()
        
        if shop_choice == '1':
            shop_type = 'traditional'
        elif shop_choice == '2':
            shop_type = 'video_shop'
        else:
            logger.error("无效的店铺类型选择")
            return
        
        # 加载或输入商品数据
        print("\n1. 使用示例商品数据")
        print("2. 从JSON文件加载商品数据")
        data_choice = input("请选择商品数据来源 (1-2): ").strip()
        
        if data_choice == '1':
            product_data = load_example_product_data(shop_type)
            print("已加载示例商品数据。您可以修改以下字段：")
            
            # 允许用户修改关键字段
            title = input(f"商品标题 (当前: {product_data['title']}): ").strip()
            if title:
                product_data['title'] = title
            
            price = input(f"商品价格 (当前: {product_data['price']}): ").strip()
            if price and price.isdigit():
                product_data['price'] = int(price)
                
        elif data_choice == '2':
            file_path = input("请输入JSON文件路径: ").strip()
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                logger.info("商品数据加载成功")
            except Exception as e:
                logger.error(f"商品数据加载失败: {str(e)}")
                return
        else:
            logger.error("无效的数据来源选择")
            return
        
        # 初始化商品上传器
        try:
            api_config = config_manager.get_api_config()
            product_uploader = ProductWithImageGenerator(
                volcano_config=volcano_config,
                wechat_api_config=api_config
            )
            logger.info("商品上传器初始化成功")
        except Exception as e:
            logger.error(f"商品上传器初始化失败: {str(e)}")
            return
        
        # 确认操作
        print("\n即将执行以下操作：")
        print(f"1. 使用火山大模型生成商品图片")
        print(f"2. 上传图片到微信小店")
        print(f"3. 上传商品数据到 {shop_type}")
        print(f"商品标题: {product_data['title']}")
        
        confirm = input("确认执行以上操作？(y/n): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        # 执行生成和上传操作
        try:
            print("\n开始执行生成图片和上传商品...")
            result = product_uploader.generate_images_and_upload_product(
                product_description=product_description,
                product_data=product_data,
                shop_type=shop_type
            )
            
            if result['success']:
                print("\n✅ 操作成功完成！")
                print(f"商品ID: {result.get('product_id')}")
                print(f"生成的主图数量: {len(result['generated_images']['main'])}")
                print(f"生成的详情图数量: {len(result['generated_images']['detail'])}")
            else:
                print(f"\n❌ 操作失败：")
                print(f"错误信息: {result.get('message')}")
                
        except Exception as e:
            logger.error(f"执行过程中发生错误: {str(e)}")
            return

def main():
    """
    主函数，处理命令行参数并执行相应操作
    """
    # 检查VOLCANO_API_KEY配置
    config_manager = ConfigManager(config_path="product_generator_config.json")
    config_manager.load_config()
    volcano_config = config_manager.get_volcano_api_config()
    if not volcano_config.get('api_key'):
        print("⚠️  警告: 未设置VOLCANO_API_KEY")
        print("配置优先级(从高到低):")
        print("1. 配置文件中的volcano_api部分的api_key")
        print("2. VOLCANO_API_KEY环境变量")
        print("3. .env文件中的VOLCANO_API_KEY")
        print()
    parser = argparse.ArgumentParser(description='火山大模型图片生成与商品上传工具')
    parser.add_argument('--interactive', '-i', action='store_true', 
                      help='启动交互式模式')
    parser.add_argument('--generate-images', '-g', action='store_true',
                      help='仅生成图片')
    parser.add_argument('--generate-and-upload', '-gu', action='store_true',
                      help='生成图片并上传商品')
    parser.add_argument('--description', '-d', type=str,
                      help='商品描述内容或包含商品描述的文件路径')
    parser.add_argument('--shop-type', '-t', choices=['traditional', 'video_shop'],
                      help='店铺类型')
    parser.add_argument('--product-data', '-p', type=str,
                      help='商品数据JSON文件路径')
    
    args = parser.parse_args()
    
    # 交互式模式
    if args.interactive:
        interactive_mode()
        return
    
    # 命令行模式
    if args.generate_images:
        # 仅生成图片模式
        if not args.description:
            print("错误: 需要提供商品描述内容 (-d 参数)")
            parser.print_help()
            return
        
        try:
            config_manager = ConfigManager(config_path="product_generator_config.json")
            config_manager.load_config()
            volcano_config = config_manager.get_volcano_api_config()
            image_generator = VolcanoImageGenerator(config=volcano_config)
            
            main_count = volcano_config.get('main_images_count', 3)
            detail_count = volcano_config.get('detail_images_count', 2)
            
            print(f"正在生成 {main_count} 张主图和 {detail_count} 张详情图...")
            
            main_image_paths = image_generator.generate_product_images(
                product_description=args.description,
                count=main_count,
                image_type="main"
            )
            
            detail_image_paths = image_generator.generate_product_images(
                product_description=args.description,
                count=detail_count,
                image_type="detail"
            )
            
            print(f"\n图片生成成功！")
            print(f"主图列表:")
            for path in main_image_paths:
                print(f"  - {path}")
            
            print(f"\n详情图列表:")
            for path in detail_image_paths:
                print(f"  - {path}")
                
        except Exception as e:
            print(f"错误: {str(e)}")
            return
    
    elif args.generate_and_upload:
        # 生成图片并上传商品模式
        if not args.description:
            print("错误: 需要提供商品描述内容 (-d 参数)")
            parser.print_help()
            return
        
        if not args.shop_type:
            print("错误: 需要提供店铺类型 (-t 参数)")
            parser.print_help()
            return
        
        # 加载商品数据
        if args.product_data:
            if not os.path.exists(args.product_data):
                print(f"错误: 商品数据文件不存在: {args.product_data}")
                return
            
            try:
                with open(args.product_data, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
            except Exception as e:
                print(f"错误: 加载商品数据失败: {str(e)}")
                return
        else:
            product_data = load_example_product_data(args.shop_type)
            print("使用默认商品数据")
        
        try:
            config_manager = ConfigManager(config_path="product_generator_config.json")
            config_manager.load_config()
            volcano_config = config_manager.get_volcano_api_config()
            api_config = config_manager.get_api_config()
            
            product_uploader = ProductWithImageGenerator(
                volcano_config=volcano_config,
                wechat_api_config=api_config
            )
            
            print("开始执行生成图片和上传商品...")
            result = product_uploader.generate_images_and_upload_product(
                product_description=args.description,
                product_data=product_data,
                shop_type=args.shop_type
            )
            
            if result['success']:
                print("\n✅ 操作成功完成！")
                print(f"商品ID: {result.get('product_id')}")
            else:
                print(f"\n❌ 操作失败：")
                print(f"错误信息: {result.get('message')}")
                
        except Exception as e:
            print(f"错误: {str(e)}")
            return
    
    else:
        # 没有指定操作，显示帮助信息
        parser.print_help()

if __name__ == "__main__":
    import time
    main()
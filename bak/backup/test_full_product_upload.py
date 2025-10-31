#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入所需模块
from product_with_image_generator import ProductWithImageGenerator

def main():
    """
    测试完整的商品图片生成和上传流程
    1. 生成3张主图和2张详情图
    2. 上传商品到微信小店
    """
    try:
        # 从环境变量获取API密钥
        volcano_api_key = os.environ.get("VOLCANO_API_KEY")
        
        if not volcano_api_key:
            print("错误: 请设置VOLCANO_API_KEY环境变量")
            print("可以通过以下方式设置:")
            print("1. 在命令行中: set VOLCANO_API_KEY=your_api_key")
            print("2. 在.env文件中添加: VOLCANO_API_KEY=your_api_key")
            return
        
        # 创建商品图片生成与上传集成实例
        # 使用配置文件中的设置，应该已经配置了3张主图和2张详情图
        generator = ProductWithImageGenerator()
        
        # 确认配置
        print(f"配置信息: 主图数量={generator.main_images_count}, 详情图数量={generator.detail_images_count}")
        print(f"图片保存目录: {generator.image_save_dir}")
        
        # 商品描述 - 根据客户要求生成图片
        product_description = "高端商务笔记本电脑，15.6英寸全高清屏幕，16GB内存，512GB固态硬盘，金属机身，轻薄便携，适合办公和轻度游戏"
        
        # 商品数据 - 完整的商品信息
        product_data = {
            "title": "高端商务办公笔记本电脑 15.6英寸全面屏",
            "desc": "本款笔记本电脑采用金属机身设计，轻薄便携，配备高性能处理器和独立显卡，16GB大内存和512GB高速固态硬盘，提供流畅的使用体验。全高清屏幕显示效果出色，长效电池续航满足一天办公需求。",
            "price": 599900,  # 价格（分）
            "original_price": 699900,
            "stock": 50,
            "category_id1": "381003",  # 电子产品
            "category_id2": "380003",  # 电脑办公
            "category_id3": "517050",  # 笔记本电脑
            "sku_list": [
                {
                    "price": 599900,
                    "original_price": 699900,
                    "stock": 50,
                    "sku_attr": ["银色", "16GB/512GB"]
                }
            ],
            "deliver_method": 0,  # 快递发货
            "express_type": 0,  # 普通快递
            "location": "广东省深圳市",
            "is_presell": 0,  # 非预售
            "presale_info": {}
        }
        
        print("\n===== 开始测试图片生成 =====")
        print(f"商品描述: {product_description}")
        
        # 1. 先生成图片，测试图片生成功能
        images = generator.generate_images_only(product_description)
        print(f"\n图片生成结果:")
        print(f"✅ 生成了 {len(images['main'])} 张主图")
        for i, path in enumerate(images['main'], 1):
            print(f"  主图{i}: {path}")
            if os.path.exists(path):
                file_size = os.path.getsize(path) / 1024 / 1024
                print(f"    大小: {file_size:.2f} MB")
            else:
                print(f"    ⚠️ 文件不存在")
        
        print(f"✅ 生成了 {len(images['detail'])} 张详情图")
        for i, path in enumerate(images['detail'], 1):
            print(f"  详情图{i}: {path}")
            if os.path.exists(path):
                file_size = os.path.getsize(path) / 1024 / 1024
                print(f"    大小: {file_size:.2f} MB")
            else:
                print(f"    ⚠️ 文件不存在")
        
        print("\n===== 开始测试商品上传 =====")
        print("注意: 上传功能需要微信小店API配置正确")
        
        # 2. 尝试完整的生成图片和上传商品流程
        # 注意：这里会重新生成图片，为了完整测试
        print("\n开始生成图片并上传商品...")
        result = generator.generate_images_and_upload_product(
            product_description=product_description,
            product_data=product_data
        )
        
        # 3. 显示结果
        if result.get("success"):
            print(f"\n🎉 商品上传成功！")
            print(f"商品ID: {result.get('product_id')}")
            print(f"\n生成的图片:")
            print(f"  主图: {len(result['generated_images']['main'])} 张")
            for path in result['generated_images']['main']:
                print(f"    - {path}")
            print(f"  详情图: {len(result['generated_images']['detail'])} 张")
            for path in result['generated_images']['detail']:
                print(f"    - {path}")
            
            print(f"\n上传的图片URL:")
            print(f"  主图URL: {len(result['uploaded_image_urls']['main'])} 个")
            for url in result['uploaded_image_urls']['main']:
                print(f"    - {url}")
            print(f"  详情图URL: {len(result['uploaded_image_urls']['detail'])} 个")
            for url in result['uploaded_image_urls']['detail']:
                print(f"    - {url}")
        else:
            print(f"\n❌ 商品上传失败: {result.get('message')}")
            print(f"错误类型: {result.get('error_type')}")
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n===== 清理临时文件 =====")
        if 'generator' in locals():
            generator.cleanup_temp_images()
        print("测试完成！")

if __name__ == "__main__":
    main()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
import time
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入图片生成器
from volcano_image_generator import VolcanoImageGenerator

def main():
    """
    测试火山API生成图片功能
    只测试生成3张主图和2张详情图，不包含商品上传
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
        
        # 读取配置文件
        config_path = 'product_generator_config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 获取图片数量配置
            main_images_count = config.get('volcano_api', {}).get('main_images_count', 3)
            detail_images_count = config.get('volcano_api', {}).get('detail_images_count', 2)
            image_save_dir = config.get('volcano_api', {}).get('image_save_dir', './test_generated_images')
            
            print(f"从配置文件读取的设置:")
            print(f"  主图数量: {main_images_count}")
            print(f"  详情图数量: {detail_images_count}")
            print(f"  图片保存目录: {image_save_dir}")
        else:
            # 默认配置
            main_images_count = 3
            detail_images_count = 2
            image_save_dir = './test_generated_images'
            print(f"使用默认设置:")
            print(f"  主图数量: {main_images_count}")
            print(f"  详情图数量: {detail_images_count}")
            print(f"  图片保存目录: {image_save_dir}")
        
        # 确保保存目录存在
        os.makedirs(image_save_dir, exist_ok=True)
        
        # 初始化图片生成器
        generator = VolcanoImageGenerator(api_key=volcano_api_key)
        
        # 商品描述 - 用于生成图片
        product_description = "高端商务笔记本电脑，15.6英寸全高清屏幕，16GB内存，512GB固态硬盘，金属机身，轻薄便携，适合办公和轻度游戏"
        
        print("\n===== 开始测试生成3张主图 =====")
        main_images = []
        start_time = time.time()
        
        for i in range(1, main_images_count + 1):
            print(f"\n生成主图 {i}/{main_images_count}...")
            # 为每张图片生成不同的提示词，增加细节变化
            prompt = f"产品摄影：高端商务笔记本电脑，{i}号视角，{product_description}，高质量，专业打光，白色简约背景，8K高清"
            
            # 生成图片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"main_{timestamp}_{i}.jpg"
            filepath = os.path.join(image_save_dir, filename)
            
            try:
                # 调用API生成图片
                try:
                    # 调用generate_product_images方法生成一张图片
                    paths = generator.generate_product_images(
                        product_description=prompt,
                        count=1,
                        image_type="main",
                        save_dir=image_save_dir
                    )
                    
                    if paths:
                        # 获取生成的图片路径
                        generated_path = paths[0]
                        print(f"✅ 主图{i}生成成功: {generated_path}")
                        if os.path.exists(generated_path):
                            file_size = os.path.getsize(generated_path)
                            print(f"  文件大小: {file_size / 1024 / 1024:.2f} MB")
                        main_images.append(generated_path)
                    else:
                        print(f"❌ 主图{i}生成失败: 返回空路径列表")
                except Exception as e:
                    print(f"❌ 主图{i}API调用失败: {str(e)}")
            except Exception as e:
                print(f"❌ 主图{i}生成过程中出错: {str(e)}")
        
        main_total_time = time.time() - start_time
        print(f"\n主图生成完成，耗时: {main_total_time:.2f}秒")
        print(f"成功生成: {len(main_images)}张主图")
        
        print("\n===== 开始测试生成2张详情图 =====")
        detail_images = []
        start_time = time.time()
        
        # 详情图1：键盘特写
        detail_prompts = [
            f"产品摄影特写：高端商务笔记本电脑键盘区域，RGB背光，全尺寸键盘带数字小键盘，{product_description}，高质量，专业打光，白色简约背景，8K高清",
            f"产品摄影特写：高端商务笔记本电脑侧面散热口和接口展示，USB-C，HDMI，耳机孔等，{product_description}，高质量，专业打光，白色简约背景，8K高清"
        ]
        
        for i in range(1, detail_images_count + 1):
            print(f"\n生成详情图 {i}/{detail_images_count}...")
            # 使用预定义的详情图提示词
            if i <= len(detail_prompts):
                prompt = detail_prompts[i-1]
            else:
                prompt = f"产品摄影特写：高端商务笔记本电脑细节{i}，{product_description}，高质量，专业打光，白色简约背景，8K高清"
            
            # 生成图片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detail_{timestamp}_{i}.jpg"
            filepath = os.path.join(image_save_dir, filename)
            
            try:
                # 调用API生成图片
                try:
                    # 调用generate_product_images方法生成一张图片
                    paths = generator.generate_product_images(
                        product_description=prompt,
                        count=1,
                        image_type="detail",
                        save_dir=image_save_dir
                    )
                    
                    if paths:
                        # 获取生成的图片路径
                        generated_path = paths[0]
                        print(f"✅ 详情图{i}生成成功: {generated_path}")
                        if os.path.exists(generated_path):
                            file_size = os.path.getsize(generated_path)
                            print(f"  文件大小: {file_size / 1024 / 1024:.2f} MB")
                        detail_images.append(generated_path)
                    else:
                        print(f"❌ 详情图{i}生成失败: 返回空路径列表")
                except Exception as e:
                    print(f"❌ 详情图{i}API调用失败: {str(e)}")
            except Exception as e:
                print(f"❌ 详情图{i}生成过程中出错: {str(e)}")
        
        detail_total_time = time.time() - start_time
        print(f"\n详情图生成完成，耗时: {detail_total_time:.2f}秒")
        print(f"成功生成: {len(detail_images)}张详情图")
        
        # 生成摘要报告
        print("\n===== 测试结果摘要 =====")
        print(f"总耗时: {(main_total_time + detail_total_time):.2f}秒")
        print(f"成功生成图片总数: {len(main_images) + len(detail_images)}张")
        print(f"主图: {len(main_images)}/{main_images_count}张")
        for i, path in enumerate(main_images, 1):
            if os.path.exists(path):
                size_mb = os.path.getsize(path) / 1024 / 1024
                print(f"  主图{i}: {os.path.basename(path)} ({size_mb:.2f} MB)")
            else:
                print(f"  主图{i}: {os.path.basename(path)} (⚠️ 文件不存在)")
        
        print(f"详情图: {len(detail_images)}/{detail_images_count}张")
        for i, path in enumerate(detail_images, 1):
            if os.path.exists(path):
                size_mb = os.path.getsize(path) / 1024 / 1024
                print(f"  详情图{i}: {os.path.basename(path)} ({size_mb:.2f} MB)")
            else:
                print(f"  详情图{i}: {os.path.basename(path)} (⚠️ 文件不存在)")
        
        # 保存测试结果
        results = {
            "test_time": datetime.now().isoformat(),
            "total_time_seconds": main_total_time + detail_total_time,
            "main_images_count": main_images_count,
            "detail_images_count": detail_images_count,
            "successful_main_images": main_images,
            "successful_detail_images": detail_images,
            "product_description": product_description
        }
        
        with open('test_image_generation_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试结果已保存到: test_image_generation_results.json")
        print("\n✅ 图片生成测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
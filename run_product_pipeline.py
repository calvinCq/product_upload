#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商品生成和上传流程入口脚本
用于生成商品并上传到微信小店
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from src.core.product_generator import generate_products, ProductGenerator
from src.core.product_uploader import ProductUploader
from src.utils.logger import log_message
from src.api.wechat_shop_api import save_products_to_csv, load_products_from_csv

def generate_product_from_file():
    """
    从sample_product_description.txt生成商品，确保生成真实图片
    """
    try:
        # 读取详细的课程描述
        def read_sample_description(file_path="sample_product_description.txt"):
            """读取并解析样本描述文件"""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                product_desc = {}
                # 提取标题
                if "# 课程标题" in content:
                    title_part = content.split("# 课程标题")[1].split("#", 1)[0].strip()
                    product_desc['course_name'] = title_part
                
                # 提取讲师简介
                if "## 讲师简介" in content:
                    teacher_part = content.split("## 讲师简介")[1].split("##", 1)[0].strip()
                    # 尝试提取讲师姓名
                    teacher_name = '专业讲师'
                    for line in teacher_part.split('\n'):
                        if line.startswith('讲师：') or line.startswith('讲师:'):
                            teacher_name = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
                            break
                    product_desc['teacher_info'] = {'name': teacher_name, 'description': teacher_part}
                
                # 提取课程大纲
                if "## 课程大纲" in content:
                    outline_part = content.split("## 课程大纲")[1].split("##", 1)[0].strip()
                    product_desc['course_outline'] = outline_part
                
                # 提取适用人群
                if "## 适用人群" in content:
                    audience_part = content.split("## 适用人群")[1].split("##", 1)[0].strip()
                    product_desc['target_audience'] = audience_part
                
                # 提取学完收获
                if "## 学完收获" in content:
                    outcomes_part = content.split("## 学完收获")[1].strip()
                    product_desc['learning_outcomes'] = outcomes_part
                
                # 添加必要的基础字段
                product_desc['product_type'] = 'education'
                product_desc['brand'] = '优质教育'
                product_desc['category'] = '教育培训'
                
                return product_desc
            except Exception as e:
                log_message(f"读取样本描述文件失败: {str(e)}", "ERROR")
                return {'course_name': '精品课程'}
        
        # 获取详细的课程描述数据
        sample_client_data = read_sample_description()
        course_name = sample_client_data.get('course_name', '精品课程')
        log_message(f"开始生成商品数据... 课程名称: {course_name}")
        
        # 生成单个商品
        generator = ProductGenerator()
        
        # 先生成图片进行验证
        log_message("验证图片生成功能...")
        try:
            # 生成3张图片进行测试
            images = generator.generate_product_images(sample_client_data, image_count=3)
            
            # 检查是否有占位图或无效图片
            def is_valid_image_url(url):
                """验证图片URL是否有效"""
                return url and not url.startswith("https://example.com") and url.startswith("http")
            
            invalid_images = [img for img in images if not is_valid_image_url(img)]
            if invalid_images:
                log_message(f"警告: 检测到{len(invalid_images)}张无效图片，图片生成可能失败", "WARNING")
                print(f"警告: 图片生成可能失败，检测到无效图片: {invalid_images[0]}")
                # 尝试重新生成
                print("尝试重新生成图片...")
                images = generator.generate_product_images(sample_client_data, image_count=3)
                invalid_images = [img for img in images if not is_valid_image_url(img)]
                if invalid_images:
                    raise Exception(f"图片生成失败，仍然存在无效图片")
            
            log_message(f"成功生成3张测试图片")
            print(f"成功生成3张测试图片: {images[0]}")
            
        except Exception as img_error:
            log_message(f"图片生成测试失败: {str(img_error)}", "ERROR")
            print(f"图片生成测试失败: {str(img_error)}")
            print("请检查钱多多API配置和网络连接")
            return None
        
        # 生成完整商品
        print("开始生成完整商品信息...")
        product = generator.generate_product(sample_client_data)
        
        if product:
            log_message(f"生成成功: {product['title']}")
            log_message(f"生成时间: {product.get('generation_time', 'N/A')}")
            log_message(f"价格: {product['skus'][0]['price']/100}元")
            
            # 验证所有图片是否为真实图片
            all_images = []
            if 'head_imgs' in product:
                all_images.extend(product['head_imgs'])
            if 'image_info' in product and 'images' in product['image_info']:
                all_images.extend(product['image_info']['images'])
            if 'desc_info' in product and 'imgs' in product['desc_info']:
                all_images.extend(product['desc_info']['imgs'])
            
            # 严格验证图片URL
            invalid_count = sum(1 for img in all_images if not is_valid_image_url(img))
            
            if invalid_count > 0:
                log_message(f"错误: 检测到{invalid_count}张无效图片", "ERROR")
                print(f"错误: 检测到{invalid_count}张无效图片，图片生成失败")
                # 打印无效图片URLs以便调试
                for img in all_images[:5]:  # 只打印前5个用于调试
                    if not is_valid_image_url(img):
                        print(f"  - 无效图片: {img}")
                return None
            else:
                log_message(f"所有{len(all_images)}张图片均为真实有效图片")
                print(f"成功: 所有{len(all_images)}张图片均为真实有效图片")
            
            log_message(f"主图数量: {len(product.get('head_imgs', []))}")
            log_message(f"描述图片数量: {len(product.get('desc_info', {}).get('imgs', []))}")
        else:
            log_message("商品生成失败", "ERROR")
            return None
        
        # 保存到文件
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"generated_product_{timestamp}.json")
        generator.save_products_to_file([product], output_file)
        
        # 同时保存为CSV格式
        csv_file = os.path.join(output_dir, f"generated_product_{timestamp}.csv")
        save_products_to_csv([product], csv_file)
        
        log_message(f"商品已保存到 {output_file} 和 {csv_file}")
        log_message(f"描述和图片URL已保存到 {os.path.splitext(output_file)[0]}_descriptions_images.json")
        
        print(f"商品生成成功，已保存到:")
        print(f"- JSON格式: {output_file}")
        print(f"- CSV格式: {csv_file}")
        return output_file
        
    except Exception as e:
        log_message(f"生成商品时发生错误: {str(e)}", "ERROR")
        print(f"生成商品时发生错误: {str(e)}")
        return None

def upload_product_from_file(file_path):
    """
    从文件上传商品，确保图片正确有效
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            log_message(f"文件不存在: {file_path}", "ERROR")
            print(f"错误: 文件不存在: {file_path}")
            return None
        
        # 读取商品数据
        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # 确保products是列表
        if isinstance(products, dict):
            products = [products]
        
        log_message(f"准备上传{len(products)}个商品...")
        print(f"准备上传{len(products)}个商品...")
        
        # 严格检查所有商品的图片是否有效
        def is_valid_image_url(url):
            """验证图片URL是否有效"""
            return url and not url.startswith("https://example.com") and url.startswith("http")
        
        has_invalid_images = False
        for i, product in enumerate(products):
            all_images = []
            # 收集所有图片URL
            if 'head_imgs' in product:
                all_images.extend(product['head_imgs'])
            if 'image_info' in product and 'images' in product['image_info']:
                all_images.extend(product['image_info']['images'])
            if 'desc_info' in product and 'imgs' in product['desc_info']:
                all_images.extend(product['desc_info']['imgs'])
            
            invalid_count = sum(1 for img in all_images if not is_valid_image_url(img))
            if invalid_count > 0:
                has_invalid_images = True
                log_message(f"错误: 商品{i+1}包含{invalid_count}张无效图片", "ERROR")
                print(f"错误: 商品{i+1}({product.get('title', '未知')})包含{invalid_count}张无效图片")
                
                # 显示无效图片示例
                for img in all_images[:5]:  # 只显示前5个无效图片
                    if not is_valid_image_url(img):
                        print(f"  - 无效图片: {img}")
                
                # 不允许上传包含无效图片的商品
                print("包含无效图片的商品不允许上传，请先重新生成商品")
                return None
        
        if not has_invalid_images:
            print("✓ 所有商品图片验证通过")
        
        # 创建上传器并上传
        print("初始化上传器...")
        uploader = ProductUploader()
        
        # 测试连接
        log_message("测试微信小店API连接...")
        print("测试微信小店API连接...")
        try:
            if not uploader.test_connection():
                log_message("连接失败，请检查API配置", "ERROR")
                print("错误: 连接微信小店API失败")
                print("请检查以下事项:")
                print("1. .env文件中的WECHAT_APPID和WECHAT_APPSECRET配置是否正确")
                print("2. 网络连接是否正常")
                print("3. 微信小店API是否可用")
                return None
            else:
                print("✓ 连接测试成功!")
        except Exception as conn_error:
            log_message(f"连接测试异常: {str(conn_error)}", "ERROR")
            print(f"错误: 连接测试异常: {str(conn_error)}")
            return None
        
        # 上传商品
        log_message("开始上传商品...")
        print("开始上传商品到微信小店...")
        try:
            results = uploader.upload_products(products)
            
            if not results:
                raise Exception("上传结果为空")
            
            # 保存上传结果
            uploader.save_upload_results(results)
            
            # 生成报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join("output", f"upload_report_{timestamp}.txt")
            report_content = uploader.generate_upload_report(results, report_file)
            
            log_message(f"上传完成，成功率: {results.get('success_rate', 0)}%")
            
            # 显示上传结果摘要
            success_count = results.get('success', 0)
            failed_count = results.get('failed', 0)
            success_rate = results.get('success_rate', 0)
            
            print(f"\n===== 上传结果摘要 =====")
            print(f"成功上传: {success_count}个商品")
            print(f"上传失败: {failed_count}个商品")
            print(f"成功率: {success_rate}%")
            print(f"详细报告已保存到: {report_file}")
            
            # 如果有失败，显示失败原因
            if failed_count > 0 and 'failed_products' in results:
                print(f"\n失败商品原因示例:")
                for i, fail_info in enumerate(results['failed_products'][:3]):  # 只显示前3个失败原因
                    print(f"商品 {i+1}: {fail_info.get('error', '未知错误')}")
            
            return results
            
        except Exception as upload_error:
            log_message(f"上传商品异常: {str(upload_error)}", "ERROR")
            print(f"错误: 上传商品异常: {str(upload_error)}")
            return None
        
    except Exception as e:
        log_message(f"上传商品时发生错误: {str(e)}", "ERROR")
        print(f"错误: 上传商品时发生错误: {str(e)}")
        return None

def upload_product_from_csv(csv_file):
    """
    从CSV文件上传商品
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(csv_file):
            log_message(f"CSV文件不存在: {csv_file}", "ERROR")
            print(f"错误: CSV文件不存在: {csv_file}")
            return None
        
        # 从CSV加载商品数据
        print(f"从CSV文件加载商品数据: {csv_file}")
        products = load_products_from_csv(csv_file)
        
        if not products:
            print("错误: 未能从CSV文件加载商品数据")
            return None
        
        print(f"成功加载{len(products)}个商品")
        
        # 验证图片URL
        def is_valid_image_url(url):
            """验证图片URL是否有效"""
            return url and not url.startswith("https://example.com") and url.startswith("http")
        
        has_invalid_images = False
        for i, product in enumerate(products):
            all_images = []
            if 'head_imgs' in product:
                all_images.extend(product['head_imgs'])
            if 'desc_info' in product and 'imgs' in product['desc_info']:
                all_images.extend(product['desc_info']['imgs'])
            
            invalid_count = sum(1 for img in all_images if not is_valid_image_url(img))
            if invalid_count > 0:
                has_invalid_images = True
                print(f"错误: 商品{i+1}({product.get('title', '未知')})包含{invalid_count}张无效图片")
                return None
        
        if not has_invalid_images:
            print("✓ 所有商品图片验证通过")
        
        # 创建上传器并上传
        print("初始化上传器...")
        
        # 初始化上传器
        try:
            uploader = ProductUploader()
        except Exception as init_error:
            log_message(f"上传器初始化失败: {str(init_error)}", "ERROR")
            print(f"错误: 上传器初始化失败: {str(init_error)}")
            return None
        
        # 测试连接
        log_message("测试微信小店API连接...")
        print("测试微信小店API连接...")
        try:
            if not uploader.test_connection():
                log_message("连接失败，请检查API配置", "ERROR")
                print("错误: 连接微信小店API失败")
                print("请检查以下事项:")
                print("1. .env文件中的WECHAT_APPID和WECHAT_APPSECRET配置是否正确")
                print("2. 网络连接是否正常")
                print("3. 微信小店API是否可用")
                return None
            else:
                print("✓ 连接测试成功!")
        except Exception as conn_error:
            log_message(f"连接测试异常: {str(conn_error)}", "ERROR")
            print(f"错误: 连接测试异常: {str(conn_error)}")
            return None
        
        # 上传商品
        log_message("开始上传商品...")
        print("开始上传商品到微信小店...")
        try:
            results = uploader.upload_products(products)
            
            if not results:
                raise Exception("上传结果为空")
            
            # 保存上传结果
            uploader.save_upload_results(results)
            
            # 生成报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join("output", f"upload_report_csv_{timestamp}.txt")
            report_content = uploader.generate_upload_report(results, report_file)
            
            log_message(f"上传完成，成功率: {results.get('success_rate', 0)}%")
            
            # 显示上传结果摘要
            success_count = results.get('success', 0)
            failed_count = results.get('failed', 0)
            success_rate = results.get('success_rate', 0)
            
            print(f"\n===== 上传结果摘要 =====")
            print(f"成功上传: {success_count}个商品")
            print(f"上传失败: {failed_count}个商品")
            print(f"成功率: {success_rate}%")
            print(f"详细报告已保存到: {report_file}")
            
            # 如果有失败，显示失败原因
            if failed_count > 0 and 'failed_products' in results:
                print(f"\n失败商品原因示例:")
                for i, fail_info in enumerate(results['failed_products'][:3]):  # 只显示前3个失败原因
                    print(f"商品 {i+1}: {fail_info.get('error', '未知错误')}")
            
            return results
            
        except Exception as upload_error:
            log_message(f"上传商品异常: {str(upload_error)}", "ERROR")
            print(f"错误: 上传商品异常: {str(upload_error)}")
            return None
        
    except Exception as e:
        log_message(f"从CSV上传商品时发生错误: {str(e)}", "ERROR")
        print(f"错误: 从CSV上传商品时发生错误: {str(e)}")
        return None

def main():
    """
    主函数，执行商品生成和上传流程
    """
    print("===== 商品生成与上传流程 =====")
    
    # 步骤1: 选择操作模式
    print("\n步骤1: 选择操作模式")
    print("1. 生成新商品并上传")
    print("2. 直接上传已有商品")
    
    mode_choice = input("请选择操作模式 (1/2): ")
    
    product_file = None
    
    if mode_choice == '1':
        # 生成新商品
        print("\n开始从sample_product_description.txt生成商品...")
        product_file = generate_product_from_file()
        
        if not product_file:
            print("商品生成失败，程序终止")
            return
    
    # 步骤2: 上传商品
    if mode_choice == '2' or (mode_choice == '1' and product_file):
        print("\n步骤2: 商品上传")
        
        if mode_choice == '2':
            # 直接上传模式，提供更多选项
            print("1. 指定JSON文件路径上传")
            print("2. 指定CSV文件路径上传")
            print("3. 使用最新生成的CSV文件上传")
            print("4. 跳过上传")
            
            upload_choice = input("请选择上传方式 (1/2/3/4): ")
            
            if upload_choice == '1':
                json_path = input("请输入JSON文件路径: ")
                print(f"\n开始从指定JSON文件上传商品: {json_path}")
                results = upload_product_from_file(json_path)
                
                if results:
                    print(f"\n上传成功: {results.get('success', 0)}个商品")
                    print(f"上传失败: {results.get('failed', 0)}个商品")
                    print(f"成功率: {results.get('success_rate', 0)}%")
                else:
                    print("上传失败")
                return
            
            elif upload_choice == '2':
                csv_path = input("请输入CSV文件路径: ")
                print(f"\n开始从指定CSV文件上传商品: {csv_path}")
                results = upload_product_from_csv(csv_path)
                
                if results:
                    print(f"\n上传成功: {results.get('success', 0)}个商品")
                    print(f"上传失败: {results.get('failed', 0)}个商品")
                    print(f"成功率: {results.get('success_rate', 0)}%")
                else:
                    print("上传失败")
                return
            
            elif upload_choice == '3':
                # 查找最新的CSV文件
                output_dir = "output"
                if not os.path.exists(output_dir):
                    print("错误: output目录不存在")
                    return
                
                csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
                if not csv_files:
                    print("错误: output目录中没有CSV文件")
                    return
                
                # 按文件名排序，获取最新的文件
                csv_files.sort(reverse=True)
                latest_csv = os.path.join(output_dir, csv_files[0])
                
                print(f"\n找到最新的CSV文件: {latest_csv}")
                confirm = input("是否使用此文件上传? (y/n): ")
                
                if confirm.lower() == 'y':
                    print(f"\n开始从CSV文件上传商品: {latest_csv}")
                    results = upload_product_from_csv(latest_csv)
                    
                    if results:
                        print(f"\n上传成功: {results.get('success', 0)}个商品")
                        print(f"上传失败: {results.get('failed', 0)}个商品")
                        print(f"成功率: {results.get('success_rate', 0)}%")
                    else:
                        print("上传失败")
                else:
                    print("已取消上传")
                return
            
            elif upload_choice == '4':
                print("已跳过商品上传步骤")
                return
            
            else:
                print("无效的选择，已跳过上传步骤")
                return
        
        # 生成模式下的上传选项
        print("1. 从生成的JSON文件上传")
        print("2. 从CSV文件上传")
        print("3. 跳过上传")
        
        choice = input("请选择上传方式 (1/2/3): ")
    
    # 只有在生成模式下才执行原始的上传逻辑
    if mode_choice == '1':
        if choice == '1':
            print("\n开始从JSON文件上传商品...")
            results = upload_product_from_file(product_file)
        
            if results:
                print(f"\n上传成功: {results.get('success', 0)}个商品")
                print(f"上传失败: {results.get('failed', 0)}个商品")
                print(f"成功率: {results.get('success_rate', 0)}%")
            else:
                print("上传失败")
    
        elif choice == '2':
            # 自动查找同名CSV文件
            csv_file = product_file.replace('.json', '.csv')
            if not os.path.exists(csv_file):
                csv_file = input("请输入CSV文件路径: ")
        
            print(f"\n开始从CSV文件上传商品: {csv_file}")
            results = upload_product_from_csv(csv_file)
        
            if results:
                print(f"\n上传成功: {results.get('success', 0)}个商品")
                print(f"上传失败: {results.get('failed', 0)}个商品")
                print(f"成功率: {results.get('success_rate', 0)}%")
            else:
                print("上传失败")
    
        elif choice == '3':
            print("已跳过商品上传步骤")
        
        else:
            print("无效的选择，已跳过上传步骤")
    
    print("\n===== 流程完成 =====")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信小店商品API上传工具
通过微信小店API直接进行商品上传和店铺信息管理
"""

import os
import json
import random
import time
from datetime import datetime

# 导入API客户端
from wechat_shop_api import (
    WeChatShopAPIClient,
    save_products_to_csv,
    log_message,
    WECHAT_SHOP_REQUIRED_FIELDS
)

# 定义必要的目录和文件
LOG_DIR = "logs"
OUTPUT_DIR = "output"
CONFIG_FILE = "wechat_api_config.json"

# 商品测试数据生成相关常量
PRODUCT_CATEGORIES = [
    {"id": 101, "name": "服装配饰"},
    {"id": 102, "name": "美妆护肤"},
    {"id": 103, "name": "食品饮料"},
    {"id": 104, "name": "家居日用"},
    {"id": 105, "name": "电子产品"},
    {"id": 106, "name": "运动户外"},
    {"id": 107, "name": "图书文具"},
    {"id": 108, "name": "玩具乐器"}
]
BRANDS = ["品牌A", "品牌B", "品牌C", "品牌D", "品牌E", "品牌F", "品牌G", "品牌H"]
COLORS = ["红色", "蓝色", "绿色", "黑色", "白色", "粉色", "黄色", "紫色"]
SIZES = ["XS", "S", "M", "L", "XL", "XXL", "均码", "定制"]


def generate_test_products(num=10):
    """
    生成测试商品数据
    :param num: 生成数量，默认10个
    :return: 商品数据列表
    """
    products = []
    
    for i in range(1, num + 1):
        # 随机选择分类
        category = random.choice(PRODUCT_CATEGORIES)
        
        # 生成商品ID（实际应该由微信返回，但这里先生成临时ID）
        product_id = f"test_product_{int(time.time())}_{i}"
        
        # 生成随机商品名称
        product_name = f"{random.choice(BRANDS)} {category['name']} 测试商品{i}"
        
        # 随机生成价格（单位：分）
        original_price = random.randint(100, 999900)
        price = int(original_price * random.uniform(0.7, 0.95))  # 折扣价格
        
        # 生成随机SKU列表
        sku_list = []
        for color in random.sample(COLORS, random.randint(1, 4)):
            for size in random.sample(SIZES, random.randint(1, 3)):
                sku_list.append({
                    "properties": [f"颜色:{color}", f"尺码:{size}"],
                    "sku_id": f"{product_id}_sku_{color}_{size}",
                    "price": price,
                    "original_price": original_price,
                    "stock": random.randint(10, 100),
                    "sku_img": f"test_image_{color}_{size}.jpg"  # 占位图，实际需要上传真实图片
                })
        
        # 商品属性
        attributes = [
            {"name": "品牌", "value": random.choice(BRANDS)},
            {"name": "产地", "value": "中国"},
            {"name": "材质", "value": "高品质材料"},
            {"name": "重量", "value": f"{random.randint(100, 1000)}g"}
        ]
        
        # 构建商品数据
        product = {
            "product_id": product_id,
            "product_name": product_name,
            "category_id": category["id"],
            "main_image": "test_main_image.jpg",  # 占位图，实际需要上传真实图片
            "image_list": ["test_image1.jpg", "test_image2.jpg"],  # 占位图，实际需要上传真实图片
            "price": price,
            "original_price": original_price,
            "product_desc": f"这是一个{product_name}的详细描述。\n\n产品特点：\n1. 高品质材料\n2. 精工制作\n3. 时尚设计\n4. 舒适耐用",
            "sku_list": sku_list,
            "attributes": attributes,
            "product_status": 1  # 1表示上架，0表示下架
        }
        
        products.append(product)
    
    return products


def load_config(config_file=CONFIG_FILE):
    """
    从配置文件加载API配置
    :param config_file: 配置文件路径
    :return: 配置字典
    """
    if not os.path.exists(config_file):
        log_message(f"配置文件不存在: {config_file}", "WARNING")
        log_message("将创建默认配置文件模板，请根据实际情况修改", "INFO")
        
        # 创建默认配置文件
        default_config = {
            "appid": "你的公众号AppID",
            "appsecret": "你的公众号AppSecret",
            "api_base_url": "https://api.weixin.qq.com",
            "timeout": 30
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        log_message(f"成功加载配置文件: {config_file}")
        return config
    except Exception as e:
        log_message(f"加载配置文件失败: {str(e)}", "ERROR")
        return {}


def check_api_config(config):
    """
    检查API配置是否有效
    :param config: 配置字典
    :return: 是否有效
    """
    required_fields = ["appid", "appsecret"]
    for field in required_fields:
        if field not in config or not config[field] or config[field].startswith("你的"):
            log_message(f"配置无效: {field} 未设置或使用默认值", "ERROR")
            return False
    return True


def display_product_fields():
    """
    显示微信小店商品所需字段信息
    """
    print("\n微信小店商品所需字段说明：")
    print("-" * 60)
    
    field_descriptions = {
        "product_id": "商品ID（由微信生成，创建时为临时ID）",
        "product_name": "商品名称",
        "category_id": "商品分类ID",
        "main_image": "商品主图URL",
        "image_list": "商品图片列表",
        "price": "商品价格（单位：分）",
        "original_price": "商品原价（单位：分）",
        "product_desc": "商品描述",
        "sku_list": "SKU列表",
        "attributes": "商品属性列表",
        "product_status": "商品状态（1:上架，0:下架）"
    }
    
    for field in WECHAT_SHOP_REQUIRED_FIELDS:
        desc = field_descriptions.get(field, "")
        print(f"{field}: {desc}")
    
    print("-" * 60)
    print("注意：实际使用时需要先上传商品图片获取URL\n")


def main():
    """
    主函数，执行微信小店商品API上传流程
    """
    # 确保必要目录存在
    for directory in [LOG_DIR, OUTPUT_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    print("=============================================")
    print("微信小店商品API上传工具")
    print("=============================================")
    print(f"日志目录: {LOG_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"配置文件: {CONFIG_FILE}")
    print("=============================================")
    
    try:
        # 加载配置
        config = load_config()
        
        # 检查API配置
        api_config_valid = check_api_config(config)
        
        # 显示商品字段明细
        print("\n[1] 显示微信小店商品字段明细...")
        display_product_fields()
        log_message("已显示微信小店商品字段明细")
        
        # 生成测试数据
        print("\n[2] 生成测试商品数据...")
        num_products = int(input("请输入生成商品数量 (默认5): ") or "5")
        products = generate_test_products(num_products)
        print(f"已生成 {len(products)} 条测试商品数据")
        log_message(f"已生成 {len(products)} 条测试商品数据")
        
        # 保存到CSV文件
        print("\n[3] 保存商品数据到CSV文件...")
        csv_file = os.path.join(OUTPUT_DIR, f"wechat_shop_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        save_products_to_csv(products, csv_file)
        print(f"商品数据已保存到: {csv_file}")
        log_message(f"商品数据已保存到: {csv_file}")
        
        # 检查是否继续执行API操作
        if not api_config_valid:
            print("\n⚠️  警告：API配置无效，无法执行API操作")
            print("请先修改配置文件中的AppID和AppSecret")
            print("\n操作已完成！")
            return
        
        # 确认是否继续执行API操作
        proceed = input("\n是否继续执行API操作流程？(y/n): ")
        if proceed.lower() != 'y':
            print("操作已取消，感谢使用！")
            log_message("用户取消执行API操作流程")
            return
        
        # 初始化API客户端
        print("\n[4] 初始化微信小店API客户端...")
        api_client = WeChatShopAPIClient(
            appid=config["appid"],
            appsecret=config["appsecret"],
            api_config=config
        )
        log_message("已初始化微信小店API客户端")
        
        # 获取店铺信息
        print("\n[5] 获取店铺信息...")
        shop_info_result = api_client.get_shop_info()
        if shop_info_result.get("success", False):
            print("✅ 成功获取店铺信息")
            shop_info = shop_info_result.get("data", {})
            print("店铺基本信息:")
            for key, value in shop_info.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ 获取店铺信息失败: {shop_info_result.get('error', '未知错误')}")
            log_message(f"获取店铺信息失败: {shop_info_result.get('error', '未知错误')}", "ERROR")
        
        # 批量上传商品
        print("\n[6] 批量上传商品...")
        print("注意：在实际使用前，请确保已替换测试图片路径为有效的图片URL")
        
        # 确认是否执行上传
        confirm_upload = input("\n是否执行商品上传操作？(y/n): ")
        if confirm_upload.lower() == 'y':
            log_message("开始执行批量上传商品")
            
            # 使用API客户端执行批量上传操作
            report = api_client.batch_upload_products_from_data(products)
            
            print(f"✅ 上传操作完成")
            print(f"   总计: {report.get('total', 0)} 个商品")
            print(f"   成功: {report.get('success_count', 0)} 个商品")
            print(f"   失败: {report.get('error_count', 0)} 个商品")
            log_message(f"批量上传完成，总计{report.get('total', 0)}个商品，成功{report.get('success_count', 0)}个，失败{report.get('error_count', 0)}个")
            
            # 验证上传结果
            print("\n[7] 验证上传结果...")
            verify_result = api_client.verify_upload_result()
            if verify_result.get("success", False):
                print("✅ 验证完成")
                print(f"   验证时间: {verify_result['verification_time']}")
                print(f"   总商品数: {verify_result['total_products']}")
                print(f"   成功上传: {verify_result['successfully_uploaded']}")
                print(f"   上传失败: {verify_result['failed_uploads']}")
            else:
                print(f"❌ 验证失败: {verify_result.get('error', '未知错误')}")
        
        # 操作完成
        print("\n=============================================")
        print("🎉 微信小店商品API上传操作已完成！")
        print("=============================================")
        log_message("微信小店商品API上传操作已完成", "SUCCESS")
        
        # 保存操作历史
        history_file = os.path.join(OUTPUT_DIR, f"operation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(api_client.get_operation_history(), f, ensure_ascii=False, indent=4)
            print(f"操作历史已保存到: {history_file}")
        except Exception as e:
            print(f"保存操作历史失败: {str(e)}")
            
    except KeyboardInterrupt:
        print("\n操作已被用户中断")
        log_message("操作被用户中断", "INFO")
    except Exception as e:
        print(f"\n操作过程中发生错误: {str(e)}")
        log_message(f"主函数执行失败: {str(e)}", "ERROR")
    finally:
        print("\n感谢使用微信小店商品API上传工具！")


if __name__ == "__main__":
    # 显示使用说明
    print("""
    =============================================
              微信小店商品API上传工具
    =============================================
    工具说明:
    1. 本工具通过微信小店API直接进行商品上传和店铺信息管理
    2. 支持生成测试商品数据、保存到CSV、批量上传和结果验证
    3. 完整日志记录在日志目录下
    4. 配置信息保存在wechat_api_config.json文件中
    
    API操作优势:
    - 直接通过微信官方API操作，稳定性高
    - 支持自动化批量操作，效率更高
    - 提供完整的错误处理和验证机制
    - 可执行实际的商品上传操作
    
    使用步骤:
    1. 确保已配置正确的微信公众号AppID和AppSecret
    2. 运行程序，查看商品字段明细
    3. 生成测试数据并保存为CSV文件
    4. 选择执行API操作流程
    5. 查看操作结果、日志和操作历史
    
    配置说明:
    - 配置文件: wechat_api_config.json
    - appid: 微信公众号AppID
    - appsecret: 微信公众号AppSecret
    - api_base_url: 微信API基础URL（一般不需要修改）
    - timeout: API调用超时时间（秒）
    
    注意事项:
    - 请确保公众号已开通微信小店功能
    - 实际使用时需要先上传商品图片获取URL
    - 所有操作都会记录详细日志和操作历史
    - 操作过程中可随时按Ctrl+C中断程序
    =============================================
    """)
    
    # 执行主函数
    main()
    
    print("\n操作完成！")
    print("提示：")
    print("1. 查看日志文件了解详细执行过程: logs目录下的日志文件")
    print("2. 查看生成的商品数据文件: output目录下的CSV文件")
    print("3. 操作历史记录保存在output目录下的JSON文件中")
    print("4. 若要使用真实API，请确保在配置文件中设置正确的AppID和AppSecret")
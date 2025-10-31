#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试商品上传功能
使用模拟商品数据直接测试上传功能
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.product_uploader import ProductUploader
from src.utils.logger import log_message

def test_upload_product():
    """测试上传单个商品"""
    log_message("===== 开始测试商品上传 =====")
    
    try:
        # 初始化上传器
        uploader = ProductUploader()
        
        # 测试连接
        log_message("测试API连接...")
        if not uploader.test_connection():
            log_message("API连接测试失败，无法继续上传", "ERROR")
            return False
        log_message("API连接测试成功")
        
        # 准备测试商品数据（包含所有必填字段）
        test_product = {
            # 匹配ProductUploader的验证字段
            "title": "测试商品" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "price": 99.99,
            "head_imgs": [
                "https://via.placeholder.com/800x800",
                "https://via.placeholder.com/800x800"
            ],  # 主图列表
            "cats": [{"third_cat_id": 10001}],  # cats也需要是对象列表格式
            
            # 匹配WeChatShopAPIClient的验证字段
            "product_name": "测试商品" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "category_id": {"third_cat_id": 10001},  # category_id需要是对象格式
            "main_image": "https://via.placeholder.com/800x800",
            "image_list": [
                "https://via.placeholder.com/800x800",
                "https://via.placeholder.com/800x800"
            ],
            "original_price": 199.99,
            "product_desc": "这是一个用于测试的商品描述。\n包含多行文本。",
            "sku_list": [{"price": 99.99, "stock": 100, "sku_id": 1}],
            "attributes": [{"name": "测试属性", "value": "测试值"}],
            "product_status": 1  # 商品状态: 1-上架, 0-下架
        }
        
        log_message(f"准备上传测试商品: {test_product['title']}")
        
        # 验证商品数据
        is_valid = uploader._validate_product_data(test_product)
        if not is_valid:
            log_message("商品数据验证失败，无法继续上传", "ERROR")
            return False
        log_message("商品数据验证通过")
        
        # 尝试上传商品
        log_message("开始上传商品...")
        success, result = uploader.upload_single_product(test_product)
        
        if success:
            product_id = result.get('product_id', '未知')
            log_message(f"商品上传成功！商品ID: {product_id}")
            return True
        else:
            error_msg = result.get("error", "未知错误") if isinstance(result, dict) else "上传失败"
            log_message(f"商品上传失败: {error_msg}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"测试过程中发生异常: {str(e)}", "ERROR")
        return False
    finally:
        log_message("===== 商品上传测试结束 =====")

if __name__ == "__main__":
    test_upload_product()
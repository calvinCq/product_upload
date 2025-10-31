#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商品生成模块
负责根据配置自动生成符合微信小店API要求的商品数据
"""

import random
import time
from datetime import datetime
import json

# 导入现有的日志功能
from wechat_shop_api import log_message


class ProductGenerator:
    """
    商品生成器类
    负责生成符合微信小店API要求的商品数据
    """
    
    def __init__(self, config):
        """
        初始化商品生成器
        
        :param config: 生成配置字典
        """
        self.config = config
        self.product_counter = 0
        self._validate_config()
    
    def _validate_config(self):
        """
        验证生成配置的有效性
        """
        # 确保必需的配置项存在
        required_fields = ['category_ids', 'price_range', 'stock_range']
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                log_message(f"警告：生成配置缺少必需项 {field}，使用默认值", "WARNING")
        
        # 设置默认值
        if 'title_templates' not in self.config or not self.config['title_templates']:
            self.config['title_templates'] = ["商品{id}"]
        
        if 'keywords' not in self.config or not self.config['keywords']:
            self.config['keywords'] = ["商品"]
        
        if 'description_templates' not in self.config or not self.config['description_templates']:
            self.config['description_templates'] = ["这是一个商品描述"]
        
        if 'main_images' not in self.config or len(self.config['main_images']) < 3:
            self.config['main_images'] = [
                "https://example.com/product1.jpg",
                "https://example.com/product2.jpg",
                "https://example.com/product3.jpg"
            ]
        
        if 'detail_images' not in self.config or not self.config['detail_images']:
            self.config['detail_images'] = ["https://example.com/detail1.jpg"]
        
        if 'deliver_method' not in self.config:
            self.config['deliver_method'] = 0
    
    def generate_single_product(self):
        """
        生成单个商品信息
        
        :return: 商品数据字典
        """
        try:
            self.product_counter += 1
            product_id = f"PROD_{int(time.time())}_{self.product_counter}"
            
            # 随机选择类目
            category = random.choice(self.config.get('category_ids', [{'level1': '1', 'level2': '2', 'level3': '3'}]))
            
            # 生成商品标题
            title = self._generate_title()
            
            # 生成价格和库存
            price_range = self.config.get('price_range', [100, 9999])
            price = random.randint(price_range[0], price_range[1])
            
            stock_range = self.config.get('stock_range', [10, 1000])
            stock = random.randint(stock_range[0], stock_range[1])
            
            # 生成商品描述
            description = self._generate_description()
            
            # 构建商品数据
            product = {
                "title": title,
                "sub_title": self._generate_subtitle(title),
                "short_title": self._generate_short_title(title),
                "desc_info": {
                    "imgs": self._get_detail_images(),
                    "desc": description
                },
                "head_imgs": self._get_main_images(),
                "deliver_method": self.config.get('deliver_method', 0),
                "cats": [
                    {"cat_id": category['level1']},
                    {"cat_id": category['level2']},
                    {"cat_id": category['level3']}
                ],
                "cats_v2": [
                    {"cat_id": category['level1']},
                    {"cat_id": category['level2']},
                    {"cat_id": category['level3']}
                ],
                "extra_service": {
                    "service_tags": []
                },
                "skus": [
                    {
                        "price": price,
                        "stock_num": stock,
                        "out_sku_id": f"SKU_{product_id}_1"
                    }
                ],
                "listing": random.choice([0, 1]),  # 随机决定是否上架
                "out_product_id": product_id,
                "create_time": datetime.now().isoformat()
            }
            
            # 添加发货方式相关字段
            if product['deliver_method'] == 0:
                # 快递发货
                product['express_info'] = {
                    "express_type": 0,
                    "template_id": "default_template"
                }
            elif product['deliver_method'] == 3:
                # 无需快递，可选发货账号类型
                product['deliver_acct_type'] = [3]  # 手机号
            
            # 验证商品数据
            if self.validate_product(product):
                log_message(f"成功生成商品: {title}")
                return product
            else:
                log_message(f"生成的商品数据无效: {title}", "ERROR")
                # 递归重试生成
                return self.generate_single_product()
                
        except Exception as e:
            error_msg = f"生成商品失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return None
    
    def generate_products(self, count=None):
        """
        批量生成商品信息
        
        :param count: 生成数量，如果为None则使用配置中的product_count
        :return: 商品数据列表
        """
        if count is None:
            count = self.config.get('product_count', 10)
        
        log_message(f"开始批量生成{count}个商品")
        products = []
        success_count = 0
        fail_count = 0
        
        for i in range(count):
            log_message(f"正在生成商品 {i+1}/{count}")
            product = self.generate_single_product()
            if product:
                products.append(product)
                success_count += 1
            else:
                fail_count += 1
            
            # 避免生成过快（可选）
            time.sleep(0.1)
        
        log_message(f"商品生成完成，成功{success_count}个，失败{fail_count}个")
        return products
    
    def validate_product(self, product):
        """
        验证商品数据是否符合API要求
        
        :param product: 商品数据
        :return: 是否有效
        """
        try:
            # 验证核心必需字段
            required_fields = [
                'title', 'head_imgs', 'deliver_method', 
                'cats', 'cats_v2', 'extra_service', 'skus'
            ]
            
            for field in required_fields:
                if field not in product:
                    log_message(f"商品缺少必需字段: {field}", "ERROR")
                    return False
            
            # 验证标题长度
            title = product['title']
            if len(title) < 5 or len(title) > 60:
                log_message(f"商品标题长度不符合要求: {len(title)}字符", "ERROR")
                return False
            
            # 验证主图数量
            head_imgs = product['head_imgs']
            if not isinstance(head_imgs, list) or len(head_imgs) < 3 or len(head_imgs) > 9:
                log_message(f"商品主图数量不符合要求: {len(head_imgs)}张", "ERROR")
                return False
            
            # 验证类目格式
            for cats_field in ['cats', 'cats_v2']:
                cats = product[cats_field]
                if not isinstance(cats, list) or len(cats) != 3:
                    log_message(f"商品类目格式不符合要求: {cats_field}", "ERROR")
                    return False
                for cat in cats:
                    if 'cat_id' not in cat:
                        log_message(f"类目缺少cat_id: {cat}", "ERROR")
                        return False
            
            # 验证SKU
            skus = product['skus']
            if not isinstance(skus, list) or len(skus) == 0 or len(skus) > 500:
                log_message(f"商品SKU数量不符合要求: {len(skus)}", "ERROR")
                return False
            
            for sku in skus:
                if 'price' not in sku or 'stock_num' not in sku:
                    log_message(f"SKU缺少必需字段: {sku}", "ERROR")
                    return False
                if not isinstance(sku['price'], int) or sku['price'] <= 0:
                    log_message(f"SKU价格无效: {sku['price']}", "ERROR")
                    return False
                if not isinstance(sku['stock_num'], int) or sku['stock_num'] < 0:
                    log_message(f"SKU库存无效: {sku['stock_num']}", "ERROR")
                    return False
            
            # 验证发货方式相关字段
            deliver_method = product['deliver_method']
            if deliver_method == 0:
                if 'express_info' not in product:
                    log_message("快递发货方式缺少express_info字段", "ERROR")
                    return False
            elif deliver_method == 3:
                if 'deliver_acct_type' not in product:
                    log_message("无需快递方式缺少deliver_acct_type字段", "ERROR")
                    return False
            
            # 验证商品详情
            if 'desc_info' in product:
                desc_info = product['desc_info']
                if 'imgs' in desc_info:
                    if not isinstance(desc_info['imgs'], list) or len(desc_info['imgs']) == 0:
                        log_message("商品详情图片无效", "ERROR")
                        return False
            
            return True
            
        except Exception as e:
            log_message(f"验证商品数据时发生错误: {str(e)}", "ERROR")
            return False
    
    def _generate_title(self):
        """
        生成商品标题
        
        :return: 标题字符串
        """
        template = random.choice(self.config.get('title_templates', ['{keyword}']))
        keyword = random.choice(self.config.get('keywords', ['商品']))
        
        # 替换模板中的占位符
        title = template.replace('{keyword}', keyword)
        title = title.replace('{id}', str(self.product_counter))
        
        # 确保标题长度符合要求
        if len(title) < 5:
            title += ' - 高品质商品'
        if len(title) > 60:
            title = title[:57] + '...'
        
        return title
    
    def _generate_subtitle(self, title):
        """
        生成商品副标题
        
        :param title: 主标题
        :return: 副标题字符串
        """
        subtitles = [
            "限时促销",
            "品质保证",
            "包邮到家",
            "新品上市",
            "热卖爆款"
        ]
        
        subtitle = random.choice(subtitles)
        # 限制在18个字符以内
        if len(subtitle) > 18:
            subtitle = subtitle[:18]
        
        return subtitle
    
    def _generate_short_title(self, title):
        """
        生成商品短标题
        
        :param title: 主标题
        :return: 短标题字符串
        """
        # 从主标题中提取前20个字符
        short_title = title[:20]
        
        return short_title
    
    def _generate_description(self):
        """
        生成商品描述
        
        :return: 描述字符串
        """
        templates = self.config.get('description_templates', ['这是一个商品描述'])
        description = random.choice(templates)
        
        # 添加一些随机内容丰富描述
        features = [
            "材质优良，经久耐用。",
            "设计精美，时尚大方。",
            "性价比高，物超所值。",
            "精工细作，品质保证。",
            "使用方便，操作简单。"
        ]
        
        # 随机添加1-3个特性描述
        for _ in range(random.randint(1, 3)):
            description += " " + random.choice(features)
        
        return description
    
    def _get_main_images(self):
        """
        获取主图列表
        
        :return: 主图URL列表
        """
        all_images = self.config.get('main_images', [])
        # 确保至少有3张主图
        if len(all_images) < 3:
            # 使用占位图片
            all_images = [
                "https://example.com/product1.jpg",
                "https://example.com/product2.jpg",
                "https://example.com/product3.jpg"
            ]
        
        # 随机选择3-9张图片
        count = random.randint(3, min(9, len(all_images)))
        # 使用random.sample确保不重复
        return random.sample(all_images, count)
    
    def _get_detail_images(self):
        """
        获取详情图列表
        
        :return: 详情图URL列表
        """
        all_images = self.config.get('detail_images', [])
        # 确保至少有1张详情图
        if not all_images:
            all_images = ["https://example.com/detail1.jpg"]
        
        # 随机选择1-5张图片
        count = random.randint(1, min(5, len(all_images)))
        return random.sample(all_images, count)
    
    def save_products_to_file(self, products, file_path):
        """
        保存生成的商品到文件
        
        :param products: 商品列表
        :param file_path: 文件路径
        :return: 是否成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            log_message(f"成功保存{len(products)}个商品到文件: {file_path}")
            return True
        except Exception as e:
            log_message(f"保存商品到文件失败: {str(e)}", "ERROR")
            return False


def main():
    """
    测试商品生成器功能
    """
    # 测试配置
    test_config = {
        'product_count': 3,
        'category_ids': [
            {'level1': '381003', 'level2': '380003', 'level3': '517050'},
            {'level1': '381003', 'level2': '380002', 'level3': '517049'}
        ],
        'price_range': [100, 9999],
        'stock_range': [10, 1000],
        'title_templates': ['高品质{keyword}商品', '特价促销{keyword}'],
        'keywords': ['电子产品', '家居用品', '服装配饰'],
        'description_templates': ['本商品质量优良，值得购买。'],
        'main_images': [
            "https://example.com/product1.jpg",
            "https://example.com/product2.jpg",
            "https://example.com/product3.jpg",
            "https://example.com/product4.jpg"
        ],
        'detail_images': [
            "https://example.com/detail1.jpg",
            "https://example.com/detail2.jpg"
        ],
        'deliver_method': 0
    }
    
    generator = ProductGenerator(test_config)
    
    # 测试生成单个商品
    print("生成单个商品测试:")
    product = generator.generate_single_product()
    if product:
        print(f"生成成功: {product['title']}")
        print(json.dumps(product, ensure_ascii=False, indent=2))
    
    # 测试批量生成商品
    print("\n批量生成商品测试:")
    products = generator.generate_products(2)
    print(f"批量生成完成，共{len(products)}个商品")
    
    # 保存到文件
    generator.save_products_to_file(products, "generated_products_test.json")


if __name__ == "__main__":
    main()
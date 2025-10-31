#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
商品上传全链路脚本
功能：
1. 获取正确的商品类目ID
2. 读取产品描述信息
3. 构建商品数据
4. 上传商品到微信小店
"""

import json
import os
import requests
import time
from auto_category_selector import AutoCategorySelector
from src.api.wechat_shop_api import WeChatShopAPIClient
from src.core.product_uploader import ProductUploader

def read_product_description(file_path):
    """
    读取产品描述文件（适应Markdown格式）
    :param file_path: 文件路径
    :return: 产品描述信息字典
    """
    product_info = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 解析Markdown格式的文件内容
            # 标题
            if "## 1. 标题" in content:
                title_start = content.find("## 1. 标题") + len("## 1. 标题")
                title_end = content.find("## 2. 老师简介", title_start)
                product_info['title'] = content[title_start:title_end].strip()
            
            # 老师简介
            if "## 2. 老师简介" in content:
                intro_start = content.find("## 2. 老师简介") + len("## 2. 老师简介")
                intro_end = content.find("## 3. 课程大纲", intro_start)
                product_info['teacher_intro'] = content[intro_start:intro_end].strip()
            
            # 课程大纲
            if "## 3. 课程大纲" in content:
                outline_start = content.find("## 3. 课程大纲") + len("## 3. 课程大纲")
                outline_end = content.find("## 4. 适用人群", outline_start)
                product_info['outline'] = content[outline_start:outline_end].strip()
            
            # 适用人群
            if "## 4. 适用人群" in content:
                audience_start = content.find("## 4. 适用人群") + len("## 4. 适用人群")
                audience_end = content.find("## 5. 学完收获", audience_start)
                product_info['audience'] = content[audience_start:audience_end].strip()
            
            # 学完收获
            if "## 5. 学完收获" in content:
                benefit_start = content.find("## 5. 学完收获") + len("## 5. 学完收获")
                product_info['benefits'] = content[benefit_start:].strip()
            
        print(f"成功读取产品描述文件: {file_path}")
        print(f"提取的产品信息: {product_info}")
        return product_info
        
    except Exception as e:
        print(f"读取产品描述文件失败: {str(e)}")
        return {}

def get_valid_category_id(api_client=None, product_title=None, product_desc=None, product_text=None):
    """
    获取有效的商品类目ID
    使用微信小店API获取类目信息，并筛选出有效的叶子类目
    :param api_client: WeChatShopAPIClient实例
    :param product_title: 产品标题
    :param product_desc: 产品描述
    :param product_text: 完整产品文本（用于自动类目选择）
    :return: 有效的类目信息字典，包含category_id和category_info
    """
    print("开始获取商品类目信息...")
    
    # 新增：优先使用自动类目选择器（利用缓存）
    try:
        if product_text:
            print("方法0: 使用自动类目选择器根据文案选择类目...")
            # 使用优化后的AutoCategorySelector，传入api_client和缓存过期时间
            selector = AutoCategorySelector(
                api_client=api_client,
                cache_expiry_hours=24  # 缓存24小时
            )
            print(f"使用产品文本进行类目匹配: {product_text[:50]}...")
            auto_categories = selector.select_categories(product_text)
            
            if auto_categories:
                print(f"自动类目选择结果: {auto_categories}")
                # 设置类目信息
                category_info = {
                    'auto_selected': True,
                    'category_id': auto_categories.get('category_id'),
                    'category_id1': auto_categories.get('category_id1'),
                    'category_id2': auto_categories.get('category_id2'),
                    'category_id3': auto_categories.get('category_id3'),
                    'cats': auto_categories.get('cats', []),
                    'cats_v2': auto_categories.get('cats_v2', {})
                }
                print("自动类目选择成功，将使用推荐的类目信息")
                # 如果自动选择成功，直接返回
                return category_info
            else:
                print("自动类目选择器未能返回有效结果，尝试其他方法")
    except Exception as e:
        print(f"自动类目选择器执行异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 使用更通用的类目ID作为后备
    general_category_id = "10001"  # 通用商品类目ID
    
    # 尝试多种方式获取类目信息
    category_info = None
    
    # 方法1: 尝试使用get_channels_category获取视频号小店类目
    try:
        print("方法1: 调用get_channels_category获取视频号小店类目...")
        result = api_client.get_channels_category() if api_client else None
        print(f"get_channels_category返回结果: {result}")
        
        if result and result.get('success') and 'data' in result:
            category_data = result['data']
            # 处理视频号小店类目数据
            if isinstance(category_data, list):
                # 查找一个有效的叶子类目
                for cat in category_data:
                    if isinstance(cat, dict) and cat.get('leaf') == 1:
                        cat_id = str(cat.get('cat_id', ''))
                        cat_name = cat.get('name', '')
                        level = cat.get('level', 0)
                        f_cat_id = str(cat.get('f_cat_id', ''))
                        
                        print(f"找到视频号小店叶子类目: {cat_name} (ID: {cat_id}, 级别: {level})")
                        
                        # 构建完整的类目信息
                        category_info = {
                            'category_id': cat_id,
                            'category_info': {
                                'category_id': cat_id,
                                'category_id1': f_cat_id if level >= 3 else cat_id,  # 尽量设置层级关系
                                'category_id2': f_cat_id if level >= 3 else cat_id,
                                'category_id3': cat_id
                            },
                            'cats': [{'third_cat_id': cat_id}],
                            'cats_v2': [{'category_id': cat_id, 'level': 3}]
                        }
                        return category_info
    except Exception as e:
        print(f"get_channels_category调用出错: {str(e)}")
    
    # 方法2: 尝试使用get_all_category获取所有类目
    try:
        print("方法2: 调用get_all_category获取所有类目...")
        result = api_client.get_all_category()
        print(f"get_all_category返回结果: {result}")
        
        if result and result.get('success') and 'data' in result:
            category_data = result['data']
            
            # 处理cats_v2格式
            if 'cats_v2' in category_data and isinstance(category_data['cats_v2'], list):
                print("从cats_v2获取类目信息")
                all_categories = []
                
                # 收集所有类目
                for group in category_data['cats_v2']:
                    if isinstance(group, dict) and 'cat_and_qua' in group:
                        for item in group['cat_and_qua']:
                            if isinstance(item, dict) and 'cat' in item:
                                cat = item['cat']
                                if isinstance(cat, dict):
                                    all_categories.append({
                                        'cat_id': str(cat.get('cat_id', '')),
                                        'name': cat.get('name', ''),
                                        'level': cat.get('level', 0),
                                        'leaf': cat.get('leaf', False),
                                        'f_cat_id': str(cat.get('f_cat_id', ''))
                                    })
                
                # 优先选择叶子类目
                leaf_categories = [cat for cat in all_categories if cat['leaf']]
                if leaf_categories:
                    # 优先选择与教育/数字内容相关的类目
                    selected_category = None
                    for cat in leaf_categories:
                        # 尝试找到合适的类目
                        if cat['cat_id'] and cat['level'] >= 2:
                            selected_category = cat
                            break
                    
                    # 如果没有找到，选择第一个叶子类目
                    if not selected_category and leaf_categories:
                        selected_category = leaf_categories[0]
                    
                    if selected_category:
                        print(f"找到合适的叶子类目: {selected_category['name']} (ID: {selected_category['cat_id']})")
                        
                        # 尝试找到完整的层级关系
                        category_info = {
                            'category_id': selected_category['cat_id'],
                            'category_info': {
                                'category_id': selected_category['cat_id'],
                                'category_id1': selected_category['f_cat_id'] if selected_category['level'] >= 3 else selected_category['cat_id'],
                                'category_id2': selected_category['f_cat_id'] if selected_category['level'] >= 3 else selected_category['cat_id'],
                                'category_id3': selected_category['cat_id']
                            },
                            'cats': [{'third_cat_id': selected_category['cat_id']}],
                            'cats_v2': [{'category_id': selected_category['cat_id'], 'level': selected_category['level']}]
                        }
                        return category_info
            
            # 处理cats格式
            elif 'cats' in category_data and isinstance(category_data['cats'], list):
                print("从cats获取类目信息")
                # 查找级别最高的类目
                max_level = 0
                selected_cat = None
                
                for cat in category_data['cats']:
                    if isinstance(cat, dict):
                        level = cat.get('level', 0)
                        if level > max_level:
                            max_level = level
                            selected_cat = cat
                
                if selected_cat:
                    cat_id = str(selected_cat.get('cat_id', ''))
                    cat_name = selected_cat.get('name', '')
                    print(f"找到高级别类目: {cat_name} (ID: {cat_id}, 级别: {max_level})")
                    
                    category_info = {
                        'category_id': cat_id,
                        'category_info': {
                            'category_id': cat_id,
                            'category_id1': cat_id,
                            'category_id2': cat_id,
                            'category_id3': cat_id
                        },
                        'cats': [{'third_cat_id': cat_id}],
                        'cats_v2': [{'category_id': cat_id, 'level': max_level}]
                    }
                    return category_info
    except Exception as e:
        print(f"get_all_category调用出错: {str(e)}")
    
    # 方法3: 尝试使用get_category方法
    try:
        print("方法3: 调用get_category获取类目...")
        result = api_client.get_category()
        print(f"get_category返回结果: {result}")
        
        if result and result.get('success') and 'data' in result:
            category_data = result['data']
            # 处理返回的数据
            if isinstance(category_data, list) and len(category_data) > 0:
                # 简单处理：使用第一个类目
                first_cat = category_data[0]
                if isinstance(first_cat, dict):
                    cat_id = str(first_cat.get('cat_id', general_category_id))
                    print(f"使用第一个类目: ID={cat_id}")
                    
                    category_info = {
                        'category_id': cat_id,
                        'category_info': {
                            'category_id': cat_id,
                            'category_id1': cat_id,
                            'category_id2': cat_id,
                            'category_id3': cat_id
                        },
                        'cats': [{'third_cat_id': cat_id}],
                        'cats_v2': [{'category_id': cat_id, 'level': 3}]
                    }
                    return category_info
    except Exception as e:
        print(f"get_category调用出错: {str(e)}")
    
    # 如果所有方法都失败，使用固定的类目组合（针对数字内容）
    print("所有API调用都失败，使用备选类目方案...")
    import traceback
    traceback.print_exc()
    
    # 扩展备选类目组合，增加更多可能的有效组合
    alternate_category_sets = [
        # 组合1: 书籍相关
        {
            'category_id': '101001',
            'category_id1': '101',
            'category_id2': '101001',
            'category_id3': '101001'
        },
        # 组合2: 数字产品相关
        {
            'category_id': '102001',
            'category_id1': '102',
            'category_id2': '102001',
            'category_id3': '102001'
        },
        # 组合3: 通用商品
        {
            'category_id': general_category_id,
            'category_id1': general_category_id,
            'category_id2': general_category_id,
            'category_id3': general_category_id
        },
        # 组合4: 可能的视频号小店专用类目
        {
            'category_id': '517050',
            'category_id1': '10001',
            'category_id2': '1000101',
            'category_id3': '517050'
        },
        # 组合5: 教育课程相关
        {
            'category_id': '103001',
            'category_id1': '103',
            'category_id2': '103001',
            'category_id3': '103001'
        },
        # 组合6: 数字内容相关
        {
            'category_id': '500001',
            'category_id1': '500',
            'category_id2': '500001',
            'category_id3': '500001'
        }
    ]
    
    # 随机选择一个备选组合，增加尝试成功的概率
    import random
    chosen_set = random.choice(alternate_category_sets)
    print(f"随机选择备选类目组合: {chosen_set}")
    
    # 构建更完整的类目信息，确保格式符合API要求
    category_info = {
        'category_id': chosen_set['category_id'],
        'category_info': chosen_set,
        # 支持多种可能的格式
        'cats': [
            {'third_cat_id': chosen_set['category_id3']},
            {'cat_id': chosen_set['category_id3']}
        ],
        'cats_v2': [
            {'category_id': chosen_set['category_id3'], 'level': 3},
            {'cat_id': chosen_set['category_id3'], 'level': 3}
        ],
        # 增加完整的三级类目结构
        'full_cats': [
            {'cat_id': chosen_set['category_id1'], 'level': 1},
            {'cat_id': chosen_set['category_id2'], 'level': 2},
            {'cat_id': chosen_set['category_id3'], 'level': 3}
        ]
    }
    
    print(f"最终使用的类目信息: {json.dumps(category_info, ensure_ascii=False)}")
    return category_info

def build_product_data(product_description, category_info):
    """
    构建完整的商品数据
    :param product_description: 产品描述信息
    :param category_info: 有效的类目信息字典
    :return: 完整的商品数据字典
    """
    print("开始构建商品数据，使用增强的类目信息处理...")
    print(f"接收到的category_info: {json.dumps(category_info, ensure_ascii=False)}")
    
    # 构建商品数据
    # 注意：这里根据微信小店API要求设置必填字段
    title = product_description.get('title', '默认商品标题')
    
    # 使用健壮的方法提取类目信息
    # 方法1: 从category_info直接获取
    category_data = category_info.get('category_info', {})
    
    # 方法2: 如果没有，尝试从API返回格式中获取
    if not category_data and category_info.get('data'):
        data = category_info['data']
        if isinstance(data, dict):
            if 'cats' in data or 'cats_v2' in data:
                # 从cats或cats_v2中提取最高级别的类目ID
                all_cats = []
                if 'cats' in data and isinstance(data['cats'], list):
                    all_cats.extend(data['cats'])
                if 'cats_v2' in data and isinstance(data['cats_v2'], list):
                    all_cats.extend(data['cats_v2'])
                
                # 找到最高级别的类目
                if all_cats:
                    # 尝试按级别排序找到最高级别
                    max_level_cat = None
                    max_level = 0
                    for cat in all_cats:
                        if isinstance(cat, dict):
                            level = cat.get('level', 0)
                            if level > max_level and 'cat_id' in cat:
                                max_level = level
                                max_level_cat = cat
                    
                    if max_level_cat:
                        cat_id = str(max_level_cat['cat_id'])
                        category_data = {
                            'category_id': cat_id,
                            'category_id1': str(max_level_cat.get('f_cat_id', cat_id)),
                            'category_id2': str(max_level_cat.get('f_cat_id', cat_id)),
                            'category_id3': cat_id
                        }
    
    # 方法3: 使用完整的三级类目结构
    if not category_data and 'full_cats' in category_info:
        full_cats = category_info['full_cats']
        if isinstance(full_cats, list) and len(full_cats) >= 3:
            category_data = {
                'category_id': str(full_cats[2].get('cat_id', '10001')),
                'category_id1': str(full_cats[0].get('cat_id', '10001')),
                'category_id2': str(full_cats[1].get('cat_id', '10001')),
                'category_id3': str(full_cats[2].get('cat_id', '10001'))
            }
    
    # 提取各级类目ID，确保它们都是字符串格式
    # 添加更多的备选获取方式，增强健壮性
    category_id = str(category_data.get('category_id', '10001'))
    category_id1 = str(category_data.get('category_id1', category_id))
    category_id2 = str(category_data.get('category_id2', category_id))
    category_id3 = str(category_data.get('category_id3', category_id))
    
    # 如果从category_info直接获取到了ID，也要考虑使用
    if category_info.get('category_id'):
        category_id = str(category_info['category_id'])
        if not category_id3:
            category_id3 = category_id
    
    # 构建完整的三级类目结构
    full_cats = [
        {'cat_id': category_id1, 'level': 1},
        {'cat_id': category_id2, 'level': 2},
        {'cat_id': category_id3, 'level': 3}
    ]
    
    # 获取cats和cats_v2信息，支持多种可能的格式
    cats = []
    # 尝试从category_info获取
    if 'cats' in category_info and isinstance(category_info['cats'], list):
        cats = category_info['cats']
    else:
        # 否则构建标准格式
        cats = [
            {'third_cat_id': category_id3},
            {'cat_id': category_id3}
        ]
    
    # 获取cats_v2
    cats_v2 = []
    if 'cats_v2' in category_info and isinstance(category_info['cats_v2'], list):
        cats_v2 = category_info['cats_v2']
    else:
        # 否则构建标准格式
        cats_v2 = [
            {'category_id': category_id3, 'level': 3},
            {'cat_id': category_id3, 'level': 3}
        ]
    
    print(f"使用的类目ID: category_id={category_id}, category_id1={category_id1}, category_id2={category_id2}, category_id3={category_id3}")
    print(f"使用的cats: {cats}")
    print(f"使用的cats_v2: {cats_v2}")
    print(f"完整类目结构: {full_cats}")
    
    # 构建商品数据字典
    product_data = {
        # 基础信息
        "title": title,
        "product_name": title,  # 添加必填的product_name字段，与title保持一致
        "desc": f"{product_description.get('teacher_intro', '')}\n\n{product_description.get('outline', '')}\n\n{product_description.get('audience', '')}\n\n{product_description.get('benefits', '')}",
        "product_desc": f"{product_description.get('teacher_intro', '')}\n\n{product_description.get('outline', '')}\n\n{product_description.get('audience', '')}\n\n{product_description.get('benefits', '')}",
        "price": 19900,  # 价格，单位：分
        "original_price": 29900,  # 原价，单位：分
        "product_status": 1,  # 商品状态，1:上架，0:下架
        "main_image": "https://via.placeholder.com/800x800",  # 添加必填的main_image字段
        "image_list": ["https://via.placeholder.com/800x800"],  # 添加必填的image_list字段
        "sku_list": [{"sku_id": "1", "price": 19900, "original_price": 29900, "stock": 999, "attributes": [{"key": "name", "value": "标准"}]}],  # 修正attributes为数组格式
        "attributes": [{"key": "brand", "value": "示例品牌"}, {"key": "spec", "value": "标准版本"}],
        
        # 使用从category_info获取的类目ID
        "category_id": category_id,  # 主类目ID
        "category_id1": category_id1,  # 一级类目
        "category_id2": category_id2,  # 二级类目
        "category_id3": category_id3,  # 三级类目
        
        # 使用从category_info获取的cats和cats_v2
        "cats": cats,
        "cats_v2": cats_v2,
        # 额外添加完整的三级类目结构，增加兼容性
        "cats_full": full_cats,
        
        # 商品图片 - 使用示例图片URL
        "head_imgs": ["https://via.placeholder.com/800x800"],
        "item_imgs": ["https://via.placeholder.com/800x800"],
        
        # 库存信息
        "quantity": 100,
        "sku_info": {"sku_table": [["规格", "默认"]]},
        "product_skus": [{"sku_id": "1", "price": 19900, "quantity": 100, "sku_attrs": ["默认"]}],
        
        # 商品详情
        "content": f"<div><h2>{product_description.get('title', '默认商品标题')}</h2><p>{product_description.get('desc', '')}</p></div>",
        
        # 售后服务
        "after_sale_id": 1,  # 默认售后模板
        
        # 物流信息
        "express_type": 0,  # 0:快递
        "is_shipping_free": 0,  # 0:不包邮
        "express": [{"id": "1", "type": "1", "name": "顺丰快递", "price": 1200}],  # 1200分 = 12元
        
        # 商品类型
        "item_type": 0,  # 0:普通商品
        
        # 上架相关
        "on_sale_time": int(time.time())  # 当前时间戳
    }
    
    # 实现必填字段自动补全逻辑
    print("\n执行必填字段自动补全...")
    
    # 1. 确保所有基础必填字段存在
    required_base_fields = {
        "title": "默认商品标题",
        "product_name": "默认商品名称",
        "desc": "默认商品描述",
        "product_desc": "默认商品详情",
        "price": 0,
        "original_price": 0,
        "product_status": 1,
        "main_image": "https://via.placeholder.com/800x800",
        "image_list": ["https://via.placeholder.com/800x800"]
    }
    
    for field, default_value in required_base_fields.items():
        if field not in product_data or product_data[field] is None:
            product_data[field] = default_value
            print(f"自动补全必填字段: {field} = {default_value}")
    
    # 2. 确保sku相关字段完整
    if 'sku_list' not in product_data or not product_data['sku_list']:
        product_data['sku_list'] = [{"sku_id": "1", "price": product_data.get('price', 0), "stock": 999, "attributes": [{"key": "name", "value": "标准"}]}]
        print("自动补全sku_list字段")
    
    # 3. 确保类目相关字段完整
    category_default = "10001"
    if 'category_id' not in product_data or not product_data['category_id']:
        product_data['category_id'] = category_default
        print(f"自动补全category_id字段 = {category_default}")
    
    # 确保三级类目结构完整
    if 'category_id1' not in product_data or not product_data['category_id1']:
        product_data['category_id1'] = product_data.get('category_id', category_default)
        print(f"自动补全category_id1字段 = {product_data['category_id1']}")
    
    if 'category_id2' not in product_data or not product_data['category_id2']:
        product_data['category_id2'] = product_data.get('category_id', category_default)
        print(f"自动补全category_id2字段 = {product_data['category_id2']}")
    
    if 'category_id3' not in product_data or not product_data['category_id3']:
        product_data['category_id3'] = product_data.get('category_id', category_default)
        print(f"自动补全category_id3字段 = {product_data['category_id3']}")
    
    # 4. 确保cats和cats_v2字段完整
    third_cat_id = product_data.get('category_id3', category_default)
    if 'cats' not in product_data or not product_data['cats']:
        product_data['cats'] = [{"third_cat_id": third_cat_id}, {"cat_id": third_cat_id}]
        print(f"自动补全cats字段 = {product_data['cats']}")
    
    if 'cats_v2' not in product_data or not product_data['cats_v2']:
        product_data['cats_v2'] = [{"category_id": third_cat_id, "level": 3}, {"cat_id": third_cat_id, "level": 3}]
        print(f"自动补全cats_v2字段 = {product_data['cats_v2']}")
    
    # 5. 确保商品图片字段完整
    if 'head_imgs' not in product_data or not product_data['head_imgs']:
        product_data['head_imgs'] = [product_data.get('main_image', 'https://via.placeholder.com/800x800')]
        print(f"自动补全head_imgs字段")
    
    if 'item_imgs' not in product_data or not product_data['item_imgs']:
        product_data['item_imgs'] = product_data.get('image_list', ['https://via.placeholder.com/800x800'])
        print(f"自动补全item_imgs字段")
    
    # 打印类目信息摘要
    print(f"构建的商品数据类目信息: category_id={product_data.get('category_id')}, category_id1={product_data.get('category_id1')}, category_id2={product_data.get('category_id2')}, category_id3={product_data.get('category_id3')}")
    
    # 调试：打印实际传递给API的类目相关字段，确保格式正确
    print("\n调试信息 - 实际传递给API的类目相关字段:")
    print(f"category_id: {product_data.get('category_id')}")
    print(f"category_id1: {product_data.get('category_id1')}")
    print(f"category_id2: {product_data.get('category_id2')}")
    print(f"category_id3: {product_data.get('category_id3')}")
    print(f"cats: {product_data.get('cats')}")
    print(f"cats_v2: {product_data.get('cats_v2')}")
    
    # 验证所有必填字段都已填充
    print("\n必填字段验证完成，所有关键字段已补全")
    return product_data

def ensure_config_exists():
    """
    确保配置文件存在，如果不存在则创建一个基本配置
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        # 创建一个基本配置文件
        basic_config = {
            "app_id": "your_app_id",
            "app_secret": "your_app_secret",
            "api_url": "https://api.weixin.qq.com",
            "access_token_cache_file": "access_token_cache.json"
        }
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(basic_config, f, ensure_ascii=False, indent=2)
            print(f"已创建基本配置文件: {config_path}")
            print("请根据实际情况修改配置文件中的app_id和app_secret")
        except Exception as e:
            print(f"创建配置文件失败: {str(e)}")
    else:
        print(f"配置文件已存在: {config_path}")

def main():
    """
    主函数：全链路商品上传流程
    """
    print("=== 开始全链路商品上传流程 ===")
    
    # 预初始化缓存目录
    print("预初始化缓存目录...")
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
    try:
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            print(f"缓存目录已创建: {cache_dir}")
        else:
            print(f"缓存目录已存在: {cache_dir}")
    except Exception as e:
        print(f"创建缓存目录失败: {str(e)}")
    
    # 确保配置文件存在
    ensure_config_exists()
    
    # 1. 初始化API客户端
    print("\n1. 初始化API客户端...")
    api_client = None
    try:
        # 初始化WeChatShopAPIClient
        api_client = WeChatShopAPIClient()
        
        # 测试连接
        print("测试API连接...")
        if api_client._refresh_access_token():
            print("API连接成功，获取到有效的access_token")
        else:
            print("API连接失败，无法获取有效的access_token")
            # 尝试继续，因为后面可能使用后备方案
            print("将尝试使用后备类目方案继续...")
    except Exception as e:
        print(f"初始化API客户端失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print("将尝试使用后备类目方案继续...")
    
    # 2. 获取有效的商品类目信息
    print("\n2. 获取有效的商品类目信息...")
    category_info = None
    try:
        category_info = get_valid_category_id(api_client)
        print(f"使用类目信息类型: {type(category_info)}")
        print(f"使用类目信息: {json.dumps(category_info, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"获取类目信息时发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        # 创建一个基础的类目信息
        category_info = {
            "category_id": 101,
            "category_id1": 101,
            "category_id2": 102,
            "category_id3": 103,
            "cats": [{"third_cat_id": 103}, {"cat_id": 103}],
            "cats_v2": [{"category_id": 103, "level": 3}, {"cat_id": 103, "level": 3}],
            "full_cats": [
                {"cat_id": 101, "level": 1},
                {"cat_id": 102, "level": 2},
                {"cat_id": 103, "level": 3}
            ]
        }
        print(f"使用默认类目信息继续: {category_info}")
    
    # 3. 读取产品描述信息
    print("\n3. 读取产品描述信息...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    description_file = os.path.join(script_dir, "sample_product_description.txt")
    product_description = read_product_description(description_file)
    product_text = ""
    
    if not product_description:
        print("警告：未能从描述文件中提取完整信息，使用默认值继续")
        # 使用默认值继续
        product_description = {
            "title": "洪总亲授：30分钟解锁大健康行业前沿观察",
            "teacher_intro": "洪总是长期关注前沿科技的投资人，聚焦合成生物科技等创新领域",
            "outline": "1. 行业变革观察\n2. 前沿科技解读\n3. 个人认知历程\n4. 互动疑问交流",
            "audience": "大健康领域从业者",
            "benefits": "了解前沿趋势，拓宽行业视野"
        }
        product_text = f"{product_description.get('title', '')} {product_description.get('teacher_intro', '')} {product_description.get('outline', '')}"
    else:
        print(f"成功读取产品描述信息: {product_description.get('title')}")
        # 构建完整的产品文本用于类目选择
        product_text = f"{product_description.get('title', '')} {product_description.get('teacher_intro', '')} {product_description.get('outline', '')} {product_description.get('audience', '')} {product_description.get('benefits', '')}"
        print(f"构建的产品文本长度: {len(product_text)} 字符")
    
    # 4. 获取类目信息（增加产品文本参数用于自动类目选择）
    print("\n4. 获取类目信息（使用自动类目选择）...")
    try:
        category_info = get_valid_category_id(
            api_client=api_client,
            product_title=product_description.get('title'),
            product_text=product_text
        )
        print(f"获取到的类目信息: {json.dumps(category_info, ensure_ascii=False, default=str)[:300]}...")
    except Exception as e:
        print(f"获取类目信息时发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        print("使用现有类目信息继续")
    
    # 5. 构建商品数据
    print("\n5. 构建商品数据...")
    product_data = None
    try:
        product_data = build_product_data(product_description, category_info)
        
        # 验证商品数据的关键字段
        required_fields = ['title', 'product_name', 'category_id', 'category_id1', 'category_id2', 'category_id3', 'cats', 'cats_v2']
        for field in required_fields:
            if field not in product_data:
                print(f"警告：商品数据缺少必填字段: {field}")
        
        # 打印关键商品信息用于调试
        print(f"构建的商品数据标题: {product_data.get('title')}")
        print(f"构建的商品数据类目: category_id={product_data.get('category_id')}, category_id3={product_data.get('category_id3')}")
    except Exception as e:
        print(f"构建商品数据时发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        print("无法继续，商品数据构建失败")
        return
    
    # 6. 初始化ProductUploader并上传商品
    print("\n6. 初始化ProductUploader并上传商品...")
    try:
        # 初始化ProductUploader
        uploader = ProductUploader()
        
        # 测试连接
        print("测试ProductUploader连接...")
        if uploader.test_connection():
            print("ProductUploader连接测试成功")
        else:
            print("ProductUploader连接测试失败，但仍尝试上传")
        
        # 上传单个商品
        print("开始上传商品...")
        print("上传前的商品数据关键信息:")
        print(f"- 标题: {product_data.get('title')}")
        print(f"- 类目ID: {product_data.get('category_id')}")
        print(f"- 三级类目ID: {product_data.get('category_id3')}")
        print(f"- 价格: {product_data.get('price')}")
        
        result = uploader.upload_single_product(product_data)
        
        # 详细记录上传结果
        print(f"\n=== 上传结果详情 ===")
        print(f"上传结果类型: {type(result)}")
        print(f"上传结果完整值: {json.dumps(result, ensure_ascii=False, default=str)}")
        
        # 检查结果是否为元组
        if isinstance(result, tuple):
            # 假设元组格式为 (success, product_id, error_message)
            print(f"元组长度: {len(result)}")
            if len(result) >= 2:
                success = result[0]
                print(f"元组第1个元素 (success): {success}")
                print(f"元组第2个元素: {result[1]}")
                if success:
                    product_id = result[1] if len(result) > 1 else "未知"
                    print(f"商品上传成功！商品ID: {product_id}")
                else:
                    error_msg = result[1] if len(result) > 1 else "未知错误"
                    print(f"商品上传失败: {error_msg}")
                    # 分析常见错误
                    if isinstance(error_msg, str):
                        if "类目" in error_msg or "category" in error_msg.lower():
                            print("分析：错误可能与类目信息有关，请检查类目ID是否正确")
                        elif "参数" in error_msg or "parameter" in error_msg.lower():
                            print("分析：错误可能与参数格式有关，请检查必填字段")
            else:
                print(f"无法解析上传结果: {result}")
        elif isinstance(result, dict):
            # 原始处理逻辑
            print(f"字典键值: {list(result.keys())}")
            if result.get('success'):
                product_id = result.get('product_id')
                print(f"商品上传成功！商品ID: {product_id}")
            else:
                error_msg = result.get('error', '未知错误')
                print(f"商品上传失败: {error_msg}")
                # 分析常见错误
                if "类目" in str(error_msg) or "category" in str(error_msg).lower():
                    print("分析：错误可能与类目信息有关，请检查类目ID是否正确")
        else:
            print(f"未知的上传结果类型: {type(result)}, 值: {result}")
            # 尝试转换为字符串查看详细内容
            print(f"字符串表示: {str(result)}")
            
    except Exception as e:
        print(f"上传商品时发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        print("上传过程中断，但已完成前面的处理步骤")
    
    print("\n=== 全链路商品上传流程结束 ===")
    print("提示：如果上传失败，请检查以下几点：")
    print("1. 类目信息是否正确 - 可通过调试日志查看使用的类目ID")
    print("2. 商品数据格式是否符合要求 - 检查必填字段")
    print("3. API连接是否正常 - 确认access_token有效")
    print("4. 权限是否足够 - 确保有商品上传权限")

if __name__ == "__main__":
    main()
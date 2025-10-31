#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动类目选择器：根据产品文案自动匹配最合适的微信小店类目
"""

import os
import json
import sys
import logging
from collections import defaultdict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.wechat_shop_api import WeChatShopAPIClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AutoCategorySelector:
    """自动类目选择器类"""
    
    def __init__(self, api_client=None, categories_file='cache/all_categories.json', cache_expiry_hours=24):
        # 类目关键词映射表
        self.keyword_category_map = {
            # 大健康相关关键词
            '健康': ['营养健康', '保健食品', '健康服务', '医疗健康'],
            '保健品': ['营养健康', '保健食品'],
            '养生': ['营养健康', '保健食品', '健康服务'],
            '保健': ['营养健康', '保健食品'],
            '维生素': ['营养健康', '保健食品'],
            '营养品': ['营养健康', '保健食品'],
            '膳食补充': ['营养健康', '保健食品'],
            '大健康': ['营养健康', '保健食品', '健康服务'],
            '自由基': ['营养健康', '保健食品'],
            
            # 教育培训相关关键词
            '课程': ['教育培训', '在线教育', '知识付费'],
            '培训': ['教育培训', '职业培训'],
            '教育': ['教育培训', '在线教育'],
            '学习': ['教育培训', '在线教育'],
            '讲座': ['教育培训', '知识付费'],
            '课堂': ['教育培训', '在线教育'],
            '训练营': ['教育培训', '职业培训'],
            '知识': ['教育培训', '知识付费'],
            '认知': ['教育培训', '知识付费'],
            
            # 其他相关关键词
            '科技': ['数码产品', '电子设备'],
            '生物': ['生物科技', '医疗健康'],
            '合成生物': ['生物科技', '医疗健康'],
            '投资人': ['金融投资', '商业服务'],
            '投资': ['金融投资', '商业服务'],
        }
        
        # 预定义的最佳类目匹配
        self.preferred_categories = {
            '大健康课程': '教育培训-知识付费-健康管理',
            '健康知识讲座': '教育培训-知识付费-健康管理',
            '营养保健品': '营养健康-保健食品-膳食补充剂',
        }
        
        self.all_categories = []
        self.category_map = {}
        self.api_client = api_client
        self.cache_expiry_hours = cache_expiry_hours
        
        # 自动创建缓存目录
        cache_dir = os.path.dirname(categories_file)
        if cache_dir and not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, exist_ok=True)
                logger.info(f"创建缓存目录: {cache_dir}")
            except Exception as e:
                logger.error(f"创建缓存目录失败: {str(e)}")
                # 如果创建目录失败，回退到当前目录
                self.categories_file = os.path.basename(categories_file)
            else:
                self.categories_file = categories_file
        else:
            self.categories_file = categories_file
        
        self.last_update_time = 0
    
    def load_categories_from_file(self):
        """从文件加载类目数据，增加缓存过期检查"""
        try:
            if not os.path.exists(self.categories_file):
                logger.info(f"类目数据文件不存在: {self.categories_file}")
                return False
            
            # 检查缓存是否有效
            if not self._is_cache_valid():
                logger.info("类目缓存已过期，需要刷新")
                return False
            
            # 检查文件更新时间，避免频繁加载
            file_mod_time = os.path.getmtime(self.categories_file)
            if file_mod_time == self.last_update_time:
                logger.info("类目数据文件未更新，使用缓存数据")
                return True
            
            logger.info(f"从文件 {self.categories_file} 加载类目数据...")
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 验证文件格式
                if 'raw_categories' in data and 'category_map' in data:
                    self.all_categories = data['raw_categories']
                    self.category_map = data['category_map']
                    self.last_update_time = file_mod_time
                    
                    logger.info(f"成功从文件加载 {len(self.category_map)} 个类目")
                    return True
                else:
                    logger.error("类目数据文件格式不正确")
                    return False
                    
        except Exception as e:
            logger.error(f"从文件加载类目数据时发生异常: {str(e)}")
            return False
    
    def _is_cache_valid(self):
        """检查缓存是否有效（未过期）"""
        if not os.path.exists(self.categories_file):
            return False
        
        try:
            import time
            file_mod_time = os.path.getmtime(self.categories_file)
            current_time = time.time()
            
            # 检查是否超过过期时间
            hours_since_modified = (current_time - file_mod_time) / 3600
            if hours_since_modified > self.cache_expiry_hours:
                logger.info(f"缓存已过期: {hours_since_modified:.2f}小时 > {self.cache_expiry_hours}小时")
                return False
            
            return True
        except Exception as e:
            logger.error(f"检查缓存有效性时发生异常: {str(e)}")
            return False
    
    def load_categories(self, force_refresh=False):
        """加载类目数据，优先从文件加载，失败则从API获取
        
        Args:
            force_refresh: 是否强制从API刷新数据
            
        Returns:
            bool: 加载是否成功
        """
        try:
            if not self.api_client:
                logger.error("API客户端未初始化，无法从API获取类目数据")
                # 尝试只从文件加载
                return self.load_categories_from_file()
            
            # 如果不强制刷新，先尝试从文件加载
            if not force_refresh:
                if self.load_categories_from_file():
                    return True
                logger.info("从文件加载失败，尝试从API获取")
            else:
                logger.info("强制刷新模式，直接从API获取类目数据")
            
            # 从API获取类目数据
            logger.info("开始从API获取类目数据...")
            
            # 尝试获取视频号小店类目
            channels_result = self.api_client.get_channels_category()
            if channels_result and channels_result.get('success'):
                self.all_categories = channels_result.get('data', [])
                logger.info(f"成功获取到 {len(self.all_categories)} 个视频号小店类目")
                
                # 构建类目映射
                self._build_category_map()
                
                # 保存到文件
                self.save_categories_to_file()
                return True
            else:
                logger.error("获取类目数据失败")
                # 尝试最后一次从文件加载
                return self.load_categories_from_file()
                
        except Exception as e:
            logger.error(f"加载类目数据时发生异常: {str(e)}")
            # 发生异常时，尝试从文件加载
            return self.load_categories_from_file()
    
    def select_categories(self, text):
        """选择类目，供main.py调用的接口"""
        if not self.category_map:
            logger.error("类目映射未初始化，无法选择类目")
            return None
        
        # 获取推荐类目
        recommended = self.get_recommended_category(text)
        if not recommended:
            # 如果没有推荐类目，尝试匹配相关类目
            matched = self.match_categories_by_text(text)
            if matched:
                recommended = {
                    'id': matched[0]['id'],
                    'name': matched[0]['name'],
                    'full_path': matched[0]['full_path']
                }
            else:
                return None
        
        # 提取完整的三级类目ID
        # 这里假设full_path格式为"一级-二级-三级"
        path_parts = recommended['full_path'].split('-')
        category_id3 = recommended['id']
        category_id2 = category_id1 = category_id3
        
        # 尝试在类目映射中查找上级类目
        for cat_id, cat_info in self.category_map.items():
            # 找到当前类目的父级
            if cat_id == category_id3 and cat_info.get('parent_id'):
                category_id2 = cat_info['parent_id']
                # 继续查找父级的父级
                for p_cat_id, p_cat_info in self.category_map.items():
                    if p_cat_id == category_id2 and p_cat_info.get('parent_id'):
                        category_id1 = p_cat_info['parent_id']
                        break
                break
        
        return {
            'category_id': category_id3,
            'category_id1': category_id1,
            'category_id2': category_id2,
            'category_id3': category_id3,
            'cats': [{'third_cat_id': category_id3}],
            'cats_v2': [{'category_id': category_id3, 'level': 3}]
        }
    
    def _build_category_map(self):
        """构建类目ID到名称的映射"""
        def traverse_categories(categories, parent_path=''):
            for cat in categories:
                cat_id = cat.get('id')
                cat_name = cat.get('name')
                full_path = f"{parent_path}-{cat_name}" if parent_path else cat_name
                
                self.category_map[cat_id] = {
                    'name': cat_name,
                    'full_path': full_path,
                    'parent_id': cat.get('parent_id'),
                    'level': cat.get('level')
                }
                
                # 递归处理子类目
                if 'children' in cat and cat['children']:
                    traverse_categories(cat['children'], full_path)
        
        traverse_categories(self.all_categories)
        logger.info(f"类目映射构建完成，共 {len(self.category_map)} 个类目")
    
    def extract_keywords(self, text):
        """从文本中提取关键词"""
        keywords = []
        # 转换为小写进行匹配
        text_lower = text.lower()
        
        # 查找所有匹配的关键词
        for keyword, category_names in self.keyword_category_map.items():
            if keyword in text_lower:
                keywords.append((keyword, category_names))
        
        return keywords
    
    def match_categories_by_text(self, text):
        """根据文本内容匹配类目"""
        if not self.category_map:
            logger.error("类目映射未初始化")
            return []
        
        logger.info("开始根据文本匹配类目...")
        # 提取关键词
        keywords_with_categories = self.extract_keywords(text)
        
        if not keywords_with_categories:
            logger.warning("未提取到关键词")
            return []
        
        logger.info(f"提取到的关键词及相关类目: {keywords_with_categories}")
        
        # 统计类目得分
        category_scores = defaultdict(int)
        
        # 基于关键词匹配计算得分
        for keyword, related_categories in keywords_with_categories:
            for category_name in related_categories:
                for cat_id, cat_info in self.category_map.items():
                    if category_name in cat_info['full_path']:
                        # 根据匹配位置和层级调整得分
                        score = 10
                        # 如果在完整路径中出现多次，增加得分
                        score += cat_info['full_path'].count(category_name) * 5
                        # 叶子类目得分更高
                        if cat_info.get('level') == 3:
                            score += 20
                        category_scores[cat_id] += score
        
        # 按得分排序
        sorted_categories = sorted(
            [(cat_id, score) for cat_id, score in category_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # 返回前5个匹配度最高的类目
        top_categories = []
        for cat_id, score in sorted_categories[:5]:
            if cat_id in self.category_map:
                cat_info = self.category_map[cat_id]
                top_categories.append({
                    'id': cat_id,
                    'name': cat_info['name'],
                    'full_path': cat_info['full_path'],
                    'score': score
                })
        
        return top_categories
    
    def get_recommended_category(self, text, product_type=None):
        """获取推荐的最佳类目"""
        # 首先尝试基于产品类型的预定义匹配
        if product_type and product_type in self.preferred_categories:
            preferred_path = self.preferred_categories[product_type]
            logger.info(f"基于产品类型 '{product_type}' 使用预定义类目路径: {preferred_path}")
            
            # 查找匹配的类目
            for cat_id, cat_info in self.category_map.items():
                if cat_info['full_path'] == preferred_path:
                    return cat_info
        
        # 否则基于文本内容匹配
        matched_categories = self.match_categories_by_text(text)
        if matched_categories:
            best_match = matched_categories[0]
            logger.info(f"最佳匹配类目: {best_match['full_path']} (得分: {best_match['score']})")
            return {
                'id': best_match['id'],
                'name': best_match['name'],
                'full_path': best_match['full_path']
            }
        
        logger.warning("未找到合适的类目")
        return None
    
    def save_categories_to_file(self, filename=None):
        """保存类目数据到文件，自动创建目录并添加时间戳"""
        try:
            # 如果未指定文件名，使用实例属性
            target_filename = filename or self.categories_file
            
            # 确保目标目录存在
            target_dir = os.path.dirname(target_filename)
            if target_dir and not os.path.exists(target_dir):
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    logger.info(f"创建目录: {target_dir}")
                except Exception as e:
                    logger.error(f"创建目录失败: {str(e)}")
                    return False
            
            # 添加时间戳信息
            data = {
                'raw_categories': self.all_categories,
                'category_map': self.category_map,
                'timestamp': time.time(),
                'expiry_hours': self.cache_expiry_hours
            }
            
            with open(target_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新最后更新时间
            self.last_update_time = os.path.getmtime(target_filename)
            logger.info(f"类目数据已保存到 {target_filename}")
            return True
        except Exception as e:
            logger.error(f"保存类目数据失败: {str(e)}")
            return False

def load_product_description(file_path):
    """加载产品描述文案"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"加载产品描述失败: {str(e)}")
        return None

def main():
    try:
        logger.info("=== 自动类目选择器启动 ===")
        
        # 加载配置
        config_path = 'config.json'
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            return
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 初始化API客户端
        api_client = WeChatShopAPIClient(
            appid=config.get('appid'),
            appsecret=config.get('appsecret')
        )
        
        # 初始化类目选择器
        selector = AutoCategorySelector()
        
        # 加载类目数据（优先从文件加载，失败则从API获取并保存）
        if not selector.load_categories(api_client):
            logger.error("无法加载类目数据，退出")
            return
        
        # 加载产品描述
        product_desc_path = 'sample_product_description.txt'
        if os.path.exists(product_desc_path):
            product_text = load_product_description(product_desc_path)
            if product_text:
                logger.info(f"\n=== 产品描述分析 ===")
                
                # 根据产品类型推荐
                if '课程' in product_text and '大健康' in product_text:
                    recommended = selector.get_recommended_category(product_text, '大健康课程')
                else:
                    recommended = selector.get_recommended_category(product_text)
                
                if recommended:
                    logger.info(f"\n推荐的类目信息:")
                    logger.info(f"  类目ID: {recommended['id']}")
                    logger.info(f"  类目名称: {recommended['name']}")
                    logger.info(f"  完整路径: {recommended['full_path']}")
                
                # 显示所有匹配的类目
                matched_categories = selector.match_categories_by_text(product_text)
                if matched_categories:
                    logger.info(f"\n匹配度排序的类目列表 (前{len(matched_categories)}个):")
                    for i, cat in enumerate(matched_categories, 1):
                        logger.info(f"  {i}. {cat['full_path']} (得分: {cat['score']})")
        
        # 交互式类目选择
        logger.info("\n=== 交互式类目选择 ===")
        user_input = input("请输入产品描述文本 (或输入 'exit' 退出): ")
        if user_input.lower() != 'exit':
            matched_categories = selector.match_categories_by_text(user_input)
            if matched_categories:
                logger.info(f"\n为您推荐的类目 (按匹配度排序):")
                for i, cat in enumerate(matched_categories, 1):
                    logger.info(f"  {i}. {cat['full_path']} (匹配度: {cat['score']})")
                
                choice = input("\n请选择类目序号 (1-5): ")
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(matched_categories):
                        selected = matched_categories[idx]
                        logger.info(f"\n您选择的类目信息:")
                        logger.info(f"  类目ID: {selected['id']}")
                        logger.info(f"  类目名称: {selected['name']}")
                        logger.info(f"  完整路径: {selected['full_path']}")
                    else:
                        logger.warning("无效的选择")
                except ValueError:
                    logger.warning("请输入有效的数字")
        
        logger.info("\n=== 类目选择完成 ===")
        
    except Exception as e:
        logger.error(f"运行过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
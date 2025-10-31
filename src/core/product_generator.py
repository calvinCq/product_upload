#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商品生成模块
负责根据客户数据生成商品信息和图片，并组装成符合微信小店API要求的商品数据
"""

import os
import sys
import random
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入现有功能和新模块
from src.utils.logger import get_logger
from src.utils.exceptions import (ValidationError, ConfigError, APIError, 
                              OperationError, catch_exceptions)
from src.utils.standardized_interface import (
    ProductInfo, ClientInfo, ValidationResult
)
# catch_exceptions已从utils.exceptions导入
from data.data_loader import DataLoader
from src.api.qianduoduo_api import QianduoDuoAPI


class ProductGenerator:
    """
    商品生成器类
    负责根据客户数据生成商品信息和图片，并组装成符合微信小店API要求的商品数据
    集成统一的异常处理和日志记录机制
    """
    
    def __init__(self, config_manager=None):
        """
        初始化商品生成器
        
        :param config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.data_loader = DataLoader(config_manager)
        self.qianduoduo_api = None
        self.product_counter = 0
        self.logger = get_logger(__name__)
        self._initialize_components()
    
    @catch_exceptions(module_name="product_generator")
    def _initialize_components(self):
        """
        初始化组件和配置
        
        :raises: ConfigError 当配置无效或初始化失败时
        """
        # 初始化钱多多API客户端
        if self.config_manager:
            try:
                api_config = self.config_manager.get_qianduoduo_api_config()
                self.qianduoduo_api = QianduoDuoAPI(api_config)
                self.logger.info("钱多多API客户端初始化完成")
            except Exception as e:
                self.logger.error(f"初始化钱多多API客户端失败: {str(e)}")
                raise ConfigError(f"钱多多API配置初始化失败: {str(e)}")
        else:
            self.logger.warning("未提供配置管理器，部分功能可能受限")
    
    def get_generation_config(self) -> Dict[str, Any]:
        """
        获取生成配置
        
        :return: 生成配置字典
        :raises: ConfigError 当获取配置失败时
        """
        if self.config_manager:
            try:
                config = self.config_manager.get_generation_config()
                self.logger.info("成功获取商品生成配置")
                return config
            except Exception as e:
                self.logger.error(f"获取商品生成配置失败: {str(e)}")
                raise ConfigError(f"获取配置失败: {str(e)}")
        
        # 返回默认配置
        default_config = {
            'product_count': 1,
            'category_ids': [{'level1': '381003', 'level2': '380003', 'level3': '517050'}],
            'price_range': [99.0, 299.0],
            'stock_range': [10, 1000],
            'image_count': 3,
            'deliver_method': 0
        }
        self.logger.warning("未提供配置管理器，返回默认配置")
        return default_config
    
    @catch_exceptions(module_name="product_generator")
    def generate_product_title(self, client_data: Dict[str, Any]) -> str:
        """
        根据客户数据生成商品标题
        
        :param client_data: 客户数据
        :return: 商品标题
        :raises: ValidationError 当客户数据无效时
        :raises: OperationError 当生成标题失败时
        """
        if not isinstance(client_data, dict):
            self.logger.error("客户数据类型无效，必须是字典格式")
            raise ValidationError("客户数据必须是字典格式")
            
        # 优先使用客户数据中的course_title（从sample_product_description.txt提取的）
        if "course_title" in client_data and client_data["course_title"]:
            title = str(client_data["course_title"])
        else:
            # 如果没有course_title，则使用默认逻辑
            course_name = client_data.get('course_name', '精品课程')
            
            # 添加吸引人的前缀
            prefixes = [
                "限时特惠 | ", "专业认证 | ", "实战课程 | ", 
                "名师授课 | ", "零基础入门 | ", "热门推荐 | "
            ]
            
            title = f"{random.choice(prefixes)}{course_name}"
            # 确保标题长度符合要求
            if len(title) < 5:
                title += ' - 高品质课程'
        
        # 确保标题长度符合要求
        if len(title) > 60:
            title = title[:57] + '...'
            
        self.logger.info(f"生成商品标题: {title}")
        return title
    
    @catch_exceptions(module_name="product_generator")
    def generate_product_description(self, client_data: Dict[str, Any]) -> str:
        """
        根据客户数据生成商品描述，优先从sample_product_description.txt读取
        
        :param client_data: 客户数据
        :return: 商品描述
        :raises: ValidationError 当客户数据无效时
        :raises: OperationError 当生成描述失败时
        """
        if not isinstance(client_data, dict):
            self.logger.error("客户数据类型无效，必须是字典格式")
            raise ValidationError("客户数据必须是字典格式")
        
        try:
            # 优先尝试从sample_product_description.txt读取描述
            description_file = "sample_product_description.txt"
            if os.path.exists(description_file):
                try:
                    with open(description_file, 'r', encoding='utf-8') as f:
                        description = f.read().strip()
                    if description:
                        self.logger.info("从sample_product_description.txt成功读取商品描述")
                        return description
                    self.logger.warning("sample_product_description.txt文件为空")
                except Exception as e:
                    self.logger.error(f"读取sample_product_description.txt失败: {str(e)}")
            else:
                self.logger.warning(f"未找到文件: {description_file}")
            
            # 如果文件读取失败或不存在，则使用客户数据生成描述
            course_name = client_data.get('course_name', '精品课程')
            course_content = client_data.get('course_content', '')
            teacher_info = client_data.get('teacher_info', {})
            learning_outcomes = client_data.get('learning_outcomes', '')
            target_audience = client_data.get('target_audience', '')
            course_features = client_data.get('course_features', [])
            
            # 构建描述
            description_parts = []
            
            # 课程简介 - 确保所有值都是字符串类型
            description_parts.append(f"【课程名称】{str(course_name)}")
            description_parts.append("\n【课程简介】")
            content = str(course_content[:500] + "..." if len(str(course_content)) > 500 else course_content)
            description_parts.append(content)
            
            # 讲师信息 - 确保所有值都是字符串类型
            if teacher_info:
                description_parts.append("\n【讲师介绍】")
                description_parts.append(f"姓名：{str(teacher_info.get('name', '未知'))}")
                description_parts.append(f"职称：{str(teacher_info.get('title', ''))}")
                description_parts.append(f"经验：{str(teacher_info.get('experience', ''))}")
            
            # 学习目标 - 确保所有值都是字符串类型
            description_parts.append("\n【学习目标】")
            description_parts.append(str(learning_outcomes))
            
            # 适合人群 - 确保所有值都是字符串类型
            description_parts.append("\n【适合人群】")
            description_parts.append(str(target_audience))
            
            # 课程特色 - 确保所有值都是字符串类型
            if course_features:
                description_parts.append("\n【课程特色】")
                for feature in course_features[:5]:  # 最多显示5个特色
                    description_parts.append(f"• {str(feature)}")
            
            # 课程承诺
            description_parts.append("\n【课程承诺】")
            description_parts.append("• 提供永久学习权限")
            description_parts.append("• 专业讲师答疑指导")
            description_parts.append("• 课程内容定期更新")
            description_parts.append("• 课后作业实战练习")
            
            # 确保所有元素都是字符串
            str_description_parts = [str(part) for part in description_parts]
            description = "\n".join(str_description_parts)
            
            self.logger.info(f"生成商品描述，长度: {len(description)} 字符")
            return description
        except Exception as e:
            self.logger.error(f"生成商品描述失败: {str(e)}")
            raise OperationError(f"生成商品描述失败: {str(e)}")
    
    @catch_exceptions(module_name="product_generator")
    def generate_product_price(self, base_price_range: Optional[Tuple[float, float]] = None) -> float:
        """
        生成商品价格
        
        :param base_price_range: 价格范围元组 (min_price, max_price)
        :return: 生成的价格
        :raises: ValidationError 当价格范围参数无效时
        :raises: OperationError 当生成价格失败时
        """
        try:
            # 验证价格范围参数
            if base_price_range is not None:
                if not isinstance(base_price_range, tuple) or len(base_price_range) != 2:
                    self.logger.error("价格范围必须是包含两个元素的元组")
                    raise ValidationError("价格范围必须是包含两个元素的元组")
                
                min_price, max_price = base_price_range
                if not (isinstance(min_price, (int, float)) and isinstance(max_price, (int, float))):
                    self.logger.error("价格范围的元素必须是数字")
                    raise ValidationError("价格范围的元素必须是数字")
                
                if min_price < 0 or max_price < 0:
                    self.logger.error("价格不能为负数")
                    raise ValidationError("价格不能为负数")
                
                if min_price > max_price:
                    self.logger.error("最小价格不能大于最大价格")
                    raise ValidationError("最小价格不能大于最大价格")
            else:
                # 从配置获取价格范围或使用默认值
                generation_config = self.get_generation_config()
                price_range = generation_config.get('price_range', [99.0, 299.0])
                if isinstance(price_range, list) and len(price_range) >= 2:
                    base_price_range = (price_range[0], price_range[1])
            
            if not base_price_range:
                base_price_range = (99.0, 299.0)
            
            # 生成随机价格
            min_price, max_price = base_price_range
            price = round(random.uniform(min_price, max_price), 2)
            self.logger.info(f"生成商品价格: {price}")
            return price
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"生成商品价格失败: {str(e)}")
            raise OperationError(f"生成商品价格失败: {str(e)}")
    
    @catch_exceptions(module_name="product_generator")
    def generate_product_category(self) -> Dict[str, str]:
        """
        生成商品分类ID
        
        :return: 分类字典
        :raises: OperationError 当生成分类失败时
        """
        try:
            # 从配置获取分类ID或使用默认值
            generation_config = self.get_generation_config()
            category_ids = generation_config.get('category_ids', [])
            
            if category_ids and isinstance(category_ids, list):
                category = random.choice(category_ids)
                self.logger.info(f"使用配置的分类: {category}")
                return category
            
            # 默认分类（教育课程相关）
            default_category = {'level1': '381003', 'level2': '380003', 'level3': '517050'}
            self.logger.info(f"使用默认分类: {default_category}")
            return default_category
        except Exception as e:
            self.logger.error(f"生成商品分类失败: {str(e)}")
            raise OperationError(f"生成商品分类失败: {str(e)}")
    
    @catch_exceptions(module_name="product_generator")
    def generate_product_images(self, client_data: Dict[str, Any], 
                              image_count: int = 1) -> List[str]:
        """
        生成商品图片，确保生成真实图片
        
        :param client_data: 客户数据
        :param image_count: 需要生成的图片数量
        :return: 图片信息列表
        :raises: ValidationError 当输入参数无效时
        :raises: OperationError 当生成图片失败时
        """
        # 参数验证
        if not isinstance(client_data, dict):
            self.logger.error("客户数据类型无效，必须是字典格式")
            raise ValidationError("客户数据必须是字典格式")
        
        if not isinstance(image_count, int) or image_count <= 0 or image_count > 10:
            self.logger.error(f"图片数量必须是1-10之间的正整数，当前值: {image_count}")
            raise ValidationError("图片数量必须是1-10之间的正整数")
        
        try:
            # 检查并尝试初始化钱多多API客户端
            if not self.qianduoduo_api:
                self.logger.warning("钱多多API未初始化，尝试重新初始化")
                from src.api.qianduoduo_api import QianduoDuoAPI
                try:
                    # 使用配置管理器初始化（如果可用）
                    if self.config_manager:
                        api_config = self.config_manager.get_qianduoduo_api_config()
                        self.qianduoduo_api = QianduoDuoAPI(api_config)
                    else:
                        self.qianduoduo_api = QianduoDuoAPI()
                    self.logger.info("钱多多API客户端重新初始化成功")
                except Exception as init_error:
                    self.logger.error(f"钱多多API客户端初始化失败: {str(init_error)}")
                    raise OperationError(f"钱多多API初始化失败: {str(init_error)}")
            
            # 获取课程相关信息
            course_name = client_data.get('course_name', '精品课程')
            teacher_name = client_data.get('teacher_info', {}).get('name', '讲师')
            course_content = client_data.get('course_content', '')
            
            # 获取配置的模型信息
            model = "doubao-seedream-4-0-250828"  # 默认模型
            if self.config_manager:
                try:
                    model = self.config_manager.get_qianduoduo_api_config().get('model', model)
                except Exception:
                    self.logger.warning("未获取到模型配置，使用默认模型")
            
            # 生成提示词
            prompts = []
            for i in range(image_count):
                if i == 0:
                    # 主图：更详细的课程主题图片提示词
                    prompt = f"创建一张高质量、专业的{course_name}课程封面图片，清晰展示主题，细节丰富，色调专业，4K高清，专业设计，吸引人的构图，蓝色和白色为主色调，适合教育产品展示"
                    # 如果有课程内容摘要，添加到提示词中
                    if course_content and len(course_content) > 50:
                        content_summary = course_content[:100] + "..." if len(course_content) > 100 else course_content
                        prompt += f"，内容相关: {content_summary}"
                else:
                    # 副图：更详细的学习场景
                    scenarios = [
                        f"{course_name}学习场景，明亮现代的教室，学员专注学习的画面，专业教学环境，高清细节，真实感强",
                        f"{teacher_name}讲师在专业教室授课的场景，包含清晰的白板或PPT内容，互动教学氛围，生动的表情",
                        f"{course_name}实践操作场景，学员动手实践，老师指导，设备专业，环境整洁，高清真实",
                        f"课程相关的专业学习资料和工具展示，整洁的桌面布置，数字化设备，学习氛围浓厚",
                        f"学员互动讨论的协作场景，团队合作精神，积极的学习氛围，高清细节",
                        f"课程成果展示，学员获得证书的荣誉感场景，专业正式的证书样式，成就感表现"
                    ]
                    prompt = random.choice(scenarios)
                
                prompts.append(prompt)
            
            # 调用API生成图片
            image_results = []
            retry_count = 5  # 增加重试次数
            
            for i, prompt in enumerate(prompts):
                self.logger.info(f"正在生成第{i+1}张图片，提示词: {prompt}")
                success = False
                
                for retry in range(retry_count):
                    try:
                        # 指数退避等待时间
                        wait_time = min(2 ** retry, 10)  # 最大等待10秒
                        if retry > 0:
                            self.logger.info(f"第{retry+1}/{retry_count}次尝试，等待{wait_time}秒后重试...")
                            time.sleep(wait_time)
                        
                        # 调用API生成图片，指定模型
                        image_url = self.qianduoduo_api.generate_image(prompt, model=model)
                        
                        # 严格验证图片URL
                        if image_url and isinstance(image_url, str):
                            if image_url.startswith("http://") or image_url.startswith("https://"):
                                if not image_url.startswith("https://example.com"):  # 排除占位图
                                    image_results.append(image_url)
                                    self.logger.info(f"第{i+1}张图片生成成功: {image_url}")
                                    success = True
                                    # 添加间隔，避免API调用过于频繁
                                    if i < len(prompts) - 1:
                                        time.sleep(1)
                                    break
                                else:
                                    self.logger.warning(f"生成的图片URL是占位图: {image_url}")
                            else:
                                self.logger.error(f"生成的图片URL格式无效: {image_url}")
                        else:
                            self.logger.warning(f"生成第{i+1}张图片失败，返回的URL为空或无效，第{retry+1}/{retry_count}次尝试")
                    except Exception as img_error:
                        self.logger.error(f"生成图片时出错: {str(img_error)}，第{retry+1}/{retry_count}次尝试")
                
                if not success:
                    error_msg = f"无法生成第{i+1}张图片，已尝试{retry_count}次"
                    self.logger.error(error_msg)
                    raise OperationError(error_msg)
            
            self.logger.info(f"成功生成 {len(image_results)} 张真实商品图片")
            return image_results
            
        except (ValidationError, OperationError):
            raise
        except Exception as e:
            self.logger.error(f"生成商品图片失败: {str(e)}")
            raise OperationError(f"生成商品图片失败: {str(e)}")
    
    def generate_product(self, client_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        根据客户数据生成单个商品数据
        
        :param client_data: 客户数据
        :return: 生成的商品数据
        :raises: ValidationError 当客户数据无效时
        :raises: OperationError 当生成商品失败时
        """
        # 参数验证
        if not isinstance(client_data, dict):
            self.logger.error("客户数据类型无效，必须是字典格式")
            raise ValidationError("客户数据必须是字典格式")
        try:
            self.logger.info("开始生成单个商品数据")
            self.product_counter += 1
            product_id = f"PROD_{int(time.time())}_{self.product_counter}"
            
            # 生成商品基本信息
            title = self.generate_product_title(client_data)
            category = self.generate_product_category()
            price = int(self.generate_product_price() * 100)  # 转换为分
            
            # 获取库存配置
            generation_config = self.get_generation_config()
            stock_range = generation_config.get('stock_range', [10, 1000])
            stock = random.randint(stock_range[0], stock_range[1])
            
            # 生成商品描述
            description = self.generate_product_description(client_data)
            
            # 生成商品图片
            image_count = generation_config.get('image_count', 3)
            main_images = self.generate_product_images(client_data, image_count)
            
            # 构建商品数据
            product = {
                "title": title,
                "sub_title": self._generate_subtitle(title),
                "short_title": self._generate_short_title(title),
                "desc_info": {
                    "imgs": main_images[1:] if len(main_images) > 1 else [],  # 详情图使用主图的后几张
                    "desc": description
                },
                "head_imgs": main_images[:9],  # 最多9张主图
                "deliver_method": generation_config.get('deliver_method', 3),  # 默认无需快递
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
                "listing": 0,  # 默认不上架，等审核后手动上架
                "out_product_id": product_id,
                "create_time": datetime.now().isoformat(),
                "client_data_hash": str(hash(str(client_data))),  # 用于跟踪来源
                "status": "draft"  # 初始状态为草稿
            }
            
            # 添加发货方式相关字段
            deliver_method = product['deliver_method']
            if deliver_method == 0:
                # 快递发货
                product['express_info'] = {
                    "express_type": 0,
                    "template_id": "default_template"
                }
            elif deliver_method == 3:
                # 无需快递，可选发货账号类型
                product['deliver_acct_type'] = [3]  # 手机号
            
            # 验证商品数据
            if not self.validate_product(product):
                error_msg = f"生成的商品数据无效: {title}"
                self.logger.error(error_msg)
                raise ValidationError(error_msg)
            
            self.logger.info(f"成功生成商品: {title}")
            return product
                
        except (ValidationError, ConfigError):
            raise
        except Exception as e:
            self.logger.error(f"生成商品失败: {str(e)}")
            raise OperationError(f"生成商品失败: {str(e)}")
    
    def generate_products(self, client_data: Dict[str, Any], 
                         product_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        根据客户数据批量生成商品信息
        
        :param client_data: 客户数据
        :param product_count: 生成数量，如果为None则使用配置中的product_count
        :return: 商品数据列表
        :raises: ValidationError 当输入参数无效时
        :raises: OperationError 当生成商品失败时
        """
        # 参数验证
        if not isinstance(client_data, dict):
            self.logger.error("客户数据类型无效，必须是字典格式")
            raise ValidationError("客户数据必须是字典格式")
        
        if product_count is not None and (not isinstance(product_count, int) or product_count <= 0):
            self.logger.error("商品数量必须是正整数")
            raise ValidationError("商品数量必须是正整数")
        
        try:
            # 验证客户数据
            validation_result = self.data_loader.validate_client_data(client_data)
            if hasattr(validation_result, 'is_valid') and not validation_result.is_valid:
                self.logger.error(f"客户数据验证失败: {validation_result.errors}")
                raise ValidationError(f"客户数据验证失败: {validation_result.errors}")
            elif not validation_result:
                self.logger.error("客户数据无效，无法生成商品")
                raise ValidationError("客户数据无效，无法生成商品")
            
            # 获取商品数量
            if product_count is None:
                generation_config = self.get_generation_config()
                product_count = generation_config.get('product_count', 1)
            
            self.logger.info(f"开始批量生成{product_count}个商品")
            products = []
            success_count = 0
            fail_count = 0
            
            # 从配置获取是否使用异步
            generation_config = self.get_generation_config()
            use_async = generation_config.get('use_async', False)
            
            if use_async and product_count > 10:
                # 大量商品时使用异步生成
                products = self.generate_products_async(client_data, product_count)
                success_count = len(products)
            else:
                # 逐个生成商品
                for i in range(product_count):
                    self.logger.info(f"正在生成商品 {i+1}/{product_count}")
                    try:
                        product = self.generate_product(client_data)
                        if product:
                            products.append(product)
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        self.logger.error(f"生成第{i+1}个商品失败: {str(e)}")
                        fail_count += 1
                    
                    # 避免生成过快
                    time.sleep(0.5)
            
            self.logger.info(f"商品生成完成，成功{success_count}个，失败{fail_count}个")
            return products
            
        except (ValidationError, ConfigError):
            raise
        except Exception as e:
            self.logger.error(f"批量生成商品失败: {str(e)}")
            raise OperationError(f"批量生成商品失败: {str(e)}")
    
    async def generate_products_async(self, client_data: Dict[str, Any], 
                                    product_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        异步批量生成商品信息
        
        :param client_data: 客户数据
        :param product_count: 生成数量
        :return: 商品列表
        :raises: ValidationError 当输入参数无效时
        :raises: OperationError 当生成商品失败时
        """
        # 参数验证
        if not isinstance(client_data, dict):
            self.logger.error("客户数据类型无效，必须是字典格式")
            raise ValidationError("客户数据必须是字典格式")
        
        if product_count is not None and (not isinstance(product_count, int) or product_count <= 0):
            self.logger.error("商品数量必须是正整数")
            raise ValidationError("商品数量必须是正整数")
        
        try:
            # 验证客户数据
            validation_result = self.data_loader.validate_client_data(client_data)
            if hasattr(validation_result, 'is_valid') and not validation_result.is_valid:
                self.logger.error(f"客户数据验证失败: {validation_result.errors}")
                raise ValidationError(f"客户数据验证失败: {validation_result.errors}")
            elif not validation_result:
                self.logger.error("客户数据无效，无法生成商品")
                raise ValidationError("客户数据无效，无法生成商品")
            
            # 获取商品数量
            if product_count is None:
                generation_config = self.get_generation_config()
                product_count = generation_config.get('product_count', 1)
            
            self.logger.info(f"开始异步批量生成商品，数量: {product_count}")
            
            # 创建异步任务
            tasks = []
            for i in range(product_count):
                task = asyncio.create_task(self._generate_product_async_task(client_data, i))
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 过滤None结果和异常
            products = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"异步任务失败: {str(result)}")
                elif result is not None:
                    products.append(result)
            
            self.logger.info(f"异步商品生成完成: 成功 {len(products)}/{product_count} 个")
            return products
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"异步批量生成商品失败: {str(e)}")
            raise OperationError(f"异步批量生成商品失败: {str(e)}")
    
    async def _generate_product_async_task(self, client_data: Dict[str, Any], 
                                         index: int) -> Optional[Dict[str, Any]]:
        """
        异步生成单个商品的任务
        
        :param client_data: 客户数据
        :param index: 索引
        :return: 商品数据或None
        """
        try:
            self.logger.info(f"异步任务正在生成商品 {index+1}")
            product = self.generate_product(client_data)
            if product:
                # 添加异步任务标识
                product['async_task_index'] = index
            self.logger.info(f"异步任务 {index+1} 商品生成完成")
            return product
        except Exception as e:
            self.logger.error(f"异步任务 {index+1} 失败: {str(e)}")
            return None
    

    
    @catch_exceptions(module_name="product_generator")
    def validate_product(self, product: Dict[str, Any]) -> ValidationResult:
        """
        验证商品数据是否符合API要求
        
        :param product: 商品数据
        :return: ValidationResult对象，包含验证结果和错误信息
        :raises: ValidationError 当输入参数无效时
        """
        if not isinstance(product, dict):
            self.logger.error("商品数据类型无效，必须是字典格式")
            raise ValidationError("商品数据必须是字典格式")
        
        errors = []
        
        try:
            # 验证核心必需字段
            required_fields = [
                'title', 'head_imgs', 'deliver_method', 
                'cats', 'cats_v2', 'extra_service', 'skus'
            ]
            
            for field in required_fields:
                if field not in product:
                    errors.append(f"缺少必需字段: {field}")
                    self.logger.warning(f"商品验证失败: 缺少必需字段 '{field}'")
            
            # 验证标题长度
            if 'title' in product:
                title = product['title']
                if len(title) < 5 or len(title) > 60:
                    errors.append(f"商品标题长度不符合要求: {len(title)}字符")
                    self.logger.warning(f"商品验证失败: 标题长度({len(title)})不在有效范围内")
            
            # 验证主图数量
            if 'head_imgs' in product:
                head_imgs = product['head_imgs']
                if not isinstance(head_imgs, list):
                    errors.append("主图必须是列表格式")
                    self.logger.warning("商品验证失败: 主图必须是列表格式")
                elif len(head_imgs) < 3 or len(head_imgs) > 9:
                    errors.append(f"主图数量必须在3-9张之间，当前: {len(head_imgs)}张")
                    self.logger.warning(f"商品验证失败: 主图数量({len(head_imgs)})不在有效范围内")
            
            # 验证类目格式
            for cats_field in ['cats', 'cats_v2']:
                if cats_field in product:
                    cats = product[cats_field]
                    if not isinstance(cats, list) or len(cats) != 3:
                        errors.append(f"类目格式不符合要求: {cats_field}")
                        self.logger.warning(f"商品验证失败: 类目格式不符合要求: {cats_field}")
                    else:
                        for cat in cats:
                            if 'cat_id' not in cat:
                                errors.append(f"类目缺少cat_id: {cat}")
                                self.logger.warning(f"商品验证失败: 类目缺少cat_id: {cat}")
                                break
            
            # 验证SKU
            if 'skus' in product:
                skus = product['skus']
                if not isinstance(skus, list):
                    errors.append("SKU必须是列表格式")
                    self.logger.warning("商品验证失败: SKU必须是列表格式")
                elif len(skus) == 0 or len(skus) > 500:
                    errors.append(f"SKU数量必须在1-500之间，当前: {len(skus)}个")
                    self.logger.warning(f"商品验证失败: SKU数量({len(skus)})不在有效范围内")
                else:
                    for sku in skus:
                        if not isinstance(sku, dict):
                            errors.append("SKU必须是字典格式")
                            self.logger.warning("商品验证失败: SKU必须是字典格式")
                            break
                        if 'price' not in sku:
                            errors.append("SKU缺少price字段")
                            self.logger.warning("商品验证失败: SKU缺少price字段")
                            break
                        if 'stock_num' not in sku:
                            errors.append("SKU缺少stock_num字段")
                            self.logger.warning("商品验证失败: SKU缺少stock_num字段")
                            break
                        if not isinstance(sku['price'], int) or sku['price'] <= 0:
                            errors.append(f"SKU价格无效: {sku['price']}")
                            self.logger.warning(f"商品验证失败: SKU价格无效: {sku['price']}")
                            break
                        if not isinstance(sku['stock_num'], int) or sku['stock_num'] < 0:
                            errors.append(f"SKU库存无效: {sku['stock_num']}")
                            self.logger.warning(f"商品验证失败: SKU库存无效: {sku['stock_num']}")
                            break
            
            # 验证发货方式相关字段
            if 'deliver_method' in product:
                deliver_method = product['deliver_method']
                if deliver_method == 0 and 'express_info' not in product:
                    errors.append("快递发货方式缺少express_info字段")
                    self.logger.warning("商品验证失败: 快递发货方式缺少express_info字段")
                elif deliver_method == 3 and 'deliver_acct_type' not in product:
                    errors.append("无需快递方式缺少deliver_acct_type字段")
                    self.logger.warning("商品验证失败: 无需快递方式缺少deliver_acct_type字段")
            
            # 验证商品详情
            if 'desc_info' in product:
                desc_info = product['desc_info']
                if not isinstance(desc_info, dict):
                    errors.append("商品详情必须是字典格式")
                    self.logger.warning("商品验证失败: 商品详情必须是字典格式")
                elif 'imgs' in desc_info and (
                    not isinstance(desc_info['imgs'], list) or len(desc_info['imgs']) == 0
                ):
                    errors.append("商品详情图片无效")
                    self.logger.warning("商品验证失败: 商品详情图片无效")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                self.logger.info(f"商品验证通过: {product.get('out_product_id', 'Unknown')}")
            else:
                self.logger.warning(f"商品验证失败，共 {len(errors)} 个错误")
            
            return ValidationResult(is_valid=is_valid, errors=errors, data=product)
            
        except Exception as e:
            self.logger.error(f"验证商品数据时发生错误: {str(e)}")
            return ValidationResult(is_valid=False, errors=[f"验证过程发生错误: {str(e)}"], data=product)
    

    
    @catch_exceptions(module_name="product_generator")
    def _generate_subtitle(self, title: str) -> str:
        """
        生成商品副标题
        
        :param title: 主标题
        :return: 副标题字符串
        :raises: ValidationError 当输入参数无效时
        :raises: OperationError 当生成副标题失败时
        """
        if not isinstance(title, str):
            self.logger.error("标题类型无效，必须是字符串格式")
            raise ValidationError("标题必须是字符串格式")
        
        try:
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
            
            self.logger.debug(f"生成副标题: '{subtitle}' 从原标题: '{title}'")
            return subtitle
        except Exception as e:
            self.logger.error(f"生成副标题失败: {str(e)}")
            raise OperationError(f"生成副标题失败: {str(e)}")
    
    @catch_exceptions(module_name="product_generator")
    def _generate_short_title(self, title: str) -> str:
        """
        生成商品短标题
        
        :param title: 主标题
        :return: 短标题字符串
        :raises: ValidationError 当输入参数无效时
        :raises: OperationError 当生成短标题失败时
        """
        if not isinstance(title, str):
            self.logger.error("标题类型无效，必须是字符串格式")
            raise ValidationError("标题必须是字符串格式")
        
        try:
            # 从主标题中提取前20个字符
            short_title = title[:20]
            
            self.logger.debug(f"生成短标题: '{short_title}' 从原标题: '{title}'")
            return short_title
        except Exception as e:
            self.logger.error(f"生成短标题失败: {str(e)}")
            raise OperationError(f"生成短标题失败: {str(e)}")
    
    @catch_exceptions(module_name="product_generator")
    def _generate_description(self) -> str:
        """
        生成商品描述
        
        :return: 描述字符串
        :raises: ConfigError 当配置获取失败时
        :raises: OperationError 当生成描述失败时
        """
        try:
            # 获取描述模板
            generation_config = self.get_generation_config()
            templates = generation_config.get('description_templates', ['这是一个商品描述'])
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
            
            self.logger.debug("成功生成商品描述")
            return description
        except Exception as e:
            self.logger.error(f"生成商品描述失败: {str(e)}")
            raise OperationError(f"生成商品描述失败: {str(e)}")
    
    @catch_exceptions(module_name="product_generator")
    def save_products_to_file(self, products: List[Dict[str, Any]], file_path: str) -> bool:
        """
        保存生成的商品到文件，并单独保存描述和图片URL
        
        :param products: 商品列表
        :param file_path: 文件路径
        :return: 是否成功
        :raises: ValidationError 当输入参数无效时
        :raises: OperationError 当保存文件失败时
        """
        if not isinstance(products, list):
            self.logger.error("商品数据类型无效，必须是列表格式")
            raise ValidationError("商品数据必须是列表格式")
        
        if not isinstance(file_path, str):
            self.logger.error("文件路径类型无效，必须是字符串格式")
            raise ValidationError("文件路径必须是字符串格式")
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 添加生成时间字段
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for product in products:
                product['generation_time'] = timestamp
            
            # 保存完整商品数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            # 单独保存描述和图片URL
            descriptions_and_images = []
            for product in products:
                item = {
                    'title': product.get('title', ''),
                    'description': product.get('desc_info', {}).get('text', ''),
                    'head_images': product.get('head_imgs', []),
                    'desc_images': product.get('desc_info', {}).get('imgs', [])
                }
                descriptions_and_images.append(item)
            
            # 保存描述和图片URL到单独文件
            base_name = os.path.splitext(file_path)[0]
            desc_img_file = f"{base_name}_descriptions_images.json"
            with open(desc_img_file, 'w', encoding='utf-8') as f:
                json.dump(descriptions_and_images, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"成功保存{len(products)}个商品到文件: {file_path}")
            self.logger.info(f"成功保存描述和图片URL到文件: {desc_img_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存商品到文件失败: {str(e)}")
            raise OperationError(f"保存商品到文件失败: {str(e)}")


@catch_exceptions(module_name="product_generator")
def generate_products(client_data: Dict[str, Any], 
                     product_count: int = 1, 
                     config_manager = None) -> List[Dict[str, Any]]:
    """
    生成商品数据的便捷函数
    
    :param client_data: 客户数据
    :param product_count: 需要生成的商品数量
    :param config_manager: 配置管理器实例
    :return: 商品列表
    :raises: ValidationError 当输入参数无效时
    :raises: OperationError 当生成商品失败时
    """
    # 参数验证
    if not isinstance(client_data, dict):
        logger = get_logger(__name__)
        logger.error("客户数据类型无效，必须是字典格式")
        raise ValidationError("客户数据必须是字典格式")
    
    if not isinstance(product_count, int) or product_count <= 0:
        logger = get_logger(__name__)
        logger.error("商品数量必须是正整数")
        raise ValidationError("商品数量必须是正整数")
    
    try:
        generator = ProductGenerator(config_manager)
        products = generator.generate_products(client_data, product_count)
        
        # 保存生成的商品到文件
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"generated_products_{timestamp}.json")
        generator.save_products_to_file(products, output_file)
        
        logger = get_logger(__name__)
        logger.info(f"便捷函数成功生成{len(products)}个商品并保存到文件")
        return products
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"便捷函数生成商品失败: {str(e)}")
        raise OperationError(f"生成商品失败: {str(e)}")


def main():
    """
    生成商品并准备上传的主函数
    """
    # 使用简单的客户数据，主要依赖sample_product_description.txt
    sample_client_data = {
        'course_name': '精品课程',  # 将从文件中读取更详细的描述
    }
    
    # 不使用配置管理器，直接使用环境变量配置
    print("使用环境变量配置生成商品...")
    
    # 生成单个商品
    generator = ProductGenerator()
    print("生成商品...")
    product = generator.generate_product(sample_client_data)
    
    if product:
        print(f"生成成功: {product['title']}")
        print(f"生成时间: {product.get('generation_time', 'N/A')}")
        print(f"价格: {product['skus'][0]['price']/100}元")
        print(f"主图数量: {len(product['head_imgs'])}")
        print(f"描述图片数量: {len(product.get('desc_info', {}).get('imgs', []))}")
    
    # 保存到文件
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"generated_product_{timestamp}.json")
    generator.save_products_to_file([product], output_file)
    print(f"商品已保存到 {output_file}")
    print(f"描述和图片URL已保存到 {os.path.splitext(output_file)[0]}_descriptions_images.json")
    print("\n商品生成完成，可以使用product_uploader进行上传")
    print("请确保已配置微信小店API的appid和appsecret")


if __name__ == "__main__":
    main()
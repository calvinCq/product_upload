#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
负责读取、解析和验证配置文件
提供获取不同类型配置的方法
"""

import json
import os
from datetime import datetime

# 尝试导入dotenv以支持.env文件配置
DOTENV_AVAILABLE = False
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件中的环境变量
    DOTENV_AVAILABLE = True
except ImportError:
    # 如果未安装dotenv库，不影响基本功能
    pass

# 导入现有的日志功能
from wechat_shop_api import log_message


class ConfigManager:
    """
    配置管理器类
    负责配置文件的加载、解析和验证
    """
    
    def __init__(self, config_path):
        """
        初始化配置管理器
        
        :param config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = {}
        self.is_loaded = False
        self.is_valid = False
        
    def load_config(self):
        """
        加载配置文件
        
        :return: 配置字典，如果加载失败返回空字典
        """
        try:
            if not os.path.exists(self.config_path):
                error_msg = f"配置文件不存在: {self.config_path}"
                log_message(error_msg, "ERROR")
                self.is_loaded = False
                return {}
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                
            self.is_loaded = True
            log_message(f"成功加载配置文件: {self.config_path}")
            return self.config
            
        except json.JSONDecodeError as e:
            error_msg = f"配置文件格式错误: {str(e)}"
            log_message(error_msg, "ERROR")
            self.is_loaded = False
            return {}
        except Exception as e:
            error_msg = f"加载配置文件失败: {str(e)}"
            log_message(error_msg, "ERROR")
            self.is_loaded = False
            return {}
    
    def validate_config(self):
        """
        验证配置有效性
        
        :return: 是否有效
        """
        if not self.is_loaded:
            if not self.config:
                self.load_config()
            if not self.is_loaded:
                return False
        
        # 基础必需部分
        required_sections = ['generation', 'upload', 'api', 'points']
        missing_sections = []
        
        # 检查必需的配置部分
        for section in required_sections:
            if section not in self.config:
                missing_sections.append(section)
        
        # 火山大模型配置为可选，但如果存在则验证其有效性
        if 'volcano_api' in self.config:
            volcano_config = self.config['volcano_api']
            if 'api_key' not in volcano_config or not volcano_config['api_key']:
                log_message("火山大模型API配置缺少api_key", "WARNING")
            if 'model_name' not in volcano_config or not volcano_config['model_name']:
                log_message("火山大模型API配置缺少model_name", "WARNING")
        
        # 钱多多API配置为可选，但如果存在则验证其有效性
        if 'qianduoduo_api' in self.config:
            qianduoduo_config = self.config['qianduoduo_api']
            if 'api_key' not in qianduoduo_config or not qianduoduo_config['api_key']:
                log_message("钱多多API配置缺少api_key", "WARNING")
            if 'model_name' not in qianduoduo_config or not qianduoduo_config['model_name']:
                log_message("钱多多API配置缺少model_name", "WARNING")
        
        if missing_sections:
            error_msg = f"配置文件缺少必需部分: {', '.join(missing_sections)}"
            log_message(error_msg, "ERROR")
            self.is_valid = False
            return False
        
        # 验证生成配置
        generation_config = self.config.get('generation', {})
        required_generation = ['product_count', 'category_ids', 'price_range']
        missing_generation = [field for field in required_generation if field not in generation_config]
        
        if missing_generation:
            error_msg = f"生成配置缺少必需字段: {', '.join(missing_generation)}"
            log_message(error_msg, "ERROR")
            self.is_valid = False
            return False
        
        # 验证上传配置
        upload_config = self.config.get('upload', {})
        required_upload = ['batch_size', 'request_interval', 'max_retries']
        missing_upload = [field for field in required_upload if field not in upload_config]
        
        if missing_upload:
            error_msg = f"上传配置缺少必需字段: {', '.join(missing_upload)}"
            log_message(error_msg, "ERROR")
            self.is_valid = False
            return False
        
        # 验证API配置
        api_config = self.config.get('api', {})
        required_api = ['appid', 'appsecret']
        missing_api = [field for field in required_api if field not in api_config or not api_config[field]]
        
        if missing_api:
            error_msg = f"API配置缺少必需字段: {', '.join(missing_api)}"
            log_message(error_msg, "ERROR")
            self.is_valid = False
            return False
        
        # 验证积分查询配置
        points_config = self.config.get('points', {})
        # 积分查询配置为可选，但如果提供了必须包含openids
        if points_config and 'openids' not in points_config:
            error_msg = "积分查询配置缺少openids字段"
            log_message(error_msg, "ERROR")
            self.is_valid = False
            return False
        
        self.is_valid = True
        log_message("配置验证通过")
        return True
    
    def get_generation_config(self):
        """
        获取生成配置
        
        :return: 生成配置字典
        """
        if not self.is_valid and not self.validate_config():
            log_message("配置无效，无法获取生成配置", "WARNING")
            return self._get_default_generation_config()
        
        generation_config = self.config.get('generation', {})
        # 合并默认值
        default_config = self._get_default_generation_config()
        for key, value in default_config.items():
            if key not in generation_config:
                generation_config[key] = value
        
        return generation_config
    
    def get_upload_config(self):
        """
        获取上传配置
        
        :return: 上传配置字典
        """
        if not self.is_valid and not self.validate_config():
            log_message("配置无效，无法获取上传配置", "WARNING")
            return self._get_default_upload_config()
        
        upload_config = self.config.get('upload', {})
        # 合并默认值
        default_config = self._get_default_upload_config()
        for key, value in default_config.items():
            if key not in upload_config:
                upload_config[key] = value
        
        return upload_config
    
    def get_points_config(self):
        """
        获取积分查询配置
        
        :return: 积分配置字典
        """
        if not self.is_valid and not self.validate_config():
            log_message("配置无效，无法获取积分配置", "WARNING")
            return self._get_default_points_config()
        
        points_config = self.config.get('points', {})
        # 合并默认值
        default_config = self._get_default_points_config()
        for key, value in default_config.items():
            if key not in points_config:
                points_config[key] = value
        
        return points_config
    
    def get_api_config(self):
        """
        获取API配置
        
        :return: API配置字典
        """
        if not self.is_valid and not self.validate_config():
            log_message("配置无效，无法获取API配置", "WARNING")
            return {}
        
        return self.config.get('api', {})
    
    def _get_default_generation_config(self):
        """
        获取默认的生成配置
        
        :return: 默认生成配置
        """
        return {
            'product_count': 10,
            'category_ids': [
                {'level1': '381003', 'level2': '380003', 'level3': '517050'}
            ],
            'price_range': [100, 9999],  # 价格范围（分）
            'stock_range': [10, 1000],   # 库存范围
            'title_templates': [
                "高品质{keyword}商品",
                "特价促销{keyword}",
                "精选{keyword}系列",
                "新品上市：{keyword}"
            ],
            'keywords': ['电子产品', '家居用品', '服装配饰', '美妆护肤', '食品饮料'],
            'description_templates': [
                "本商品质量优良，性价比高，值得购买。",
                "精选材质制作，耐用性强，使用体验好。",
                "时尚设计，简约大方，适合各种场合。"
            ],
            'main_images': [
                "https://example.com/product1.jpg",
                "https://example.com/product2.jpg",
                "https://example.com/product3.jpg"
            ],
            'detail_images': [
                "https://example.com/detail1.jpg",
                "https://example.com/detail2.jpg"
            ],
            'deliver_method': 0  # 默认快递发货
        }
    
    def get_volcano_api_config(self):
        """
        获取火山大模型API配置，支持多源配置优先级：配置文件 > 环境变量 > .env文件
        
        :return: 火山大模型API配置字典
        """
        # 如果配置无效，尝试验证
        if not self.is_valid:
            self.validate_config()
        
        # 获取火山大模型API配置，如果不存在则返回默认配置
        volcano_config = self.config.get('volcano_api', {})
        
        # 合并默认值
        default_config = self._get_default_volcano_api_config()
        for key, value in default_config.items():
            if key not in volcano_config:
                volcano_config[key] = value
        
        # 配置优先级处理：配置文件 > 环境变量 > .env文件
        # 1. 首先检查配置文件中是否有API key，如果没有则尝试从环境变量加载
        if not volcano_config.get('api_key'):
            # 2. 从环境变量加载
            api_key = os.environ.get('VOLCANO_API_KEY')
            if api_key:
                volcano_config['api_key'] = api_key
                log_message("从环境变量加载火山大模型API密钥", "INFO")
            elif DOTENV_AVAILABLE:
                log_message("未找到火山大模型API密钥，请检查配置文件或环境变量", "WARNING")
            else:
                log_message("未找到火山大模型API密钥，建议安装python-dotenv以支持.env文件配置", "WARNING")
        else:
            log_message("从配置文件加载火山大模型API密钥", "INFO")
        
        # 处理其他可能的环境变量配置
        env_config_mapping = {
            'VOLCANO_API_BASE_URL': 'api_base_url',
            'VOLCANO_MODEL_NAME': 'model_name',
            'VOLCANO_TIMEOUT': 'timeout',
            'VOLCANO_RETRY_COUNT': 'retry_count',
            'VOLCANO_MAIN_IMAGES_COUNT': 'main_images_count',
            'VOLCANO_DETAIL_IMAGES_COUNT': 'detail_images_count'
        }
        
        for env_var, config_key in env_config_mapping.items():
            env_value = os.environ.get(env_var)
            if env_value and not volcano_config.get(config_key):
                # 对于数值类型，尝试转换
                if config_key in ['timeout', 'retry_count', 'main_images_count', 'detail_images_count']:
                    try:
                        volcano_config[config_key] = int(env_value)
                    except ValueError:
                        log_message(f"环境变量{env_var}值不是有效的数字，忽略", "WARNING")
                else:
                    volcano_config[config_key] = env_value
                log_message(f"从环境变量加载火山配置项: {config_key}", "INFO")
        
        return volcano_config
    
    def get_qianduoduo_api_config(self):
        """
        获取钱多多API配置，支持多源配置优先级：配置文件 > 环境变量 > .env文件
        
        :return: 钱多多API配置字典
        """
        # 如果配置无效，尝试验证
        if not self.is_valid:
            self.validate_config()
        
        # 获取钱多多API配置，如果不存在则返回默认配置
        qianduoduo_config = self.config.get('qianduoduo_api', {})
        
        # 合并默认值
        default_config = self._get_default_qianduoduo_api_config()
        for key, value in default_config.items():
            if key not in qianduoduo_config:
                qianduoduo_config[key] = value
        
        # 配置优先级处理：配置文件 > 环境变量 > .env文件
        # 1. 首先检查配置文件中是否有API key，如果没有则尝试从环境变量加载
        if not qianduoduo_config.get('api_key'):
            # 2. 从环境变量加载
            api_key = os.environ.get('QIANDUODUO_API_KEY')
            if api_key:
                qianduoduo_config['api_key'] = api_key
                log_message("从环境变量加载钱多多API密钥", "INFO")
            elif DOTENV_AVAILABLE:
                # 使用内置默认密钥作为备选
                default_key = "sk-T3PbJoofAo22v5CzDhrFUhlVuX3MmPdUTRTswa7phYdZ6Q5g"
                qianduoduo_config['api_key'] = default_key
                log_message("使用默认钱多多API密钥", "INFO")
            else:
                # 使用内置默认密钥作为备选
                default_key = "sk-T3PbJoofAo22v5CzDhrFUhlVuX3MmPdUTRTswa7phYdZ6Q5g"
                qianduoduo_config['api_key'] = default_key
                log_message("使用默认钱多多API密钥", "INFO")
        else:
            log_message("从配置文件加载钱多多API密钥", "INFO")
        
        # 处理其他可能的环境变量配置
        env_config_mapping = {
            'QIANDUODUO_API_BASE_URL': 'api_base_url',
            'QIANDUODUO_MODEL_NAME': 'model_name',
            'QIANDUODUO_TIMEOUT': 'timeout',
            'QIANDUODUO_RETRY_COUNT': 'retry_count'
        }
        
        for env_var, config_key in env_config_mapping.items():
            env_value = os.environ.get(env_var)
            if env_value and not qianduoduo_config.get(config_key):
                # 对于数值类型，尝试转换
                if config_key in ['timeout', 'retry_count']:
                    try:
                        qianduoduo_config[config_key] = int(env_value)
                    except ValueError:
                        log_message(f"环境变量{env_var}值不是有效的数字，忽略", "WARNING")
                else:
                    qianduoduo_config[config_key] = env_value
                log_message(f"从环境变量加载钱多多配置项: {config_key}", "INFO")
        
        return qianduoduo_config
    
    def _get_default_volcano_api_config(self):
        """
        获取默认的火山大模型API配置
        
        :return: 默认火山大模型API配置
        """
        return {
            'api_key': '',
            'api_base_url': 'https://ark.cn-beijing.volces.com',
            'model_name': 'doubao-seedream-4-0-250828',
            'image_generation_endpoint': '/api/v3/images/generations',
            'timeout': 60,
            'retry_count': 3,
            'retry_delay': 5,
            'main_images_count': 1,
            'detail_images_count': 2,
            'image_save_dir': './temp_images',
            'max_image_size_mb': 5,
            'allowed_formats': ['.jpg', '.jpeg', '.png']
        }
    
    def _get_default_qianduoduo_api_config(self):
        """
        获取默认的钱多多API配置
        
        :return: 默认钱多多API配置
        """
        return {
            'api_key': 'sk-T3PbJoofAo22v5CzDhrFUhlVuX3MmPdUTRTswa7phYdZ6Q5g',  # 默认API密钥
            'api_base_url': 'https://api2.aigcbest.top',
            'model_name': 'DeepSeek-V3.1',  # 钱多多版本的DeepSeek-V3.1模型
            'text_generation_endpoint': '/v1/chat/completions',
            'image_generation_endpoint': '/v1/images/generations',
            'timeout': 60,
            'retry_count': 3,
            'retry_delay': 3,
            'main_images_count': 2,
            'detail_images_count': 1,
            'image_save_dir': './temp_images',
            'max_image_size_mb': 5,
            'allowed_formats': ['.jpg', '.jpeg', '.png']
        }
    
    def _get_default_upload_config(self):
        """
        获取默认的上传配置
        
        :return: 默认上传配置
        """
        return {
            'batch_size': 10,
            'request_interval': 2,      # 请求间隔（秒）
            'max_retries': 3,
            'retry_interval_base': 5,   # 重试间隔基数（秒）
            'enable_retry': True,
            'save_results': True,
            'results_file': f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    
    def _get_default_points_config(self):
        """
        获取默认的积分查询配置
        
        :return: 默认积分查询配置
        """
        return {
            'enabled': False,
            'openids': []
        }


def main():
    """
    测试配置管理器功能
    """
    # 测试使用，实际使用时不会直接调用
    import sys
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = 'product_generator_config.json'
    
    manager = ConfigManager(config_path)
    config = manager.load_config()
    
    if manager.validate_config():
        print("配置有效")
        print("\n生成配置:")
        print(manager.get_generation_config())
        print("\n上传配置:")
        print(manager.get_upload_config())
        print("\n积分配置:")
        print(manager.get_points_config())
        print("\nAPI配置:")
        print(manager.get_api_config())
    else:
        print("配置无效")


if __name__ == "__main__":
    main()
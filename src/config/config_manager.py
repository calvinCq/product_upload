#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
负责读取、解析和验证配置文件
提供获取不同类型配置的方法
统一管理钱多多API配置
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Union, List, Tuple

# 尝试导入dotenv以支持.env文件配置
DOTENV_AVAILABLE = False
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件中的环境变量
    DOTENV_AVAILABLE = True
except ImportError:
    # 如果未安装dotenv库，不影响基本功能
    pass

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入Logger模块
try:
    from src.utils.logger import Logger
except ImportError:
    # 如果Logger模块不存在，提供一个简单的日志实现
    class SimpleLogger:
        def __init__(self):
            self.name = "ConfigManager"
            
        def log(self, message: str, level: str = "INFO") -> None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] [{self.name}] {message}")
            
        def debug(self, message: str) -> None:
            self.log(message, "DEBUG")
            
        def info(self, message: str) -> None:
            self.log(message, "INFO")
            
        def warning(self, message: str) -> None:
            self.log(message, "WARNING")
            
        def error(self, message: str) -> None:
            self.log(message, "ERROR")
            
        def critical(self, message: str) -> None:
            self.log(message, "CRITICAL")
    
    Logger = SimpleLogger
    
# 获取日志实例
logger = Logger() if not hasattr(Logger, 'get_instance') else Logger.get_instance()


class ConfigManager:
    """
    配置管理器类
    负责配置文件的加载、解析和验证
    支持配置优先级：命令行参数 > 环境变量 > 配置文件 > 默认值
    """
    
    def __init__(self, config_path: Optional[str] = None, cli_args: Optional[Dict[str, Any]] = None):
        """
        初始化配置管理器
        
        :param config_path: 配置文件路径，如果为None则使用默认路径
        :param cli_args: 命令行参数字典，用于覆盖配置
        """
        self.config_path = config_path or "config.json"
        self.cli_args = cli_args or {}
        self.config = {}
        self.is_loaded = False
        self.is_valid = False
        self._cached_configs = {}  # 配置缓存
        # 初始化时自动加载配置
        self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        :return: 配置字典，如果加载失败返回空字典
        """
        try:
            if not os.path.exists(self.config_path):
                warning_msg = f"配置文件不存在: {self.config_path}"
                logger.warning(warning_msg)
                # 即使配置文件不存在，也继续执行，将使用默认配置
                self.config = {}
                self.is_loaded = True
                logger.info("使用默认配置")
                return self.config
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                
            self.is_loaded = True
            logger.info(f"成功加载配置文件: {self.config_path}")
            # 清空缓存，因为配置已更新
            self._cached_configs.clear()
            return self.config
            
        except json.JSONDecodeError as e:
            error_msg = f"配置文件格式错误: {str(e)}"
            logger.error(error_msg)
            self.is_loaded = False
            return {}
        except Exception as e:
            error_msg = f"加载配置文件失败: {str(e)}"
            logger.error(error_msg)
            self.is_loaded = False
            return {}
    
    def validate_config(self) -> bool:
        """
        验证配置有效性
        
        :return: 是否有效
        """
        if not self.is_loaded:
            if not self.config:
                self.load_config()
            if not self.is_loaded:
                logger.warning("配置未加载，无法验证")
                return False
        
        # 验证策略：采用宽松验证，即使缺少某些配置也能继续运行
        # 只对关键配置进行严格验证
        
        try:
            # 钱多多API配置验证（较宽松）
            if 'qianduoduo_api' not in self.config:
                logger.warning("配置缺少钱多多API配置部分，将使用默认配置")
            else:
                qianduoduo_config = self.config['qianduoduo_api']
                if 'api_key' not in qianduoduo_config or not qianduoduo_config['api_key']:
                    logger.warning("钱多多API配置缺少api_key，将使用默认值")
            
            # API配置验证（严格）
            api_config = self.config.get('api', {})
            required_api = ['appid', 'appsecret']
            missing_api = [field for field in required_api if field not in api_config or not api_config[field]]
            
            if missing_api:
                error_msg = f"API配置缺少必需字段: {', '.join(missing_api)}"
                logger.error(error_msg)
                self.is_valid = False
                return False
            
            # 验证上传配置
            upload_config = self.config.get('upload', {})
            if upload_config:
                # 验证批量大小是否为正整数
                if 'batch_size' in upload_config and (not isinstance(upload_config['batch_size'], int) or upload_config['batch_size'] <= 0):
                    logger.warning("上传配置中的batch_size无效，将使用默认值")
                # 验证请求间隔是否为非负数
                if 'request_interval' in upload_config and (not isinstance(upload_config['request_interval'], (int, float)) or upload_config['request_interval'] < 0):
                    logger.warning("上传配置中的request_interval无效，将使用默认值")
            
            self.is_valid = True
            logger.info("配置验证通过")
            return True
        except Exception as e:
            logger.error(f"配置验证过程中发生错误: {str(e)}")
            self.is_valid = False
            return False
    
    def _apply_config_priority(self, config_section: str, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用配置优先级：命令行参数 > 环境变量 > 配置文件 > 默认值
        
        :param config_section: 配置部分名称
        :param base_config: 基础配置（通常是默认配置）
        :return: 合并后的配置
        """
        try:
            # 1. 从配置文件获取对应部分的配置
            file_config = self.config.get(config_section, {})
            
            # 2. 递归合并配置文件配置到默认配置
            result_config = self._deep_merge_dicts(base_config, file_config)
            
            # 3. 应用环境变量配置
            self._apply_env_variables(result_config, config_section)
            
            # 4. 应用命令行参数（优先级最高）
            self._apply_cli_args(result_config, config_section)
            
            return result_config
        except Exception as e:
            logger.error(f"应用配置优先级时发生错误: {str(e)}")
            # 发生错误时返回基础配置
            return base_config.copy()
    
    def _deep_merge_dicts(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并两个字典
        
        :param base: 基础字典
        :param overlay: 覆盖字典
        :return: 合并后的字典
        """
        result = base.copy()
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    def _apply_env_variables(self, config: Dict[str, Any], section: str) -> None:
        """
        应用环境变量到配置字典
        
        :param config: 配置字典
        :param section: 配置部分名称
        """
        env_prefix = f"{section.upper()}_"
        for key in list(config.keys()):
            env_key = f"{env_prefix}{key.upper()}"
            env_value = os.environ.get(env_key)
            if env_value is not None:
                # 尝试根据目标类型转换值
                target_type = type(config[key])
                if target_type == int:
                    try:
                        config[key] = int(env_value)
                        logger.debug(f"从环境变量覆盖配置 {section}.{key} = {config[key]}")
                    except ValueError:
                        logger.warning(f"环境变量 {env_key} 值不是有效的整数，忽略")
                elif target_type == float:
                    try:
                        config[key] = float(env_value)
                        logger.debug(f"从环境变量覆盖配置 {section}.{key} = {config[key]}")
                    except ValueError:
                        logger.warning(f"环境变量 {env_key} 值不是有效的浮点数，忽略")
                elif target_type == bool:
                    # 处理布尔值
                    env_value_lower = env_value.lower()
                    if env_value_lower in ('true', 'yes', '1'):
                        config[key] = True
                        logger.debug(f"从环境变量覆盖配置 {section}.{key} = {config[key]}")
                    elif env_value_lower in ('false', 'no', '0'):
                        config[key] = False
                        logger.debug(f"从环境变量覆盖配置 {section}.{key} = {config[key]}")
                elif target_type == list and ',' in env_value:
                    # 尝试将逗号分隔的字符串转换为列表
                    config[key] = [item.strip() for item in env_value.split(',')]
                    logger.debug(f"从环境变量覆盖配置 {section}.{key} = {config[key]}")
                else:
                    # 其他类型直接使用
                    config[key] = env_value
                    logger.debug(f"从环境变量覆盖配置 {section}.{key} = {config[key]}")
    
    def _apply_cli_args(self, config: Dict[str, Any], section: str) -> None:
        """
        应用命令行参数到配置字典
        
        :param config: 配置字典
        :param section: 配置部分名称
        """
        section_prefix = f"{section}_"
        for key, value in self.cli_args.items():
            if key.startswith(section_prefix) and value is not None:
                config_key = key[len(section_prefix):]
                if config_key in config:
                    # 尝试进行类型转换以匹配目标类型
                    target_type = type(config[config_key])
                    if target_type != type(value) and value is not None:
                        try:
                            if target_type == int:
                                value = int(value)
                            elif target_type == float:
                                value = float(value)
                            elif target_type == bool:
                                if isinstance(value, str):
                                    value_lower = value.lower()
                                    value = value_lower in ('true', 'yes', '1')
                        except (ValueError, TypeError):
                            logger.warning(f"无法将命令行参数 {key} 转换为 {target_type.__name__} 类型，使用原始值")
                    
                    config[config_key] = value
                    logger.debug(f"从命令行参数覆盖配置 {section}.{config_key} = {config[config_key]}")
    
    def get_generation_config(self) -> Dict[str, Any]:
        """
        获取生成配置
        
        :return: 生成配置字典
        """
        # 检查缓存
        if 'generation' in self._cached_configs:
            return self._cached_configs['generation']
        
        # 验证配置
        if not self.is_valid:
            self.validate_config()
        
        # 应用配置优先级
        default_config = self._get_default_generation_config()
        generation_config = self._apply_config_priority('generation', default_config)
        
        # 验证生成配置的有效性
        self._validate_generation_config(generation_config)
        
        # 缓存结果
        self._cached_configs['generation'] = generation_config
        return generation_config
    
    def _validate_generation_config(self, config: Dict[str, Any]) -> None:
        """
        验证生成配置的有效性
        
        :param config: 生成配置字典
        """
        try:
            # 验证商品数量
            if 'product_count' in config and (not isinstance(config['product_count'], int) or config['product_count'] <= 0):
                logger.warning("生成配置中的product_count无效，将使用默认值")
                config['product_count'] = 10
            
            # 验证价格范围
            if 'price_range' in config and (not isinstance(config['price_range'], list) or len(config['price_range']) != 2):
                logger.warning("生成配置中的price_range无效，将使用默认值")
                config['price_range'] = [100, 9999]
            
            # 验证库存范围
            if 'stock_range' in config and (not isinstance(config['stock_range'], list) or len(config['stock_range']) != 2):
                logger.warning("生成配置中的stock_range无效，将使用默认值")
                config['stock_range'] = [10, 1000]
        except Exception as e:
            logger.error(f"验证生成配置时发生错误: {str(e)}")
    
    def get_upload_config(self) -> Dict[str, Any]:
        """
        获取上传配置
        
        :return: 上传配置字典
        """
        # 检查缓存
        if 'upload' in self._cached_configs:
            return self._cached_configs['upload']
        
        # 验证配置
        if not self.is_valid:
            self.validate_config()
        
        # 应用配置优先级
        default_config = self._get_default_upload_config()
        upload_config = self._apply_config_priority('upload', default_config)
        
        # 验证上传配置的有效性
        self._validate_upload_config(upload_config)
        
        # 缓存结果
        self._cached_configs['upload'] = upload_config
        return upload_config
    
    def _validate_upload_config(self, config: Dict[str, Any]) -> None:
        """
        验证上传配置的有效性
        
        :param config: 上传配置字典
        """
        try:
            # 验证批量大小
            if 'batch_size' in config and (not isinstance(config['batch_size'], int) or config['batch_size'] <= 0):
                logger.warning("上传配置中的batch_size无效，将使用默认值")
                config['batch_size'] = 10
            
            # 验证请求间隔
            if 'request_interval' in config and (not isinstance(config['request_interval'], (int, float)) or config['request_interval'] < 0):
                logger.warning("上传配置中的request_interval无效，将使用默认值")
                config['request_interval'] = 2
            
            # 验证重试次数
            if 'max_retries' in config and (not isinstance(config['max_retries'], int) or config['max_retries'] < 0):
                logger.warning("上传配置中的max_retries无效，将使用默认值")
                config['max_retries'] = 3
            
            # 验证重试间隔基数
            if 'retry_interval_base' in config and (not isinstance(config['retry_interval_base'], (int, float)) or config['retry_interval_base'] <= 0):
                logger.warning("上传配置中的retry_interval_base无效，将使用默认值")
                config['retry_interval_base'] = 5
        except Exception as e:
            logger.error(f"验证上传配置时发生错误: {str(e)}")
    
    def get_points_config(self) -> Dict[str, Any]:
        """
        获取积分查询配置
        
        :return: 积分配置字典
        """
        # 检查缓存
        if 'points' in self._cached_configs:
            return self._cached_configs['points']
        
        # 验证配置
        if not self.is_valid:
            self.validate_config()
        
        # 应用配置优先级
        default_config = self._get_default_points_config()
        points_config = self._apply_config_priority('points', default_config)
        
        # 缓存结果
        self._cached_configs['points'] = points_config
        return points_config
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        获取API配置
        
        :return: API配置字典
        """
        # 检查缓存
        if 'api' in self._cached_configs:
            return self._cached_configs['api']
        
        # 验证配置
        if not self.is_valid and not self.validate_config():
            logger.warning("配置无效，无法获取API配置")
            return {}
        
        # 获取默认API配置
        default_config = self._get_default_api_config()
        
        # 应用配置优先级
        api_config = self._apply_config_priority('api', default_config)
        
        # 缓存结果
        self._cached_configs['api'] = api_config
        return api_config
    
    def _get_default_api_config(self) -> Dict[str, Any]:
        """
        获取默认的API配置，优先从环境变量读取
        
        :return: 默认API配置
        """
        # 从配置文件获取API配置作为基础
        config_from_file = self.config.get('api', {})
        
        # 确保必需的字段存在
        default_api_config = {
            'appid': os.environ.get('WECHAT_APPID', '') or os.environ.get('WECHAT_APP_ID', ''),
            'appsecret': os.environ.get('WECHAT_APPSECRET', '') or os.environ.get('WECHAT_APP_SECRET', ''),
            'api_base_url': os.environ.get('WECHAT_API_BASE_URL', 'https://api.weixin.qq.com')
        }
        
        # 合并默认值和配置文件中的值
        for key, default_value in default_api_config.items():
            if key not in config_from_file or not config_from_file[key]:
                config_from_file[key] = default_value
        
        return config_from_file
    
    def _get_default_generation_config(self) -> Dict[str, Any]:
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
                "精选材质制作，耐用强劲，使用体验好。",
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
            'deliver_method': 0,  # 默认快递发货
            'enable_image_generation': True,  # 是否启用图片生成
            'image_aspect_ratio': '1:1'  # 图片宽高比
        }
    
    def get_qianduoduo_api_config(self) -> Dict[str, Any]:
        """
        获取钱多多API配置
        
        :return: 钱多多API配置字典
        """
        config_key = 'qianduoduo_api'
        if config_key in self._cached_configs:
            return self._cached_configs[config_key]
        
        try:
            # 初始化配置字典
            config = {
                'api_key': os.environ.get('QIANDUODUO_API_KEY', ''),
                'api_secret': os.environ.get('QIANDUODUO_API_SECRET', ''),
                'base_url': os.environ.get('QIANDUODUO_API_BASE_URL', 'https://api2.aigcbest.top'),
                'timeout': int(os.environ.get('QIANDUODUO_TIMEOUT', '30')),
                'image_model': os.environ.get('QIANDUODUO_IMAGE_MODEL', 'doubao-seedream-4-0-250828'),
                'text_model': os.environ.get('QIANDUODUO_TEXT_MODEL', 'DeepSeek-V3.1')
            }
            
            # 从主配置中加载
            if config_key in self.config:
                config.update(self.config[config_key])
            
            # 缓存并返回配置
            self._cached_configs[config_key] = config
            logger.info(f"钱多多API配置加载完成，使用图片模型: {config.get('image_model')}, 文本模型: {config.get('text_model')}")
            return config
        except Exception as e:
            logger.error(f"获取钱多多API配置时发生错误: {str(e)}")
            # 返回默认配置作为兜底
            return {
                'api_key': '',
                'api_secret': '',
                'base_url': 'https://api2.aigcbest.top',
                'timeout': 30,
                'image_model': 'doubao-seedream-4-0-250828',
                'text_model': 'DeepSeek-V3.1'
            }
    
    def get_volcano_api_config(self) -> Dict[str, Any]:
        """
        获取火山大模型API配置（兼容旧代码）
        
        :return: 火山大模型API配置字典
        """
        logger.warning("火山引擎API已废弃，建议使用钱多多API")
        return {}
    
    def _get_default_upload_config(self) -> Dict[str, Any]:
        """
        获取默认的上传配置
        
        :return: 默认上传配置
        """
        return {
            'batch_size': 5,
            'request_interval': 2.0,
            'max_retries': 3,
            'timeout': 30,
            'upload_url': 'https://api.weixin.qq.com/shop/product/add',
            'enable_verify': True
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取任意配置值
        
        :param key: 配置键，支持点表示法访问嵌套配置（如 'api.appid'）
        :param default: 默认值
        :return: 配置值或默认值
        """
        try:
            # 检查是否为嵌套键
            if '.' in key:
                keys = key.split('.')
                value = self.config
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                return value
            else:
                # 检查是否为预定义的配置部分
                if key in self._cached_configs:
                    return self._cached_configs[key]
                # 否则从原始配置中获取
                return self.config.get(key, default)
        except Exception as e:
            logger.error(f"获取配置时发生错误: {str(e)}")
            return default
    
    def reload_config(self) -> bool:
        """
        重新加载配置文件
        
        :return: 是否加载成功
        """
        try:
            self.is_loaded = False
            self.is_valid = False
            self._cached_configs.clear()
            return len(self.load_config()) > 0
        except Exception as e:
            logger.error(f"重新加载配置时发生错误: {str(e)}")
            return False
    
    def __str__(self) -> str:
        """
        返回配置管理器的字符串表示
        
        :return: 配置管理器的字符串表示
        """
        status = "有效" if self.is_valid else "无效"
        return f"ConfigManager(config_path={self.config_path}, status={status})"


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
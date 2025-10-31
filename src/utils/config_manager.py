#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
负责加载、验证和管理系统配置
支持从配置文件、环境变量和命令行参数加载配置
"""

import os
import json
from typing import Dict, Any, Optional

# 导入logger模块
from src.utils.logger import log_message

class ConfigManager:
    """
    配置管理器类
    提供配置的加载、验证和访问功能
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化配置管理器"""
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """
        加载配置
        优先级: 命令行参数 > 环境变量 > 配置文件
        """
        # 加载环境变量配置
        self._load_env_config()
        
        # 加载配置文件（如果存在）
        self._load_config_file()
    
    def _load_env_config(self):
        """
        从环境变量加载配置
        """
        # 微信小店API配置
        self.config['wechat_shop'] = {
            'app_id': os.environ.get('WECHAT_APPID', ''),
            'app_secret': os.environ.get('WECHAT_APPSECRET', ''),
            'api_base_url': os.environ.get('WECHAT_API_BASE_URL', 'https://api.weixin.qq.com')
        }
        
        # 钱多多API配置
        self.config['qianduoduo'] = {
            'api_key': os.environ.get('QIANDUODUO_API_KEY', ''),
            'api_base_url': os.environ.get('QIANDUODUO_API_BASE_URL', 'https://api.qianduoduo.com')
        }
    
    def _load_config_file(self):
        """
        从配置文件加载配置
        支持JSON格式的配置文件
        """
        config_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'config.json'
        )
        
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    
                # 合并配置
                self._merge_config(file_config)
                log_message(f"成功加载配置文件: {config_file_path}")
            except json.JSONDecodeError as e:
                log_message(f"配置文件格式错误: {str(e)}", "ERROR")
            except Exception as e:
                log_message(f"加载配置文件失败: {str(e)}", "ERROR")
        else:
            log_message(f"配置文件不存在: {config_file_path}", "WARNING")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """
        合并配置
        """
        for key, value in new_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                # 递归合并字典
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        支持通过点号分隔的路径访问嵌套配置
        
        :param key_path: 配置键路径，例如 'wechat_shop.app_id'
        :param default: 默认值
        :return: 配置值或默认值
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        设置配置值
        
        :param key_path: 配置键路径
        :param value: 配置值
        """
        keys = key_path.split('.')
        config = self.config
        
        # 导航到目标键的父级
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
    
    def validate(self) -> bool:
        """
        验证配置是否有效
        
        :return: 配置是否有效
        """
        # 验证微信小店API配置
        wechat_config = self.config.get('wechat_shop', {})
        if not wechat_config.get('app_id') or not wechat_config.get('app_secret'):
            log_message("微信小店API配置不完整，缺少app_id或app_secret", "ERROR")
            return False
        
        # 验证钱多多API配置（如果启用）
        qianduoduo_config = self.config.get('qianduoduo', {})
        if qianduoduo_config.get('enabled', False) and not qianduoduo_config.get('api_key'):
            log_message("钱多多API配置不完整，缺少api_key", "ERROR")
            return False
        
        log_message("配置验证通过")
        return True
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        获取完整配置
        
        :return: 完整配置字典
        """
        return self.config

# 创建全局配置管理器实例
config_manager = ConfigManager()

# 导出函数
def get_config() -> ConfigManager:
    """
    获取配置管理器实例
    
    :return: 配置管理器实例
    """
    return config_manager

def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    获取配置值的便捷函数
    
    :param key_path: 配置键路径
    :param default: 默认值
    :return: 配置值或默认值
    """
    return config_manager.get(key_path, default)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志工具模块
为整个系统提供统一的日志记录功能
"""

import os
import sys
import logging
import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler


class Logger:
    """
    自定义日志类
    提供简单易用的日志记录功能，支持日志轮转、彩色输出和多模块日志分离
    """
    
    # 日志级别映射
    LEVEL_MAP = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
        'FATAL': logging.CRITICAL
    }
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',       # 青色
        'INFO': '\033[32m',        # 绿色
        'WARNING': '\033[33m',     # 黄色
        'ERROR': '\033[31m',       # 红色
        'CRITICAL': '\033[35m',    # 紫色
        'RESET': '\033[0m'         # 重置
    }
    
    _instance = None
    
    def __new__(cls):
        """
        单例模式实现
        """
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._init_logger()
        return cls._instance
    
    def _init_logger(self):
        """
        初始化日志记录器
        """
        # 默认配置
        self.config = {
            'level': os.environ.get('LOG_LEVEL', 'INFO').upper(),
            'console_level': os.environ.get('LOG_CONSOLE_LEVEL', 'INFO').upper(),
            'file_level': os.environ.get('LOG_FILE_LEVEL', 'INFO').upper(),
            'log_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'),
            'max_bytes': int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024)),  # 10MB
            'backup_count': int(os.environ.get('LOG_BACKUP_COUNT', 5)),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'use_color': os.environ.get('LOG_USE_COLOR', 'True').lower() == 'true'
        }
        
        # 获取日志级别
        level = self.LEVEL_MAP.get(self.config['level'], logging.INFO)
        
        # 创建root logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)  # 捕获所有级别的日志
        
        # 清除已存在的handler
        self.root_logger.handlers.clear()
        
        # 创建控制台handler
        self._setup_console_handler()
        
        # 创建文件handler（带轮转功能）
        self._setup_file_handler()
        
        # 保存handler引用
        self.file_handler = None
        
        # 模块日志记录器缓存
        self.loggers: Dict[str, logging.Logger] = {}
    
    def _setup_console_handler(self):
        """
        设置控制台日志处理器
        """
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_level = self.LEVEL_MAP.get(self.config['console_level'], logging.INFO)
            console_handler.setLevel(console_level)
            
            # 创建格式化器
            formatter = logging.Formatter(
                self.config['format'],
                self.config['datefmt']
            )
            console_handler.setFormatter(formatter)
            
            # 添加handler到logger
            self.root_logger.addHandler(console_handler)
            self.console_handler = console_handler
        except Exception as e:
            # 如果控制台handler设置失败，降级处理
            print(f"警告: 设置控制台日志处理器失败: {str(e)}")
    
    def _setup_file_handler(self):
        """
        设置文件日志处理器（支持轮转）
        """
        try:
            # 创建日志目录
            if not os.path.exists(self.config['log_dir']):
                try:
                    os.makedirs(self.config['log_dir'], exist_ok=True)
                except OSError as e:
                    print(f"警告: 创建日志目录失败: {e}")
                    return
            
            # 生成日志文件名（按日期）
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.config['log_dir'], f'upload_product_{today}.log')
            
            # 创建轮转文件handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.config['max_bytes'],
                backupCount=self.config['backup_count'],
                encoding='utf-8'
            )
            
            file_level = self.LEVEL_MAP.get(self.config['file_level'], logging.INFO)
            file_handler.setLevel(file_level)
            
            # 创建文件格式化器
            file_formatter = logging.Formatter(
                self.config['format'],
                self.config['datefmt']
            )
            file_handler.setFormatter(file_formatter)
            
            # 添加handler到logger
            self.root_logger.addHandler(file_handler)
            self.file_handler = file_handler
        except Exception as e:
            # 如果文件handler设置失败，降级处理
            print(f"警告: 创建日志文件失败: {e}")
    
    def configure(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        配置日志系统
        
        :param config: 日志配置字典
        """
        if config:
            self.config.update(config)
            
            # 清除现有的处理器
            for handler in self.root_logger.handlers[:]:
                self.root_logger.removeHandler(handler)
            
            # 重置所有已创建的logger
            self.loggers.clear()
            
            # 重新设置处理器
            self._setup_console_handler()
            self._setup_file_handler()
            
            # 记录配置信息
            self.info(f"日志系统已重新配置: 级别={self.config['level']}, 控制台级别={self.config['console_level']}, 文件级别={self.config['file_level']}", 'logger')
    
    def get_logger(self, name: str = 'upload_product') -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        :param name: 日志记录器名称
        :return: logging.Logger实例
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            level = self.LEVEL_MAP.get(self.config['level'], logging.INFO)
            logger.setLevel(level)
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def log(self, message: str, level: str = 'INFO', name: str = 'upload_product', exc_info: bool = False):
        """
        记录日志
        
        :param message: 日志消息
        :param level: 日志级别
        :param name: 日志名称
        :param exc_info: 是否记录异常信息
        """
        level = level.upper()
        
        # 检查级别是否有效
        if level not in self.LEVEL_MAP:
            level = 'INFO'
        
        # 获取对应的logging级别
        log_level = self.LEVEL_MAP[level]
        
        # 获取或创建logger
        logger = self.get_logger(name)
        
        # 记录到logger
        logger.log(log_level, message, exc_info=exc_info)
        
        # 如果在控制台且支持彩色，则添加彩色输出
        if (self.config['use_color'] and sys.stdout.isatty() and level in self.COLORS and 
            log_level >= self.console_handler.level):
            colored_message = f"{self.COLORS[level]}{message}{self.COLORS['RESET']}"
            # 这里只是为了彩色输出到控制台，不通过logging模块避免重复记录
            print(colored_message)
    
    def debug(self, message: str, name: str = 'upload_product'):
        """
        记录DEBUG级别日志
        
        :param message: 日志消息
        :param name: 日志名称
        """
        self.log(message, 'DEBUG', name)
    
    def info(self, message: str, name: str = 'upload_product'):
        """
        记录INFO级别日志
        
        :param message: 日志消息
        :param name: 日志名称
        """
        self.log(message, 'INFO', name)
    
    def warning(self, message: str, name: str = 'upload_product'):
        """
        记录WARNING级别日志
        
        :param message: 日志消息
        :param name: 日志名称
        """
        self.log(message, 'WARNING', name)
    
    def error(self, message: str, name: str = 'upload_product', exc_info: bool = True):
        """
        记录ERROR级别日志
        
        :param message: 日志消息
        :param name: 日志名称
        :param exc_info: 是否记录异常信息
        """
        self.log(message, 'ERROR', name, exc_info)
    
    def critical(self, message: str, name: str = 'upload_product', exc_info: bool = True):
        """
        记录CRITICAL级别日志
        
        :param message: 日志消息
        :param name: 日志名称
        :param exc_info: 是否记录异常信息
        """
        self.log(message, 'CRITICAL', name, exc_info)
    
    def exception(self, message: str, name: str = 'upload_product'):
        """
        记录异常信息
        
        :param message: 日志消息
        :param name: 日志名称
        """
        self.log(message, 'ERROR', name, exc_info=True)
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        :param level: 日志级别字符串
        """
        level = level.upper()
        if level in self.LEVEL_MAP:
            self.config['level'] = level
            for logger in self.loggers.values():
                logger.setLevel(self.LEVEL_MAP[level])
            self.console_handler.setLevel(self.LEVEL_MAP[level])
            self.info(f"日志级别已设置为: {level}", 'logger')


# 创建全局日志实例
logger_instance: Optional[Logger] = None


def get_logger(name: str = 'upload_product') -> Logger:
    """
    获取日志实例
    
    :param name: 日志名称
    :return: Logger实例
    """
    global logger_instance
    if logger_instance is None:
        logger_instance = Logger()
    
    # 向后兼容：如果调用get_logger()并提供name，返回Logger实例但记录警告
    if name != 'upload_product':
        logger_instance.warning(f"调用get_logger()时提供name参数已废弃，请使用logger_instance.get_logger(name)替代", 'logger')
    
    return logger_instance


def log_message(message: str, level: str = 'INFO', name: str = 'upload_product') -> None:
    """
    记录日志的便捷函数
    
    :param message: 日志消息
    :param level: 日志级别
    :param name: 日志名称
    """
    logger = get_logger()
    logger.log(message, level, name)


def debug(message: str, name: str = 'upload_product') -> None:
    """
    记录DEBUG级别日志的便捷函数
    
    :param message: 日志消息
    :param name: 日志名称
    """
    log_message(message, 'DEBUG', name)


def info(message: str, name: str = 'upload_product') -> None:
    """
    记录INFO级别日志的便捷函数
    
    :param message: 日志消息
    :param name: 日志名称
    """
    log_message(message, 'INFO', name)


def warning(message: str, name: str = 'upload_product') -> None:
    """
    记录WARNING级别日志的便捷函数
    
    :param message: 日志消息
    :param name: 日志名称
    """
    log_message(message, 'WARNING', name)


def error(message: str, name: str = 'upload_product', exc_info: bool = True) -> None:
    """
    记录ERROR级别日志的便捷函数
    
    :param message: 日志消息
    :param name: 日志名称
    :param exc_info: 是否记录异常信息
    """
    logger = get_logger()
    logger.error(message, name, exc_info)


def critical(message: str, name: str = 'upload_product', exc_info: bool = True) -> None:
    """
    记录CRITICAL级别日志的便捷函数
    
    :param message: 日志消息
    :param name: 日志名称
    :param exc_info: 是否记录异常信息
    """
    logger = get_logger()
    logger.critical(message, name, exc_info)


def exception(message: str, name: str = 'upload_product') -> None:
    """
    记录异常信息的便捷函数
    
    :param message: 日志消息
    :param name: 日志名称
    """
    logger = get_logger()
    logger.exception(message, name)


def set_log_level(level: str) -> None:
    """
    设置日志级别
    
    :param level: 日志级别
    """
    logger = get_logger()
    logger.set_level(level)


def configure_logger(config: Optional[Dict[str, Any]] = None) -> None:
    """
    配置日志系统
    
    :param config: 日志配置字典
    """
    logger = get_logger()
    logger.configure(config)


def test_logger():
    """
    测试日志功能
    """
    # 设置为DEBUG级别以测试所有日志
    set_log_level('DEBUG')
    
    # 测试各种级别
    debug("这是一条调试信息")
    info("这是一条普通信息")
    warning("这是一条警告信息")
    
    try:
        1 / 0
    except Exception:
        error("这是一条错误信息")
        exception("这是一条带异常栈的错误信息")
    
    critical("这是一条严重错误信息")
    
    # 测试命名日志器
    logger = get_logger()
    app_logger = logger.get_logger("app")
    app_logger.info("应用程序特定的日志信息")
    
    # 测试配置更新
    configure_logger({
        'level': 'INFO',
        'console_level': 'DEBUG',
        'file_level': 'INFO'
    })
    
    debug("这条调试日志应该只显示在控制台")
    info("这条信息日志应该同时显示在控制台和文件中")
    
    print("\n日志测试完成，请检查logs目录下的日志文件")


if __name__ == '__main__':
    test_logger()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异常处理模块
提供统一的异常类和错误处理工具
"""

from typing import Optional, Dict, Any, Union
import sys
import traceback

# 导入日志模块
from src.utils.logger import error, exception as log_exception


class BaseError(Exception):
    """
    基础异常类
    所有自定义异常都继承自此类
    """
    
    def __init__(self, message: str, code: str = 'UNKNOWN_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化基础异常
        
        :param message: 错误消息
        :param code: 错误代码
        :param details: 错误详情
        :param cause: 原始异常
        """
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause
        self.timestamp = None  # 可以在日志记录时添加
        
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """
        返回异常的字符串表示
        """
        return f"{self.__class__.__name__} [{self.code}]: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典格式
        
        :return: 异常信息字典
        """
        result = {
            'error': self.__class__.__name__,
            'code': self.code,
            'message': self.message
        }
        
        if self.details:
            result['details'] = self.details
        
        if self.cause:
            result['cause'] = str(self.cause)
        
        return result


class ConfigError(BaseError):
    """
    配置相关异常
    """
    
    def __init__(self, message: str, code: str = 'CONFIG_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        super().__init__(message, code, details, cause)


class ValidationError(BaseError):
    """
    验证相关异常
    """
    
    def __init__(self, message: str, field: Optional[str] = None,
                 code: str = 'VALIDATION_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化验证异常
        
        :param message: 错误消息
        :param field: 验证失败的字段名
        :param code: 错误代码
        :param details: 错误详情
        :param cause: 原始异常
        """
        super().__init__(message, code, details, cause)
        self.field = field
        
        if field and 'field' not in self.details:
            self.details['field'] = field


class APIError(BaseError):
    """
    API调用相关异常
    """
    
    def __init__(self, message: str, api_name: str, 
                 code: str = 'API_ERROR', status_code: Optional[int] = None,
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化API异常
        
        :param message: 错误消息
        :param api_name: API名称
        :param code: 错误代码
        :param status_code: HTTP状态码（如果适用）
        :param details: 错误详情
        :param cause: 原始异常
        """
        super().__init__(message, code, details, cause)
        self.api_name = api_name
        self.status_code = status_code
        
        if 'api_name' not in self.details:
            self.details['api_name'] = api_name
        
        if status_code and 'status_code' not in self.details:
            self.details['status_code'] = status_code


class NetworkError(BaseError):
    """
    网络相关异常
    """
    
    def __init__(self, message: str, url: Optional[str] = None,
                 code: str = 'NETWORK_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化网络异常
        
        :param message: 错误消息
        :param url: 请求的URL
        :param code: 错误代码
        :param details: 错误详情
        :param cause: 原始异常
        """
        super().__init__(message, code, details, cause)
        self.url = url
        
        if url and 'url' not in self.details:
            self.details['url'] = url


class FileError(BaseError):
    """
    文件操作相关异常
    """
    
    def __init__(self, message: str, file_path: Optional[str] = None,
                 code: str = 'FILE_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化文件异常
        
        :param message: 错误消息
        :param file_path: 文件路径
        :param code: 错误代码
        :param details: 错误详情
        :param cause: 原始异常
        """
        super().__init__(message, code, details, cause)
        self.file_path = file_path
        
        if file_path and 'file_path' not in self.details:
            self.details['file_path'] = file_path


class ProcessingError(BaseError):
    """
    处理过程相关异常
    """
    
    def __init__(self, message: str, process_name: Optional[str] = None,
                 code: str = 'PROCESSING_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化处理异常
        
        :param message: 错误消息
        :param process_name: 处理过程名称
        :param code: 错误代码
        :param details: 错误详情
        :param cause: 原始异常
        """
        super().__init__(message, code, details, cause)
        self.process_name = process_name
        
        if process_name and 'process_name' not in self.details:
            self.details['process_name'] = process_name


class TimeoutError(BaseError):
    """
    超时相关异常
    """
    
    def __init__(self, message: str, timeout: Optional[float] = None,
                 code: str = 'TIMEOUT_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化超时异常
        
        :param message: 错误消息
        :param timeout: 超时时间（秒）
        :param code: 错误代码
        :param details: 错误详情
        :param cause: 原始异常
        """
        super().__init__(message, code, details, cause)
        self.timeout = timeout
        
        if timeout is not None and 'timeout' not in self.details:
            self.details['timeout'] = timeout


class RateLimitError(BaseError):
    """
    速率限制相关异常
    """
    
    def __init__(self, message: str, retry_after: Optional[float] = None,
                 code: str = 'RATE_LIMIT_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化速率限制异常
        
        :param message: 错误消息
        :param retry_after: 建议重试时间（秒）
        :param code: 错误代码
        :param details: 错误详情
        :param cause: 原始异常
        """
        super().__init__(message, code, details, cause)
        self.retry_after = retry_after
        
        if retry_after is not None and 'retry_after' not in self.details:
            self.details['retry_after'] = retry_after


class OperationError(BaseError):
    """
    操作执行相关异常
    用于表示业务操作执行失败的情况
    """
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 code: str = 'OPERATION_ERROR', 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        初始化操作异常
        
        :param message: 错误消息
        :param operation: 操作名称
        :param code: 错误代码
        :param details: 错误详情
        :param cause: 原始异常
        """
        super().__init__(message, code, details, cause)
        self.operation = operation
        
        if operation and 'operation' not in self.details:
            self.details['operation'] = operation


def handle_exception(e: Exception, module_name: str = 'general',
                    re_raise: bool = False) -> Dict[str, Any]:
    """
    统一异常处理函数
    
    :param e: 捕获的异常
    :param module_name: 模块名称
    :param re_raise: 是否重新抛出异常
    :return: 错误信息字典
    """
    error_info = {}
    
    try:
        # 根据异常类型进行处理
        if isinstance(e, BaseError):
            # 处理自定义异常
            error_info = e.to_dict()
            log_exception(f"{e.__class__.__name__} [{e.code}]: {e.message}", module_name)
        else:
            # 处理标准异常
            error_info = {
                'error': e.__class__.__name__,
                'code': 'SYSTEM_ERROR',
                'message': str(e)
            }
            # 记录完整的异常栈
            log_exception(f"未处理的异常: {str(e)}", module_name)
        
        # 如果需要重新抛出异常
        if re_raise:
            raise
        
        return error_info
    except Exception as handler_error:
        # 异常处理过程中发生的错误
        print(f"异常处理失败: {handler_error}")
        print(f"原始异常: {e}")
        traceback.print_exc()
        return {
            'error': 'ErrorHandlerFailure',
            'code': 'ERROR_HANDLER_FAILURE',
            'message': '异常处理过程中发生错误',
            'details': {
                'original_error': str(e),
                'handler_error': str(handler_error)
            }
        }


def catch_exceptions(module_name: str = 'general', re_raise: bool = False):
    """
    异常捕获装饰器
    
    :param module_name: 模块名称
    :param re_raise: 是否重新抛出异常
    :return: 装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return handle_exception(e, module_name, re_raise)
        return wrapper
    return decorator


def format_error_message(error: Union[Exception, Dict[str, Any]]) -> str:
    """
    格式化错误信息为可读字符串
    
    :param error: 错误对象或错误信息字典
    :return: 格式化后的错误字符串
    """
    if isinstance(error, Exception):
        if isinstance(error, BaseError):
            return str(error)
        else:
            return f"{error.__class__.__name__}: {str(error)}"
    elif isinstance(error, dict):
        error_type = error.get('error', 'UnknownError')
        code = error.get('code', 'UNKNOWN')
        message = error.get('message', '')
        return f"{error_type} [{code}]: {message}"
    else:
        return str(error)


if __name__ == '__main__':
    # 测试异常类和处理函数
    
    print("测试异常处理模块...")
    
    try:
        # 测试基础异常
        raise BaseError("这是一个基础异常", code="TEST_ERROR", details={"test": "value"})
    except Exception as e:
        print(f"捕获到基础异常: {e}")
        print(f"异常字典: {e.to_dict() if isinstance(e, BaseError) else {}}")
    
    try:
        # 测试配置异常
        raise ConfigError("配置文件不存在", details={"file": "config.json"})
    except Exception as e:
        print(f"捕获到配置异常: {e}")
        print(f"异常字典: {e.to_dict() if isinstance(e, BaseError) else {}}")
    
    try:
        # 测试API异常
        raise APIError("API调用失败", api_name="wechat.upload", status_code=500)
    except Exception as e:
        print(f"捕获到API异常: {e}")
        print(f"异常字典: {e.to_dict() if isinstance(e, BaseError) else {}}")
    
    # 测试异常处理函数
    try:
        1 / 0
    except Exception as e:
        error_info = handle_exception(e, module_name="test_module")
        print(f"异常处理结果: {error_info}")
    
    # 测试异常装饰器
    @catch_exceptions(module_name="decorator_test")
    def test_function():
        raise ValueError("测试装饰器")
    
    result = test_function()
    print(f"装饰器处理结果: {result}")
    
    # 测试错误格式化
    formatted = format_error_message(ValueError("测试格式化"))
    print(f"格式化结果: {formatted}")
    
    formatted_dict = format_error_message({"error": "TestError", "code": "TEST", "message": "测试字典格式化"})
    print(f"格式化字典结果: {formatted_dict}")
    
    print("\n异常处理模块测试完成")
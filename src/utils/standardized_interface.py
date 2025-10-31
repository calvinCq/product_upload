#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
标准化接口模块
提供统一的数据结构和模块间通信规范
"""

from typing import Dict, Any, List, Optional, TypedDict, Union, Generic, TypeVar
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json

# 导入自定义异常
from src.utils.exceptions import ValidationError


# 类型变量
T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BaseResponse(Generic[T]):
    """
    基础响应数据结构
    """
    success: bool = False
    data: Optional[T] = None
    message: str = ""
    code: str = "SUCCESS"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        """
        result = asdict(self)
        # 处理datetime类型
        if isinstance(result.get('timestamp'), datetime):
            result['timestamp'] = result['timestamp'].isoformat()
        return result
    
    def to_json(self) -> str:
        """
        转换为JSON字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def __bool__(self) -> bool:
        """
        允许直接使用if response判断是否成功
        """
        return self.success


class ClientInfo(TypedDict, total=False):
    """
    客户信息数据结构
    """
    client_id: str  # 客户ID
    client_name: str  # 客户名称
    contact_person: str  # 联系人
    contact_phone: str  # 联系电话
    contact_email: str  # 联系邮箱
    address: str  # 地址
    business_scope: str  # 业务范围
    preferences: Dict[str, Any]  # 偏好设置
    additional_info: Dict[str, Any]  # 附加信息


class ProductInfo(TypedDict, total=False):
    """
    商品信息数据结构
    """
    product_id: str  # 商品ID
    title: str  # 商品标题
    description: str  # 商品描述
    price: float  # 商品价格
    original_price: float  # 原价
    category: str  # 商品分类
    tags: List[str]  # 商品标签
    images: List[str]  # 图片URL列表
    attributes: Dict[str, Any]  # 商品属性
    specs: List[Dict[str, Any]]  # 商品规格
    stock: int  # 库存
    sales: int  # 销量
    status: str  # 状态
    created_at: str  # 创建时间
    updated_at: str  # 更新时间
    source: str  # 来源
    additional_data: Dict[str, Any]  # 附加数据


class UploadResult(TypedDict, total=False):
    """
    上传结果数据结构
    """
    product_id: str  # 商品ID
    platform_id: str  # 平台商品ID
    status: str  # 上传状态
    message: str  # 消息
    created_at: str  # 创建时间
    errors: List[str]  # 错误信息
    warnings: List[str]  # 警告信息


class BatchUploadResult(TypedDict, total=False):
    """
    批量上传结果数据结构
    """
    total: int  # 总数
    success: int  # 成功数量
    failed: int  # 失败数量
    skipped: int  # 跳过数量
    results: List[UploadResult]  # 详细结果
    start_time: str  # 开始时间
    end_time: str  # 结束时间
    duration: float  # 耗时（秒）


class GenerateRequest(TypedDict, total=False):
    """
    生成请求数据结构
    """
    client_info: ClientInfo  # 客户信息
    num_products: int  # 生成数量
    template_id: Optional[str]  # 模板ID
    category: Optional[str]  # 商品分类
    keywords: List[str]  # 关键词
    requirements: Dict[str, Any]  # 生成要求
    image_options: Dict[str, Any]  # 图片生成选项


class UploadRequest(TypedDict, total=False):
    """
    上传请求数据结构
    """
    products: List[ProductInfo]  # 商品列表
    platform: str  # 平台标识
    batch_size: int  # 批次大小
    retry_count: int  # 重试次数
    timeout: float  # 超时时间
    sandbox: bool  # 沙箱模式


class ValidationResult(TypedDict, total=False):
    """
    验证结果数据结构
    """
    valid: bool  # 是否有效
    errors: List[Dict[str, Any]]  # 错误列表
    warnings: List[Dict[str, Any]]  # 警告列表
    score: Optional[float]  # 评分


class ProgressTracker:
    """
    进度跟踪器
    用于跟踪长时间运行任务的进度
    """
    
    def __init__(self, total: int, task_name: str = ""):
        """
        初始化进度跟踪器
        
        :param total: 总任务数
        :param task_name: 任务名称
        """
        self.total = total
        self.current = 0
        self.task_name = task_name
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()
        self.completed_tasks: List[str] = []
        self.failed_tasks: Dict[str, str] = {}
    
    def update(self, increment: int = 1, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        更新进度
        
        :param increment: 增加的进度
        :param task_id: 任务ID
        :return: 进度信息
        """
        self.current = min(self.current + increment, self.total)
        self.last_update_time = datetime.now()
        
        if task_id:
            self.completed_tasks.append(task_id)
        
        return self.get_progress()
    
    def mark_failed(self, task_id: str, error_message: str) -> None:
        """
        标记任务失败
        
        :param task_id: 任务ID
        :param error_message: 错误消息
        """
        self.failed_tasks[task_id] = error_message
    
    def get_progress(self) -> Dict[str, Any]:
        """
        获取当前进度
        
        :return: 进度信息字典
        """
        progress_percent = (self.current / self.total * 100) if self.total > 0 else 0
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "task_name": self.task_name,
            "current": self.current,
            "total": self.total,
            "progress_percent": round(progress_percent, 2),
            "elapsed_time": round(elapsed_time, 2),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "is_complete": self.current >= self.total
        }
    
    def is_complete(self) -> bool:
        """
        检查是否完成
        
        :return: 是否已完成
        """
        return self.current >= self.total


class DataValidator:
    """
    数据验证器
    提供通用的数据验证功能
    """
    
    @staticmethod
    def validate_client_info(client_info: Dict[str, Any]) -> ValidationResult:
        """
        验证客户信息
        
        :param client_info: 客户信息字典
        :return: 验证结果
        """
        errors = []
        warnings = []
        
        # 检查必填字段
        required_fields = ['client_id', 'client_name', 'contact_person', 'contact_phone']
        for field in required_fields:
            if field not in client_info or not client_info[field]:
                errors.append({
                    'field': field,
                    'message': f'必填字段 {field} 不能为空'
                })
        
        # 验证联系电话格式
        if 'contact_phone' in client_info and client_info['contact_phone']:
            phone = client_info['contact_phone']
            # 简单的中国手机号验证
            if len(phone) != 11 or not phone.isdigit():
                warnings.append({
                    'field': 'contact_phone',
                    'message': f'联系电话格式可能不正确: {phone}'
                })
        
        # 验证邮箱格式
        if 'contact_email' in client_info and client_info['contact_email']:
            email = client_info['contact_email']
            if '@' not in email or '.' not in email.split('@')[1]:
                warnings.append({
                    'field': 'contact_email',
                    'message': f'邮箱格式可能不正确: {email}'
                })
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def validate_product_info(product: Dict[str, Any]) -> ValidationResult:
        """
        验证商品信息
        
        :param product: 商品信息字典
        :return: 验证结果
        """
        errors = []
        warnings = []
        
        # 检查必填字段
        required_fields = ['title', 'description', 'price', 'category']
        for field in required_fields:
            if field not in product or not product[field]:
                errors.append({
                    'field': field,
                    'message': f'必填字段 {field} 不能为空'
                })
        
        # 验证价格
        if 'price' in product:
            try:
                price = float(product['price'])
                if price < 0:
                    errors.append({
                        'field': 'price',
                        'message': '价格不能为负数'
                    })
            except (ValueError, TypeError):
                errors.append({
                    'field': 'price',
                    'message': '价格必须是数字'
                })
        
        # 验证库存
        if 'stock' in product:
            try:
                stock = int(product['stock'])
                if stock < 0:
                    warnings.append({
                        'field': 'stock',
                        'message': '库存不能为负数'
                    })
            except (ValueError, TypeError):
                warnings.append({
                    'field': 'stock',
                    'message': '库存必须是整数'
                })
        
        # 验证图片列表
        if 'images' in product and product['images']:
            if not isinstance(product['images'], list):
                errors.append({
                    'field': 'images',
                    'message': '图片必须是列表格式'
                })
            elif len(product['images']) == 0:
                warnings.append({
                    'field': 'images',
                    'message': '建议至少提供一张商品图片'
                })
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def validate_batch_products(products: List[Dict[str, Any]]) -> ValidationResult:
        """
        验证批量商品信息
        
        :param products: 商品列表
        :return: 验证结果
        """
        if not isinstance(products, list):
            return {
                'valid': False,
                'errors': [{'field': 'products', 'message': '商品必须是列表格式'}],
                'warnings': []
            }
        
        if not products:
            return {
                'valid': False,
                'errors': [{'field': 'products', 'message': '商品列表不能为空'}],
                'warnings': []
            }
        
        # 验证每个商品
        all_errors = []
        all_warnings = []
        
        for idx, product in enumerate(products):
            result = DataValidator.validate_product_info(product)
            if not result['valid']:
                for error in result['errors']:
                    all_errors.append({
                        'field': error['field'],
                        'message': f'商品[{idx}]: {error["message"]}'
                    })
            
            for warning in result['warnings']:
                all_warnings.append({
                    'field': warning['field'],
                    'message': f'商品[{idx}]: {warning["message"]}'
                })
        
        return {
            'valid': len(all_errors) == 0,
            'errors': all_errors,
            'warnings': all_warnings,
            'score': 100 - (len(all_errors) * 10 + len(all_warnings) * 2)  # 简单评分
        }


class InterfaceFactory:
    """
    接口工厂
    用于创建标准化的请求和响应对象
    """
    
    @staticmethod
    def create_success_response(data: Optional[Any] = None, 
                              message: str = "操作成功") -> BaseResponse:
        """
        创建成功响应
        
        :param data: 响应数据
        :param message: 响应消息
        :return: 成功响应对象
        """
        return BaseResponse(
            success=True,
            data=data,
            message=message,
            code="SUCCESS"
        )
    
    @staticmethod
    def create_error_response(message: str, code: str = "ERROR") -> BaseResponse:
        """
        创建错误响应
        
        :param message: 错误消息
        :param code: 错误代码
        :return: 错误响应对象
        """
        return BaseResponse(
            success=False,
            data=None,
            message=message,
            code=code
        )
    
    @staticmethod
    def create_validation_error_response(result: ValidationResult) -> BaseResponse:
        """
        创建验证错误响应
        
        :param result: 验证结果
        :return: 验证错误响应对象
        """
        error_messages = [f"{err.get('field', 'unknown')}: {err.get('message', '')}" 
                         for err in result.get('errors', [])]
        message = "; ".join(error_messages) if error_messages else "验证失败"
        
        return BaseResponse(
            success=False,
            data=result,
            message=message,
            code="VALIDATION_ERROR"
        )


# 导出所有类和函数
__all__ = [
    'BaseResponse',
    'ClientInfo',
    'ProductInfo',
    'UploadResult',
    'BatchUploadResult',
    'GenerateRequest',
    'UploadRequest',
    'ValidationResult',
    'ProgressTracker',
    'DataValidator',
    'InterfaceFactory'
]


if __name__ == "__main__":
    # 测试标准化接口模块
    
    print("测试标准化接口模块...")
    
    # 测试响应对象
    success_resp = InterfaceFactory.create_success_response({"key": "value"}, "测试成功")
    print(f"成功响应: {success_resp.to_json()}")
    
    error_resp = InterfaceFactory.create_error_response("测试失败", "TEST_ERROR")
    print(f"错误响应: {error_resp.to_json()}")
    
    # 测试数据验证
    client_info = {
        "client_id": "123",
        "client_name": "测试客户",
        "contact_person": "张三",
        "contact_phone": "13800138000"
    }
    
    validation_result = DataValidator.validate_client_info(client_info)
    print(f"客户信息验证结果: {validation_result}")
    
    # 测试进度跟踪器
    tracker = ProgressTracker(10, "测试任务")
    tracker.update(task_id="task1")
    tracker.update(2)
    print(f"进度信息: {tracker.get_progress()}")
    
    print("\n标准化接口模块测试完成")
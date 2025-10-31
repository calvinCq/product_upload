#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主程序入口
负责协调整个商品生成和上传流程
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, Any, Optional, List

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入核心模块
from config.config_manager import ConfigManager
from data.data_loader import DataLoader
from core.product_generator import ProductGenerator
from core.product_uploader import ProductUploader
from api.wechat_shop_api import WeChatShopAPI

# 导入工具模块
from src.utils.logger import log_message, get_logger
from src.utils.exceptions import ConfigError, ValidationError, APIError, handle_exception, catch_exceptions
from src.utils.standardized_interface import (
    BaseResponse, ClientInfo, ProductInfo, UploadRequest,
    DataValidator, ProgressTracker, InterfaceFactory
)

# 初始化日志记录器
logger = get_logger("main")


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    :return: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='商品生成与上传系统')
    
    # 输入选项
    parser.add_argument('--input', '-i', type=str, help='输入数据文件路径（JSON格式）')
    parser.add_argument('--input-format', '-f', type=str, default='json', choices=['json', 'text'], 
                       help='输入数据格式（默认: json）')
    
    # 输出选项
    parser.add_argument('--output-dir', '-o', type=str, default='output', 
                       help='输出目录（默认: output）')
    parser.add_argument('--save-products', action='store_true', default=True, 
                       help='保存生成的商品数据到文件（默认: True）')
    parser.add_argument('--save-results', action='store_true', default=True, 
                       help='保存上传结果到文件（默认: True）')
    
    # 处理选项
    parser.add_argument('--generate-only', action='store_true', help='仅生成商品，不上传')
    parser.add_argument('--upload-only', action='store_true', help='仅上传商品，不生成（需要指定--input）')
    parser.add_argument('--num-products', '-n', type=int, default=1, help='生成商品数量（默认: 1）')
    
    # 配置选项
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--use-sandbox', action='store_true', help='使用沙箱模式（不执行实际上传）')
    
    # 日志选项
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='日志级别（默认: INFO）')
    
    args = parser.parse_args()
    
    # 应用日志级别
    from utils.logger import set_log_level
    set_log_level(args.log_level)
    
    return args


def ensure_directories(output_dir: str) -> None:
    """
    确保必要的目录存在
    
    :param output_dir: 输出目录
    """
    directories = [output_dir, os.path.join(output_dir, 'products'), os.path.join(output_dir, 'results')]
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logger.info(f"创建目录: {directory}")
            except OSError as e:
                logger.error(f"创建目录失败 {directory}: {str(e)}")
                raise


@catch_exceptions(module_name="main", re_raise=True)
def load_client_data(args: argparse.Namespace) -> ClientInfo:
    """
    加载客户数据
    
    :param args: 命令行参数
    :return: 客户数据字典
    :raises ValidationError: 当客户数据无效时
    """
    data_loader = DataLoader()
    
    # 从文件加载数据
    if args.input and os.path.exists(args.input):
        logger.info(f"从文件加载数据: {args.input}")
        if args.input_format == 'json':
            client_data = data_loader.load_json_data(args.input)
        else:
            client_data = data_loader.load_text_data(args.input)
    else:
        # 提示用户输入数据
        logger.info("请输入客户数据（JSON格式）:")
        try:
            input_json = input().strip()
            client_data = json.loads(input_json)
        except json.JSONDecodeError as e:
            logger.error(f"输入数据不是有效的JSON格式: {e}")
            raise ValidationError("输入数据不是有效的JSON格式，请重试。", code="INVALID_JSON")
    
    # 验证客户数据
    validation_result = DataValidator.validate_client_info(client_data)
    if not validation_result['valid']:
        error_messages = [err['message'] for err in validation_result['errors']]
        error_msg = f"客户数据验证失败: {'; '.join(error_messages)}"
        logger.error(error_msg)
        raise ValidationError(error_msg, code="INVALID_CLIENT_DATA", details=validation_result)
    
    # 记录警告信息
    if validation_result['warnings']:
        warning_messages = [f"{warn['field']}: {warn['message']}" for warn in validation_result['warnings']]
        logger.warning(f"客户数据警告: {'; '.join(warning_messages)}")
    
    logger.info("客户数据加载成功")
    return client_data


@catch_exceptions(module_name="main", re_raise=True)
def generate_products(client_data: ClientInfo, args: argparse.Namespace, config_manager: ConfigManager) -> List[ProductInfo]:
    """
    生成商品数据
    
    :param client_data: 客户数据
    :param args: 命令行参数
    :param config_manager: 配置管理器
    :return: 生成的商品列表
    :raises ValidationError: 参数验证失败时抛出
    :raises Exception: 当商品生成失败时
    """
    # 参数验证
    if not isinstance(client_data, dict):
        raise ValidationError("客户数据必须为字典类型", code="INVALID_CLIENT_DATA_TYPE")
    
    if args.num_products <= 0:
        raise ValidationError("生成数量必须为正整数", code="INVALID_PRODUCT_COUNT")
    
    logger.info(f"开始生成商品，数量: {args.num_products}")
    logger.debug(f"客户数据: {client_data.keys()}")
    
    # 创建商品生成器
    generator = ProductGenerator(config_manager=config_manager)
    
    # 创建进度跟踪器
    tracker = ProgressTracker(args.num_products, "商品生成")
    
    try:
        # 生成商品
        products = generator.generate_batch(client_data, args.num_products)
        
        # 更新进度
        tracker.update(args.num_products)
        progress_info = tracker.get_progress()
        logger.info(f"成功生成 {len(products)} 个商品，耗时: {progress_info['elapsed_time']}秒")
        
        # 验证生成的商品数据
        logger.info("开始验证商品数据...")
        validation_result = DataValidator.validate_batch_products(products)
        if not validation_result['valid']:
            error_messages = [err['message'] for err in validation_result['errors']]
            logger.error(f"商品数据验证失败: {'; '.join(error_messages)}")
            # 仍然返回商品，但记录错误
        else:
            logger.info("商品数据验证通过")
        
        # 记录验证警告
        if validation_result['warnings']:
            warning_messages = [f"{warn['field']}: {warn['message']}" for warn in validation_result['warnings']]
            logger.warning(f"商品数据警告: {'; '.join(warning_messages)}")
        
        # 保存商品数据
        if args.save_products:
            products_file = os.path.join(args.output_dir, 'products', 'generated_products.json')
            success = generator.save_products(products, products_file)
            if success:
                logger.info(f"商品数据已保存到: {products_file}")
            else:
                logger.error(f"商品数据保存失败: {products_file}")
        
        return products
    
    except Exception as e:
        logger.error(f"商品生成失败: {str(e)}")
        raise


@catch_exceptions(module_name="main", re_raise=True)
async def generate_products_async(client_data: ClientInfo, args: argparse.Namespace, config_manager: ConfigManager) -> List[ProductInfo]:
    """
    异步生成商品数据
    
    :param client_data: 客户数据
    :param args: 命令行参数
    :param config_manager: 配置管理器
    :return: 生成的商品列表
    :raises Exception: 当商品生成失败时
    """
    logger.info(f"开始异步生成商品，数量: {args.num_products}")
    
    # 创建商品生成器
    generator = ProductGenerator(config_manager=config_manager)
    
    # 创建进度跟踪器
    tracker = ProgressTracker(args.num_products, "异步商品生成")
    
    try:
        # 异步生成商品
        products = await generator.generate_batch_async(client_data, args.num_products)
        
        # 更新进度
        tracker.update(args.num_products)
        progress_info = tracker.get_progress()
        logger.info(f"成功异步生成 {len(products)} 个商品，耗时: {progress_info['elapsed_time']}秒")
        
        # 验证生成的商品数据
        validation_result = DataValidator.validate_batch_products(products)
        if not validation_result['valid']:
            error_messages = [err['message'] for err in validation_result['errors']]
            logger.error(f"商品数据验证失败: {'; '.join(error_messages)}")
        
        # 记录验证警告
        if validation_result['warnings']:
            warning_messages = [f"{warn['field']}: {warn['message']}" for warn in validation_result['warnings']]
            logger.warning(f"商品数据警告: {'; '.join(warning_messages)}")
        
        # 保存商品数据
        if args.save_products:
            products_file = os.path.join(args.output_dir, 'products', 'generated_products.json')
            success = generator.save_products(products, products_file)
            if success:
                logger.info(f"商品数据已保存到: {products_file}")
            else:
                logger.error(f"商品数据保存失败: {products_file}")
        
        return products
    
    except Exception as e:
        logger.error(f"异步商品生成失败: {str(e)}")
        raise


@catch_exceptions(module_name="main", re_raise=True)
def upload_products(products: List[ProductInfo], args: argparse.Namespace, config_manager: ConfigManager) -> Dict[str, Any]:
    """
    上传商品
    
    :param products: 商品列表
    :param args: 命令行参数
    :param config_manager: 配置管理器
    :return: 上传结果
    :raises APIError: 当API调用失败时
    :raises ConnectionError: 当连接失败时
    """
    if args.use_sandbox:
        logger.info("使用沙箱模式，不会执行实际上传操作")
        return {"status": "sandbox", "products_count": len(products), "success": True}
    
    # 验证商品数据
    validation_result = DataValidator.validate_batch_products(products)
    if not validation_result['valid']:
        error_messages = [err['message'] for err in validation_result['errors']]
        error_msg = f"商品数据验证失败，无法上传: {'; '.join(error_messages)}"
        logger.error(error_msg)
        raise ValidationError(error_msg, code="INVALID_PRODUCT_DATA", details=validation_result)
    
    logger.info(f"准备上传 {len(products)} 个商品")
    
    # 创建上传请求
    upload_request: UploadRequest = {
        "products": products,
        "platform": "wechat",
        "sandbox": args.use_sandbox,
        "batch_size": config_manager.get_upload_config().get("batch_size", 10),
        "retry_count": config_manager.get_upload_config().get("retry_count", 3),
        "timeout": config_manager.get_upload_config().get("timeout", 30.0)
    }
    
    # 创建上传器
    uploader = ProductUploader(config_manager=config_manager)
    
    # 创建进度跟踪器
    tracker = ProgressTracker(len(products), "商品上传")
    
    try:
        # 测试连接
        logger.info("测试微信小店API连接...")
        if not uploader.test_connection():
            logger.error("API连接失败，请检查配置后重试。")
            raise ConnectionError("无法连接到微信小店API")
        
        # 执行上传
        logger.info("开始上传商品...")
        results = uploader.upload_products(products)
        
        # 更新进度
        tracker.update(len(products))
        progress_info = tracker.get_progress()
        
        # 生成上传报告
        report = uploader.generate_upload_report(results)
        logger.info(f"上传报告:\n{report}")
        logger.info(f"商品上传完成，耗时: {progress_info['elapsed_time']}秒")
        
        # 保存上传结果
        if args.save_results:
            result_file = os.path.join(args.output_dir, 'results', 'upload_results.json')
            success = uploader.save_upload_results(results, result_file)
            if success:
                logger.info(f"上传结果已保存到: {result_file}")
            else:
                logger.error(f"上传结果保存失败: {result_file}")
        
        return results
    
    except ConnectionError as e:
        logger.error(f"连接失败: {str(e)}")
        raise ConnectionError(f"无法连接到微信小店API: {str(e)}")
    except Exception as e:
        logger.error(f"商品上传失败: {str(e)}")
        raise APIError(str(e), api_name="wechat.upload", code="UPLOAD_FAILED")
    finally:
        uploader.close()


@catch_exceptions(module_name="main", re_raise=False)
async def main_async() -> None:
    """
    异步主函数
    """
    logger.info("商品生成与上传系统启动")
    
    # 解析命令行参数
    args = parse_args()
    logger.debug(f"命令行参数: {vars(args)}")
    
    # 确保输出目录存在
    ensure_directories(args.output_dir)
    
    # 初始化配置管理器
    try:
        config_manager = ConfigManager(config_path=args.config)
        logger.info("配置管理器初始化成功")
    except ConfigError as e:
        logger.error(f"配置初始化失败: {str(e)}")
        logger.info("程序异常退出")
        sys.exit(1)
    except Exception as e:
        logger.error(f"配置管理器初始化失败: {str(e)}")
        logger.info("程序异常退出")
        sys.exit(1)
    
    try:
        products: List[ProductInfo] = []
        
        # 如果仅上传模式，则从输入文件加载商品
        if args.upload_only:
            if not args.input or not os.path.exists(args.input):
                error_msg = "--upload-only模式需要指定--input参数以加载商品数据"
                logger.error(error_msg)
                sys.exit(1)
            
            logger.info(f"从文件加载商品数据: {args.input}")
            data_loader = DataLoader()
            products = data_loader.load_json_data(args.input)
            
            # 验证加载的商品数据
            validation_result = DataValidator.validate_batch_products(products)
            if not validation_result['valid']:
                error_messages = [err['message'] for err in validation_result['errors']]
                error_msg = f"加载的商品数据验证失败: {'; '.join(error_messages)}"
                logger.error(error_msg)
                sys.exit(1)
        else:
            # 加载客户数据
            client_data = load_client_data(args)
            
            # 生成商品（使用异步方法）
            products = await generate_products_async(client_data, args, config_manager)
        
        # 上传商品（如果不是仅生成模式）
        if not args.generate_only and products:
            upload_products(products, args, config_manager)
        
        logger.info("商品生成和上传流程完成！")
        
    except KeyboardInterrupt:
        logger.warning("用户中断操作")
    except ValidationError as e:
        logger.error(f"数据验证失败: {e.message}")
        logger.info("程序异常退出")
        sys.exit(1)
    except APIError as e:
        logger.error(f"API调用失败: {e.message}")
        logger.info("程序异常退出")
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"连接失败: {str(e)}")
        logger.info("程序异常退出")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        logger.info("程序异常退出")
        sys.exit(1)


@catch_exceptions(module_name="main", re_raise=False)
def main() -> None:
    """
    主函数
    """
    logger.info("商品生成与上传系统启动")
    
    # 运行异步主函数
    try:
        # 设置事件循环策略（解决Windows上的问题）
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(main_async())
    except RuntimeError as e:
        # 如果事件循环已经在运行（如在某些IDE中），使用传统方式
        if 'Event loop is closed' in str(e) or 'Event loop is already running' in str(e):
            logger.warning("使用同步模式执行（事件循环已存在）")
            
            # 解析命令行参数
            args = parse_args()
            logger.debug(f"命令行参数: {vars(args)}")
            
            # 确保输出目录存在
            ensure_directories(args.output_dir)
            
            # 初始化配置管理器
            try:
                config_manager = ConfigManager(config_path=args.config)
                logger.info("配置管理器初始化成功")
            except ConfigError as e:
                logger.error(f"配置初始化失败: {str(e)}")
                sys.exit(1)
            
            try:
                products: List[ProductInfo] = []
                
                # 如果仅上传模式，则从输入文件加载商品
                if args.upload_only:
                    if not args.input or not os.path.exists(args.input):
                        error_msg = "--upload-only模式需要指定--input参数以加载商品数据"
                        logger.error(error_msg)
                        sys.exit(1)
                    
                    logger.info(f"从文件加载商品数据: {args.input}")
                    data_loader = DataLoader()
                    products = data_loader.load_json_data(args.input)
                    
                    # 验证加载的商品数据
                    validation_result = DataValidator.validate_batch_products(products)
                    if not validation_result['valid']:
                        error_messages = [err['message'] for err in validation_result['errors']]
                        error_msg = f"加载的商品数据验证失败: {'; '.join(error_messages)}"
                        logger.error(error_msg)
                        sys.exit(1)
                else:
                    # 加载客户数据
                    client_data = load_client_data(args)
                    
                    # 生成商品（使用同步方法）
                    products = generate_products(client_data, args, config_manager)
                
                # 上传商品（如果不是仅生成模式）
                if not args.generate_only and products:
                    upload_products(products, args, config_manager)
                
                logger.info("商品生成和上传流程完成！")
                
            except KeyboardInterrupt:
                logger.warning("用户中断操作")
            except ValidationError as e:
                logger.error(f"数据验证失败: {e.message}")
                sys.exit(1)
            except APIError as e:
                logger.error(f"API调用失败: {e.message}")
                sys.exit(1)
            except ConnectionError as e:
                logger.error(f"连接失败: {str(e)}")
                sys.exit(1)
            except Exception as e:
                logger.error(f"程序执行出错: {str(e)}")
                sys.exit(1)
    
    logger.info("程序正常退出")


if __name__ == "__main__":
    main()
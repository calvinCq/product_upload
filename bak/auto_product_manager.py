#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信小店商品自动管理主程序
功能：
- 自动生成符合微信小店API要求的商品数据
- 自动上传商品到微信小店
- 支持用户积分查询
- 生成操作报告
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime

# 导入各个模块
from config_manager import ConfigManager
from product_generator import ProductGenerator
from product_uploader import ProductUploader
from vip_score_manager import VipScoreManager

# 导入日志功能
from wechat_shop_api import log_message


def parse_arguments():
    """
    解析命令行参数
    
    :return: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='微信小店商品自动管理工具')
    
    # 子命令分组
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 生成商品命令
    generate_parser = subparsers.add_parser('generate', help='生成商品数据')
    generate_parser.add_argument(
        '--count', '-c', 
        type=int, 
        default=None, 
        help='生成商品数量（默认使用配置文件中的设置）'
    )
    generate_parser.add_argument(
        '--output', '-o', 
        type=str, 
        default='generated_products.json', 
        help='生成的商品数据保存路径'
    )
    
    # 上传商品命令
    upload_parser = subparsers.add_parser('upload', help='上传商品到微信小店')
    upload_parser.add_argument(
        '--file', '-f', 
        type=str, 
        required=True, 
        help='包含商品数据的JSON文件路径'
    )
    upload_parser.add_argument(
        '--async', '-a', 
        action='store_true', 
        dest='use_async',
        help='使用异步上传（提高效率）'
    )
    upload_parser.add_argument(
        '--report', '-r', 
        type=str, 
        default='upload_report.txt', 
        help='上传报告保存路径'
    )
    upload_parser.add_argument(
        '--results', '-s', 
        type=str, 
        default='upload_results.json', 
        help='上传结果详情保存路径'
    )
    
    # 查询积分命令
    score_parser = subparsers.add_parser('score', help='查询用户积分')
    score_parser.add_argument(
        '--openid', '-o', 
        type=str, 
        help='单个用户的openid'
    )
    score_parser.add_argument(
        '--file', '-f', 
        type=str, 
        help='包含多个openid的文件路径（每行一个）'
    )
    score_parser.add_argument(
        '--report', '-r', 
        type=str, 
        default='score_report.txt', 
        help='积分查询报告保存路径'
    )
    score_parser.add_argument(
        '--results', '-s', 
        type=str, 
        default='score_results.json', 
        help='积分查询结果详情保存路径'
    )
    
    # 一键执行命令（生成+上传）
    auto_parser = subparsers.add_parser('auto', help='自动生成并上传商品')
    auto_parser.add_argument(
        '--count', '-c', 
        type=int, 
        default=None, 
        help='生成商品数量（默认使用配置文件中的设置）'
    )
    auto_parser.add_argument(
        '--async', '-a', 
        action='store_true', 
        dest='use_async',
        help='使用异步上传（提高效率）'
    )
    auto_parser.add_argument(
        '--temp-file', 
        type=str, 
        default='temp_generated_products.json', 
        help='临时保存生成商品的文件路径'
    )
    auto_parser.add_argument(
        '--report', '-r', 
        type=str, 
        default='auto_report.txt', 
        help='自动执行报告保存路径'
    )
    
    # 查看配置命令
    subparsers.add_parser('config', help='查看当前配置信息')
    
    # 验证配置命令
    subparsers.add_parser('validate', help='验证配置文件的有效性')
    
    # 通用参数
    parser.add_argument(
        '--config', '-C', 
        type=str, 
        default='product_generator_config.json', 
        help='配置文件路径'
    )
    parser.add_argument(
        '--log-level', 
        type=str, 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
        default='INFO', 
        help='日志级别'
    )
    
    # 如果没有指定命令，显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    return parser.parse_args()


def load_products_from_file(file_path):
    """
    从文件加载商品数据
    
    :param file_path: 文件路径
    :return: 商品列表
    """
    try:
        if not os.path.exists(file_path):
            log_message(f"商品文件不存在: {file_path}", "ERROR")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        if not isinstance(products, list):
            log_message(f"商品文件格式错误，应为JSON数组", "ERROR")
            return None
        
        log_message(f"成功从文件加载{len(products)}个商品")
        return products
        
    except Exception as e:
        log_message(f"加载商品文件失败: {str(e)}", "ERROR")
        return None


def load_openids_from_file(file_path):
    """
    从文件加载openid列表
    
    :param file_path: 文件路径
    :return: openid列表
    """
    try:
        if not os.path.exists(file_path):
            log_message(f"openid文件不存在: {file_path}", "ERROR")
            return None
        
        openids = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                openid = line.strip()
                if openid:
                    openids.append(openid)
        
        log_message(f"成功从文件加载{len(openids)}个openid")
        return openids
        
    except Exception as e:
        log_message(f"加载openid文件失败: {str(e)}", "ERROR")
        return None


def ensure_directory(file_path):
    """
    确保文件所在目录存在
    
    :param file_path: 文件路径
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        log_message(f"创建目录: {directory}")


def generate_products(config, args):
    """
    生成商品数据
    
    :param config: 配置管理器实例
    :param args: 命令行参数
    :return: 是否成功
    """
    try:
        log_message("开始生成商品数据")
        
        # 确保输出目录存在
        ensure_directory(args.output)
        
        # 初始化商品生成器
        generator = ProductGenerator(config.get_generation_config())
        
        # 生成商品
        products = generator.generate_products(args.count)
        
        if not products:
            log_message("未能生成任何商品", "ERROR")
            return False
        
        # 保存到文件
        if generator.save_products_to_file(products, args.output):
            log_message(f"商品生成完成，共{len(products)}个，已保存到: {args.output}")
            return True
        else:
            log_message("保存商品数据失败", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"生成商品时发生错误: {str(e)}", "ERROR")
        return False


def upload_products(config, args):
    """
    上传商品到微信小店
    
    :param config: 配置管理器实例
    :param args: 命令行参数
    :return: 是否成功
    """
    try:
        # 加载商品数据
        products = load_products_from_file(args.file)
        if not products:
            return False
        
        # 确保输出目录存在
        ensure_directory(args.report)
        ensure_directory(args.results)
        
        # 初始化商品上传器
        uploader = ProductUploader(config.config)
        
        # 执行上传
        if args.use_async:
            # 异步上传
            log_message("使用异步模式上传商品")
            results = asyncio.run(uploader.upload_products_async(products))
        else:
            # 同步上传
            log_message("使用同步模式上传商品")
            results = uploader.upload_products(products)
        
        # 保存结果和报告
        uploader.save_upload_results(results, args.results)
        report = uploader.generate_upload_report(results, args.report)
        
        # 输出摘要信息
        log_message(f"商品上传完成")
        log_message(f"总商品数: {results.get('total', 0)}")
        log_message(f"成功数量: {results.get('success', 0)}")
        log_message(f"失败数量: {results.get('failed', 0)}")
        log_message(f"成功率: {results.get('success_rate', 0)}%")
        log_message(f"报告已保存到: {args.report}")
        log_message(f"详细结果已保存到: {args.results}")
        
        return results.get('success', 0) > 0
        
    except Exception as e:
        log_message(f"上传商品时发生错误: {str(e)}", "ERROR")
        return False


def query_scores(config, args):
    """
    查询用户积分
    
    :param config: 配置管理器实例
    :param args: 命令行参数
    :return: 是否成功
    """
    try:
        # 创建包含所有必要配置的字典
        full_config = {
            'api': config.get_api_config(),
            'points': config.get_points_config()
        }
        
        # 初始化积分管理器
        score_manager = VipScoreManager(full_config)
        
        # 确保输出目录存在
        ensure_directory(args.report)
        ensure_directory(args.results)
        
        if args.openid:
            # 查询单个用户
            log_message(f"查询单个用户积分: {args.openid}")
            success, score_info = score_manager.get_vip_user_score(args.openid)
            
            if success:
                log_message(f"用户 {args.openid} 的积分: {score_info['score']} 分")
                # 构建结果
                results = {
                    'total': 1,
                    'success': 1,
                    'failed': 0,
                    'details': [score_info]
                }
                score_manager.save_score_results(results, args.results)
                score_manager.generate_score_report(results, args.report)
                return True
            else:
                log_message(f"查询失败: {score_info}", "ERROR")
                return False
        
        elif args.file:
            # 批量查询
            openids = load_openids_from_file(args.file)
            if not openids:
                return False
            
            results = score_manager.batch_get_vip_user_scores(openids)
            score_manager.save_score_results(results, args.results)
            report = score_manager.generate_score_report(results, args.report)
            
            # 输出摘要信息
            log_message(f"积分查询完成")
            log_message(f"总用户数: {results.get('total', 0)}")
            log_message(f"成功查询: {results.get('success', 0)}")
            log_message(f"失败查询: {results.get('failed', 0)}")
            log_message(f"总积分: {results.get('total_score', 0)}")
            log_message(f"平均积分: {results.get('average_score', 0)}")
            log_message(f"报告已保存到: {args.report}")
            log_message(f"详细结果已保存到: {args.results}")
            
            return results.get('success', 0) > 0
        
        else:
            log_message("请提供--openid或--file参数", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"查询积分时发生错误: {str(e)}", "ERROR")
        return False


def auto_generate_and_upload(config, args):
    """
    自动生成并上传商品
    
    :param config: 配置管理器实例
    :param args: 命令行参数
    :return: 是否成功
    """
    try:
        log_message("开始自动生成并上传商品流程")
        
        # 确保输出目录存在
        ensure_directory(args.temp_file)
        ensure_directory(args.report)
        
        # 创建包含所有必要配置的字典
        full_config = {
            'generation': config.get_generation_config(),
            'upload': config.get_upload_config(),
            'api': config.get_api_config()
        }
        
        # 步骤1: 生成商品
        log_message("【步骤1/2】生成商品数据")
        generator = ProductGenerator(full_config)
        products = generator.generate_products(args.count)
        
        if not products:
            log_message("未能生成任何商品，流程终止", "ERROR")
            return False
        
        # 保存临时文件
        generator.save_products_to_file(products, args.temp_file)
        log_message(f"已生成{len(products)}个商品，临时保存到: {args.temp_file}")
        
        # 步骤2: 上传商品
        log_message("【步骤2/2】上传商品到微信小店")
        uploader = ProductUploader(full_config)
        
        if args.use_async:
            results = asyncio.run(uploader.upload_products_async(products))
        else:
            results = uploader.upload_products(products)
        
        # 生成综合报告
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("微信小店商品自动管理 - 综合执行报告")
        report_lines.append("=" * 80)
        report_lines.append(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"生成商品数量: {len(products)}")
        report_lines.append(f"上传成功数量: {results.get('success', 0)}")
        report_lines.append(f"上传失败数量: {results.get('failed', 0)}")
        report_lines.append(f"上传成功率: {results.get('success_rate', 0)}%")
        report_lines.append(f"总耗时: {results.get('duration', 0)}秒")
        report_lines.append("\n详细上传报告:")
        report_lines.append("=" * 80)
        
        # 添加上传报告详情
        upload_report = uploader.generate_upload_report(results)
        report_lines.append(upload_report)
        
        # 保存综合报告
        report_content = "\n".join(report_lines)
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        log_message(f"综合报告已保存到: {args.report}")
        log_message("自动执行流程完成")
        
        return results.get('success', 0) > 0
        
    except Exception as e:
        log_message(f"自动执行过程中发生错误: {str(e)}", "ERROR")
        return False
    finally:
        # 可选：清理临时文件
        if hasattr(args, 'temp_file') and os.path.exists(args.temp_file):
            try:
                os.remove(args.temp_file)
                log_message(f"已清理临时文件: {args.temp_file}")
            except:
                pass


def show_config(config):
    """
    显示当前配置信息
    
    :param config: 配置管理器实例
    """
    print("\n当前配置信息:")
    print("=" * 60)
    
    # 格式化输出配置信息
    for section, values in config.config.items():
        print(f"\n[{section.upper()}]")
        if isinstance(values, dict):
            for key, value in values.items():
                # 隐藏敏感信息
                if key in ['secret', 'password']:
                    print(f"  {key}: {'*' * 8}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {values}")
    
    print("\n" + "=" * 60)
    log_message("配置信息已显示")


def validate_config(config):
    """
    验证配置文件的有效性
    
    :param config: 配置管理器实例
    :return: 是否有效
    """
    try:
        log_message("开始验证配置文件")
        
        # 调用配置管理器的验证方法
        is_valid = config.validate_config()
        
        if is_valid:
            log_message("配置文件验证通过")
            print("配置文件验证通过！")
            return True
        else:
            log_message("配置文件验证失败", "ERROR")
            print("配置文件验证失败！请检查日志获取详细信息。")
            return False
            
    except Exception as e:
        log_message(f"验证配置时发生错误: {str(e)}", "ERROR")
        print(f"验证失败: {str(e)}")
        return False


def main():
    """
    主函数
    """
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 记录启动日志
        log_message(f"启动微信小店商品自动管理工具 - 命令: {args.command}")
        
        # 加载配置
        config_manager = ConfigManager(args.config)
        log_message(f"已加载配置文件: {args.config}")
        
        # 根据命令执行相应功能
        success = False
        
        if args.command == 'generate':
            success = generate_products(config_manager, args)
            
        elif args.command == 'upload':
            success = upload_products(config_manager, args)
            
        elif args.command == 'score':
            success = query_scores(config_manager, args)
            
        elif args.command == 'auto':
            success = auto_generate_and_upload(config_manager, args)
            
        elif args.command == 'config':
            show_config(config_manager)
            success = True
            
        elif args.command == 'validate':
            success = validate_config(config_manager)
        
        # 退出程序
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        log_message("程序被用户中断", "WARNING")
        print("\n程序已中断。")
        sys.exit(1)
    
    except Exception as e:
        log_message(f"程序发生未捕获的错误: {str(e)}", "ERROR")
        print(f"错误: {str(e)}")
        print("请查看日志获取详细信息。")
        sys.exit(1)


if __name__ == "__main__":
    main()
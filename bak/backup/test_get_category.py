#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信小店商品类目获取测试工具
支持传统微信小店和视频号小店类目API
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from wechat_shop_api import WeChatShopAPIClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 确保输出目录存在
os.makedirs('test_results', exist_ok=True)


def load_config():
    """
    加载配置文件
    """
    try:
        with open('wechat_api_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return None


def direct_get_access_token(appid, appsecret, api_base_url):
    """
    直接获取access_token进行调试
    """
    try:
        url = f"{api_base_url}/cgi-bin/token"
        params = {
            'grant_type': 'client_credential',
            'appid': appid,
            'secret': appsecret
        }
        logger.info(f"正在直接请求access_token: {url}")
        response = requests.get(url, params=params, timeout=30)
        response_data = response.json()
        
        logger.debug(f"  access_token请求状态码: {response.status_code}")
        logger.debug(f"  access_token响应内容: {response_data}")
        
        if 'access_token' in response_data:
            return response_data['access_token']
        return None
    except Exception as e:
        logger.error(f"直接获取access_token失败: {str(e)}")
        return None


def direct_get_category(access_token, api_base_url, api_path):
    """
    直接使用access_token调用类目API
    """
    try:
        url = f"{api_base_url}{api_path}"
        params = {'access_token': access_token}
        logger.info(f"直接调用类目API: {url}")
        response = requests.get(url, params=params, timeout=30)
        response_data = response.json()
        
        logger.debug(f"  类目API请求状态码: {response.status_code}")
        logger.debug(f"  类目API响应内容: {response_data}")
        
        return response_data
    except Exception as e:
        logger.error(f"直接调用类目API失败: {str(e)}")
        return None


def provide_error_solution(errcode=None):
    """
    根据错误码提供解决方案
    """
    solutions = {
        40001: "无效的凭证，请检查appid和appsecret是否正确",
        40013: "无效的appid，请确认appid是否正确或已在微信公众号平台注册",
        40125: "无效的appsecret，请确认appsecret是否正确",
        40066: "无效的URL，请检查API路径是否正确",
        41001: "缺少access_token，请确保已正确获取access_token"
    }
    
    if errcode and errcode in solutions:
        return solutions[errcode]
    return "请参考微信官方文档排查问题"


def display_category_info(category_data):
    """
    显示类目信息
    """
    if not category_data:
        return
    
    # 适配不同的数据格式
    if isinstance(category_data, dict):
        # 检查是否有嵌套的data字段
        if 'data' in category_data and isinstance(category_data['data'], dict):
            category_data = category_data['data']
        
        # 检查cats或categories字段
        if 'cats' in category_data:
            categories = category_data['cats']
        elif 'categories' in category_data:
            categories = category_data['categories']
        elif isinstance(category_data.get('category'), list):
            categories = category_data['category']
        else:
            categories = [category_data]  # 假设整个响应就是一个类目
        
        logger.info(f"\n🎯 成功获取到 {len(categories)} 个类目")
        
        # 显示前10个类目作为示例
        for i, cat in enumerate(categories[:10]):
            if isinstance(cat, dict):
                cat_id = cat.get('cat_id', cat.get('id', 'N/A'))
                cat_name = cat.get('cat_name', cat.get('name', 'N/A'))
                parent_id = cat.get('parent_id', cat.get('pid', 'N/A'))
                level = cat.get('level', 'N/A')
                logger.info(f"  类目{i+1}: ID={cat_id}, 名称={cat_name}, 父ID={parent_id}, 级别={level}")
            else:
                logger.info(f"  类目{i+1}: {cat}")
        
        if len(categories) > 10:
            logger.info(f"  ... 等共 {len(categories)} 个类目")
    else:
        logger.info(f"\n🎯 获取到类目数据: {category_data}")


def save_category_result(category_data, api_type):
    """
    保存类目获取结果
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"test_results/wechat_shop_{api_type}_category_result_{timestamp}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 类目结果已保存到: {filename}")
        return filename
    except Exception as e:
        logger.error(f"保存类目结果失败: {str(e)}")
        return None


def generate_category_index(category_data, filename):
    """
    生成类目索引便于查看
    """
    if not category_data or not filename:
        return
    
    index_filename = filename.replace('.json', '_index.txt')
    try:
        with open(index_filename, 'w', encoding='utf-8') as f:
            f.write("微信小店商品类目索引\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            # 适配不同的数据格式
            categories = []
            if isinstance(category_data, dict):
                if 'data' in category_data and isinstance(category_data['data'], dict):
                    category_data = category_data['data']
                if 'cats' in category_data:
                    categories = category_data['cats']
                elif 'categories' in category_data:
                    categories = category_data['categories']
                elif isinstance(category_data.get('category'), list):
                    categories = category_data['category']
            
            # 按级别组织类目
            level_map = {}
            for cat in categories:
                if isinstance(cat, dict):
                    level = str(cat.get('level', 'N/A'))
                    if level not in level_map:
                        level_map[level] = []
                    level_map[level].append(cat)
            
            # 写入各级类目
            for level in sorted(level_map.keys()):
                f.write(f"\n=== 级别 {level} 类目 ===\n")
                for cat in level_map[level]:
                    cat_id = cat.get('cat_id', cat.get('id', 'N/A'))
                    cat_name = cat.get('cat_name', cat.get('name', 'N/A'))
                    f.write(f"{cat_id}: {cat_name}\n")
        
        logger.info(f"✅ 类目索引已生成: {index_filename}")
    except Exception as e:
        logger.error(f"生成类目索引失败: {str(e)}")


def test_get_category():
    """
    测试获取微信小店商品类目
    """
    logger.info("=" * 44)
    logger.info("微信小店商品类目获取测试工具")
    logger.info("=" * 44)
    logger.info("支持传统微信小店和视频号小店类目API")
    logger.info("=" * 44)
    
    # 加载配置
    config = load_config()
    if not config:
        logger.error("配置加载失败，无法继续测试")
        return False
    
    logger.info("配置加载成功，开始测试类目获取API...")
    logger.info("\n========== 开始测试微信小店商品类目获取API ==========")
    
    appid = config.get('appid')
    appsecret = config.get('appsecret')
    api_base_url = config.get('api_base_url', 'https://api.weixin.qq.com')
    api_paths = config.get('api_paths', {})
    
    # 1. 直接获取access_token进行调试
    logger.info("\n🔍 尝试直接获取access_token...")
    access_token = direct_get_access_token(appid, appsecret, api_base_url)
    
    if not access_token:
        logger.error("❌ 无法获取access_token，请检查appid和appsecret配置")
        return False
    
    logger.info(f"✅ 成功获取access_token: {access_token[:20]}...")
    
    # 2. 尝试多种类目API接口
    api_success = False
    category_data = None
    
    # 2.1 尝试视频号小店类目API (channels/ec/category/all)
    if 'get_all_category' in api_paths:
        logger.info("\n🔍 尝试使用视频号小店类目API (get_all_category)...")
        category_data = direct_get_category(access_token, api_base_url, api_paths['get_all_category'])
        
        if category_data and (category_data.get('errcode') == 0 or 'cats' in category_data or 'categories' in category_data):
            logger.info("✅ 视频号小店类目API调用成功！")
            api_success = True
            display_category_info(category_data)
            filename = save_category_result(category_data, 'channels')
            generate_category_index(category_data, filename)
        else:
            logger.warning(f"❌ 视频号小店类目API调用失败: {category_data}")
    
    # 2.2 尝试传统微信小店类目API
    if not api_success and 'get_category' in api_paths:
        logger.info("\n🔄 尝试使用传统微信小店类目API...")
        category_data = direct_get_category(access_token, api_base_url, api_paths['get_category'])
        
        if category_data and (category_data.get('errcode') == 0 or 'cats' in category_data or 'categories' in category_data):
            logger.info("✅ 传统微信小店类目API调用成功！")
            api_success = True
            display_category_info(category_data)
            filename = save_category_result(category_data, 'traditional')
            generate_category_index(category_data, filename)
        else:
            logger.warning(f"❌ 传统微信小店类目API调用失败: {category_data}")
    
    # 3. 打印详细调试信息
    logger.info("\n🔍 详细调试信息:")
    logger.info(f"  AppID: {appid}")
    logger.info(f"  API基础URL: {api_base_url}")
    if 'get_all_category' in api_paths:
        logger.info(f"  视频号API路径: {api_paths['get_all_category']}")
    if 'get_category' in api_paths:
        logger.info(f"  传统API路径: {api_paths['get_category']}")
    
    # 4. 结果判断
    if api_success:
        logger.info("\n🎉 类目获取测试成功完成！")
        logger.info("\n💡 使用建议:")
        logger.info("1. 在商品上传时，请使用获取到的类目ID")
        logger.info("2. 优先使用三级类目ID以获得最佳匹配")
        logger.info("3. 定期更新类目数据以确保准确性")
        return True
    else:
        logger.error("\n❌ 类目获取测试未成功")
        logger.info("=" * 44)
        logger.info("可能的原因：")
        logger.info("1. 当前账号未开通微信小店或视频号小店功能")
        logger.info("2. 账号权限不足，无法访问类目API")
        logger.info("3. AppID或AppSecret配置有误")
        logger.info("4. 网络连接问题或API服务器暂时不可用")
        logger.info("5. API路径可能已更新，请参考最新微信官方文档")
        logger.info("")
        logger.info("💡 排查建议:")
        logger.info("1. 检查wechat_api_config.json中的appid和appsecret是否正确")
        logger.info("2. 确认当前公众号是否已开通微信小店或视频号小店功能")
        logger.info("3. 检查API路径配置是否符合微信最新文档要求")
        logger.info("4. 查看wechat_api_operation.log获取详细错误信息")
        
        # 分析错误码
        if category_data and isinstance(category_data, dict) and 'errcode' in category_data:
            errcode = category_data['errcode']
            logger.info(f"\n📋 错误码分析: {errcode} - {provide_error_solution(errcode)}")
        
        return False


def main():
    """
    主函数
    """
    try:
        success = test_get_category()
        logger.info("\n✅ 程序执行完毕")
        return 0 if success else 1
    except Exception as e:
        logger.error(f"程序运行异常: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
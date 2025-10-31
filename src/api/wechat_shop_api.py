#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信小店API操作类
提供与微信小店API交互的基本功能
"""

import os
import json
import time
import csv
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv  # 用于加载.env文件中的环境变量
from src.utils.logger import log_message
from src.utils.config_manager import get_config_value

# 加载.env文件中的环境变量
load_dotenv()

def load_api_paths():
    """
    从配置文件加载API路径配置
    """
    # 尝试从配置管理器获取API路径配置
    try:
        api_paths = get_config_value('wechat_shop.api_paths', {})
        if api_paths:
            return api_paths
    except Exception as e:
        log_message(f"从配置管理器加载API路径配置失败: {e}", "WARNING")
    
    # 回退到从配置文件加载
    config_path = os.path.join(os.path.dirname(__file__), 'wechat_api_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('api_paths', {})
    except Exception as e:
        log_message(f"警告：加载API路径配置失败: {e}", "WARNING")
        # 返回默认路径作为备份
        return {
            'access_token': '/cgi-bin/token',
            'get_vip_user_score': '/shop/vip/getvipuserscore',
            'get_category': '/merchant/category/getall',
            'get_all_category': '/channels/ec/category/all',
            'get_channels_category': '/channels/ec/category/batchget',  # 修正为正确的路径
            'get_channels_product_list': '/channels/ec/product/list/get',
            'get_product_detail': '/channels/ec/product/get'
        }

# API路径定义（从配置文件加载）
API_PATHS = load_api_paths()

def load_wechat_api_config():
    """
    从配置文件加载微信API配置
    """
    # 默认配置
    default_config = {
        "api_base_url": "https://api.weixin.qq.com",
        "access_token": "",
        "appid": "",
        "appsecret": "",
        "timeout": 30
    }
    
    # 尝试从配置管理器获取配置
    try:
        config_manager_values = {
            "api_base_url": get_config_value('wechat_shop.api_base_url'),
            "appid": get_config_value('wechat_shop.appid'),
            "appsecret": get_config_value('wechat_shop.appsecret'),
            "timeout": get_config_value('wechat_shop.timeout')
        }
        
        # 过滤None值并更新默认配置
        filtered_config = {k: v for k, v in config_manager_values.items() if v is not None}
        default_config.update(filtered_config)
    except Exception as e:
        log_message(f"从配置管理器加载微信API配置失败: {e}", "WARNING")
    
    # 回退到从配置文件加载
    config_path = os.path.join(os.path.dirname(__file__), 'wechat_api_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 过滤掉api_paths，因为已经单独加载
            filtered_config = {k: v for k, v in config.items() if k != 'api_paths'}
            # 更新默认配置
            default_config.update(filtered_config)
    except Exception as e:
        log_message(f"警告：加载微信API配置失败: {e}", "WARNING")
    
    # 确保必要的默认值存在
    default_config.setdefault('access_token', '')
    default_config.setdefault('timeout', 30)
    return default_config

# 微信小店API配置（从配置文件加载）
WECHAT_API_CONFIG = load_wechat_api_config()

# 日志文件
LOG_FILE = "wechat_api_operation.log"

# 商品相关API路径定义，会在类中使用

# 微信小店商品必填字段
WECHAT_SHOP_REQUIRED_FIELDS = [
    "product_id",  # 商品ID
    "product_name",  # 商品名称
    "category_id",  # 商品分类ID
    "main_image",  # 商品主图
    "image_list",  # 商品图片列表
    "price",  # 商品价格
    "original_price",  # 商品原价
    "product_desc",  # 商品描述
    "sku_list",  # SKU列表
    "attributes",  # 商品属性
    "product_status",  # 商品状态
]


def log_message(message, level="INFO"):
    """
    记录日志消息
    :param message: 日志消息
    :param level: 日志级别，默认INFO
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    # 确保日志目录存在
    log_dir = os.path.dirname(LOG_FILE) if os.path.dirname(LOG_FILE) else '.'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 写入日志文件
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    # 同时输出到控制台
    print(log_entry.strip())


def convert_product_to_csv_format(product):
    """
    将商品数据转换为CSV格式的字典
    :param product: 商品数据字典
    :return: CSV格式的商品数据字典
    """
    csv_data = {
        '商品标题': product.get('title', ''),
        '副标题': product.get('sub_title', ''),
        '短标题': product.get('short_title', ''),
        '商品描述': product.get('desc_info', {}).get('desc', ''),
        '发货方式': product.get('deliver_method', 0),
        '一级类目ID': '',
        '二级类目ID': '',
        '三级类目ID': '',
        '主图1': '',
        '主图2': '',
        '主图3': '',
        '主图4': '',
        '主图5': '',
        '主图6': '',
        '主图7': '',
        '主图8': '',
        '主图9': '',
        '详情图1': '',
        '详情图2': '',
        '详情图3': '',
        'SKU价格(分)': '',
        'SKU库存': '',
        'SKU编码': '',
        '上架状态': product.get('listing', 0)
    }
    
    # 处理类目ID
    cats = product.get('cats', [])
    if len(cats) > 0:
        csv_data['一级类目ID'] = cats[0].get('cat_id', '')
    if len(cats) > 1:
        csv_data['二级类目ID'] = cats[1].get('cat_id', '')
    if len(cats) > 2:
        csv_data['三级类目ID'] = cats[2].get('cat_id', '')
    
    # 处理主图
    head_imgs = product.get('head_imgs', [])
    for i, img in enumerate(head_imgs[:9]):
        csv_data[f'主图{i+1}'] = img
    
    # 处理详情图
    detail_imgs = product.get('desc_info', {}).get('imgs', [])
    for i, img in enumerate(detail_imgs[:3]):
        csv_data[f'详情图{i+1}'] = img
    
    # 处理SKU信息
    skus = product.get('skus', [])
    if skus:
        csv_data['SKU价格(分)'] = skus[0].get('price', '')
        csv_data['SKU库存'] = skus[0].get('stock_num', '')
        csv_data['SKU编码'] = skus[0].get('out_sku_id', '')
    
    return csv_data

def save_products_to_csv(products, csv_file):
    """
    将商品数据保存到CSV文件
    :param products: 商品数据列表
    :param csv_file: CSV文件路径
    """
    if not products:
        log_message("没有商品数据可保存", "WARNING")
        return False
    
    # 确保目录存在
    output_dir = os.path.dirname(csv_file) if os.path.dirname(csv_file) else '.'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 定义CSV字段名（按照模板要求排序）
    fieldnames = [
        '商品标题', '副标题', '短标题', '商品描述', '发货方式',
        '一级类目ID', '二级类目ID', '三级类目ID',
        '主图1', '主图2', '主图3', '主图4', '主图5', '主图6', '主图7', '主图8', '主图9',
        '详情图1', '详情图2', '详情图3',
        'SKU价格(分)', 'SKU库存', 'SKU编码', '上架状态'
    ]
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # 转换每个商品并写入CSV
            for product in products:
                csv_data = convert_product_to_csv_format(product)
                writer.writerow(csv_data)
        
        log_message(f"成功将{len(products)}条商品数据保存到{csv_file}")
        return True
    except Exception as e:
        log_message(f"保存商品数据到CSV失败: {str(e)}", "ERROR")
        return False


def convert_csv_to_product_format(csv_row):
    """
    将CSV行数据转换为商品数据格式
    :param csv_row: CSV行数据字典
    :return: 商品数据字典
    """
    product = {
        'title': csv_row.get('商品标题', ''),
        'sub_title': csv_row.get('副标题', ''),
        'short_title': csv_row.get('短标题', ''),
        'desc_info': {
            'desc': csv_row.get('商品描述', ''),
            'imgs': []
        },
        'deliver_method': int(csv_row.get('发货方式', '0')),
        'cats': [],
        'cats_v2': [],
        'head_imgs': [],
        'extra_service': {
            'service_tags': []
        },
        'skus': [],
        'listing': int(csv_row.get('上架状态', '0'))
    }
    
    # 处理类目
    cats = []
    for level in ['一级类目ID', '二级类目ID', '三级类目ID']:
        cat_id = csv_row.get(level, '').strip()
        if cat_id:
            cats.append({'cat_id': cat_id})
    
    if cats:
        product['cats'] = cats
        product['cats_v2'] = cats.copy()
    
    # 处理主图
    for i in range(1, 10):
        img = csv_row.get(f'主图{i}', '').strip()
        if img:
            product['head_imgs'].append(img)
    
    # 处理详情图
    for i in range(1, 4):
        img = csv_row.get(f'详情图{i}', '').strip()
        if img:
            product['desc_info']['imgs'].append(img)
    
    # 处理SKU
    price = csv_row.get('SKU价格(分)', '').strip()
    stock_num = csv_row.get('SKU库存', '').strip()
    out_sku_id = csv_row.get('SKU编码', '').strip()
    
    if price or stock_num:
        sku = {
            'price': int(price) if price else 0,
            'stock_num': int(stock_num) if stock_num else 0
        }
        if out_sku_id:
            sku['out_sku_id'] = out_sku_id
        product['skus'] = [sku]
    
    return product

def load_products_from_csv(csv_file):
    """
    从CSV文件加载商品数据
    :param csv_file: CSV文件路径
    :return: 商品数据列表
    """
    if not os.path.exists(csv_file):
        log_message(f"CSV文件不存在: {csv_file}", "ERROR")
        return []
    
    products = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # 转换为商品格式
                product = convert_csv_to_product_format(row)
                products.append(product)
        
        log_message(f"成功从{csv_file}加载{len(products)}条商品数据")
        return products
    except Exception as e:
        log_message(f"从CSV加载商品数据失败: {str(e)}", "ERROR")
        return []


class WeChatShopAPIClient:
    """
    微信小店API客户端类
    提供通过微信小店API操作商品和店铺信息的功能
    """
    
    def __init__(self, appid=None, appsecret=None, api_config=None):
        """
        初始化微信小店API客户端
        :param appid: 公众号AppID
        :param appsecret: 公众号AppSecret
        :param api_config: 自定义API配置字典
        """
        self.api_config = WECHAT_API_CONFIG.copy()
        if api_config:
            self.api_config.update(api_config)
        
        if appid:
            self.api_config["appid"] = appid
        if appsecret:
            self.api_config["appsecret"] = appsecret
        
        self.access_token = self.api_config.get("access_token", "")
        self.token_expire_time = 0  # token过期时间戳
        self.session = requests.Session()
        self.api_paths = API_PATHS.copy()
        self.operation_history = []
        self.session.timeout = self.api_config.get("timeout", 30)
        
        # 使用全局加载的API路径配置
        # 可以在这里添加实例特定的覆盖或补充
        self.api_paths = API_PATHS.copy()
        
    def _check_config(self):
        """
        检查API配置是否完整
        :return: 是否配置完整
        """
        required_configs = ["api_base_url", "appid", "appsecret"]
        for config in required_configs:
            # 对于appid和appsecret，也检查环境变量
            if config == "appid" and os.environ.get("WECHAT_APPID"):
                continue
            if config == "appsecret" and os.environ.get("WECHAT_APPSECRET"):
                continue
            if not self.api_config.get(config):
                log_message(f"缺少必要配置: {config}", "ERROR")
                return False
        return True
    
    def _refresh_access_token(self):
        """
        刷新access_token
        :return: access_token
        """
        # 检查是否在有效期内
        if self.access_token and time.time() < self.token_expire_time:
            log_message(f"使用缓存的access_token（剩余{int(self.token_expire_time - time.time())}秒）")
            return self.access_token
        
        if not self._check_config():
            log_message("配置不完整，无法刷新access_token", "ERROR")
            return None
        
        try:
            # 从环境变量获取凭证（优先级高于配置文件）
            appid = os.environ.get('WECHAT_APPID', self.api_config["appid"])
            appsecret = os.environ.get('WECHAT_APPSECRET', self.api_config["appsecret"])
            
            params = {
                "grant_type": "client_credential",
                "appid": appid,
                "secret": appsecret
            }
            
            url = f"{self.api_config['api_base_url']}{self.api_paths.get('access_token', '/cgi-bin/token')}"
            log_message(f"正在请求access_token: {url}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                # 设置过期时间，提前20分钟刷新
                self.token_expire_time = time.time() + result.get("expires_in", 7200) - 1200
                log_message(f"成功获取access_token，有效期至{datetime.fromtimestamp(self.token_expire_time)}")
                return self.access_token
            else:
                log_message(f"获取access_token失败: {result.get('errmsg', '未知错误')}", "ERROR")
                return None
        except Exception as e:
            log_message(f"请求access_token异常: {str(e)}", "ERROR")
            return None
    
    def _record_operation(self, operation_type, status, details=None):
        """
        记录API操作日志
        :param operation_type: 操作类型
        :param status: 操作状态
        :param details: 操作详情
        """
        operation_record = {
            "timestamp": datetime.now().isoformat(),
            "type": operation_type,
            "status": status,
            "details": details or {}
        }
        self.operation_history.append(operation_record)
        # 限制历史记录数量，避免内存溢出
        if len(self.operation_history) > 1000:
            self.operation_history.pop(0)
        log_message(f"记录操作: {operation_type} - {status}")
        
    def get_access_token(self):
        """
        获取access_token（公共方法，供外部调用）
        :return: access_token字符串或None
        """
        return self._refresh_access_token()

    def _api_request(self, api_path, method="post", params=None, data=None, files=None):
        """
        发送API请求
        :param api_path: API路径
        :param method: 请求方法，默认post
        :param params: URL参数
        :param data: 请求数据
        :param files: 文件数据
        :return: API响应结果
        """
        # 确保access_token有效
        if not self._refresh_access_token():
            return {"success": False, "error": "无法获取有效的access_token"}
        
        # 准备请求参数
        if params is None:
            params = {}
        params["access_token"] = self.access_token
        
        # 准备请求URL
        url = f"{self.api_config['api_base_url']}{api_path}"
        
        # 记录请求信息（屏蔽敏感信息）
        request_info = {
            "url": url,
            "method": method,
            "params": {k: v for k, v in params.items() if k != 'access_token'}
        }
        
        # 如果有数据，记录数据长度但不记录完整数据（避免日志过大）
        if data:
            request_info["data_size"] = len(json.dumps(data)) if isinstance(data, dict) else len(str(data))
        
        log_message(f"正在发送{method.upper()}请求: {request_info}", "DEBUG")
        
        try:
            if method.lower() == "get":
                response = self.session.get(url, params=params)
            else:
                if files:
                    response = self.session.post(url, params=params, data=data, files=files)
                else:
                    response = self.session.post(url, params=params, json=data)
            
            # 记录响应状态
            log_message(f"收到响应: 状态码={response.status_code}", "DEBUG")
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 检查微信API错误码
            if result.get("errcode") == 0 or "errcode" not in result:
                log_message(f"API请求成功: {api_path}")
                # 记录成功操作
                self._record_operation(api_path, "success", {"response": result})
                return {"success": True, "data": result}
            else:
                error_msg = f"API错误 {result.get('errcode', 'unknown')}: {result.get('errmsg', '未知错误')}"
                log_message(error_msg, "ERROR")
                # 记录失败操作
                self._record_operation(api_path, "error", {"error": error_msg, "response": result})
                return {"success": False, "error": error_msg, "data": result}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            log_message(error_msg, "ERROR")
            # 记录异常操作
            self._record_operation(api_path, "exception", {"error": str(e)})
            
            # 增加重试逻辑（针对网络问题）
            if isinstance(e, (requests.exceptions.ConnectionError, 
                             requests.exceptions.Timeout, 
                             requests.exceptions.ChunkedEncodingError)):
                log_message("遇到网络异常，将尝试重试...", "WARNING")
                # 简单重试一次
                time.sleep(1)  # 等待1秒后重试
                try:
                    if method.lower() == "get":
                        response = self.session.get(url, params=params)
                    else:
                        if files:
                            response = self.session.post(url, params=params, data=data, files=files)
                        else:
                            response = self.session.post(url, params=params, json=data)
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get("errcode") == 0 or "errcode" not in result:
                        log_message(f"API请求重试成功: {api_path}")
                        self._record_operation(api_path, "success", {"response": result, "retry": True})
                        return {"success": True, "data": result}
                except Exception as retry_e:
                    log_message(f"重试请求仍然失败: {str(retry_e)}", "ERROR")
                        
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"处理响应异常: {str(e)}"
            log_message(error_msg, "ERROR")
            # 记录异常操作
            self._record_operation(api_path, "exception", {"error": str(e)})
            return {"success": False, "error": error_msg}
    
    def upload_image(self, image_path):
        """
        上传商品图片
        :param image_path: 图片本地路径
        :return: 上传结果，包含图片URL
        """
        if not os.path.exists(image_path):
            return {"success": False, "error": f"图片文件不存在: {image_path}"}
        
        try:
            # 准备文件数据
            with open(image_path, 'rb') as f:
                files = {'media': f}
                
                # 调用上传图片API
                result = self._api_request(self.api_paths['upload_image'], method="post", files=files)
                
                # 记录操作历史
                self.operation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "operation": "upload_image",
                    "image_path": image_path,
                    "result": result
                })
                
                return result
                
        except Exception as e:
            error_msg = f"上传图片失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return {"success": False, "error": error_msg}
    
    def upload_product(self, product_data):
        """
        上传视频号小店商品
        :param product_data: 商品数据字典
        :return: 上传结果
        """
        try:
            # 验证必填字段
            required_fields = ['title', 'desc', 'category_id1', 'category_id2', 'sku_list']
            for field in required_fields:
                if field not in product_data:
                    return {"success": False, "error": f"缺少必填字段: {field}"}
            
            # 使用视频号小店的商品创建API路径
            api_path = self.api_paths.get('add_product', '/channels/ec/product/create')
            
            # 调用商品创建API
            log_message(f"正在上传商品: {product_data.get('title', '未命名')}")
            result = self._api_request(api_path, method="post", data=product_data)
            
            # 记录操作历史
            self.operation_history.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "upload_product",
                "product_title": product_data.get('title'),
                "result": result
            })
            
            return result
            
        except Exception as e:
            error_msg = f"上传商品失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return {"success": False, "error": error_msg}
    
    def add_product(self, product_data):
        """
        添加商品
        :param product_data: 商品数据字典
        :return: 添加结果
        """
        # 验证必填字段，但排除product_id（这通常是返回值）
        for field in WECHAT_SHOP_REQUIRED_FIELDS:
            if field != "product_id" and field not in product_data:
                return {"success": False, "error": f"缺少必填字段: {field}"}
        
        try:
            # 调用添加商品API
            result = self._api_request(self.api_paths['add_product'], method="post", data=product_data)
            
            # 记录操作历史
            self.operation_history.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "add_product",
                "product_id": product_data.get("product_id"),
                "result": result
            })
            
            return result
            
        except Exception as e:
            error_msg = f"添加商品失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return {"success": False, "error": error_msg}
    
    def batch_upload_products_from_data(self, products):
        """
        直接从商品数据列表批量上传商品
        :param products: 商品数据列表
        :return: 上传结果统计
        """
        # 验证商品数据
        if not products or not isinstance(products, list):
            return {"success": False, "error": "无效的商品数据列表"}
        
        # 记录开始时间
        start_time = time.time()
        total_count = len(products)
        success_count = 0
        error_count = 0
        error_list = []
        
        log_message(f"开始批量上传{total_count}个商品")
        
        try:
            for i, product in enumerate(products, 1):
                log_message(f"正在上传商品 {i}/{total_count}: {product.get('product_name', '未命名')}")
                
                # 检查并上传商品图片
                if 'main_image' in product and os.path.exists(product['main_image']):
                    upload_result = self.upload_image(product['main_image'])
                    if upload_result['success']:
                        product['main_image'] = upload_result['data'].get('image_url', '')
                    else:
                        error_msg = f"上传主图失败: {upload_result.get('error', '未知错误')}"
                        log_message(error_msg, "ERROR")
                        
                        error_list.append({"index": i, "product_id": product.get("product_id"), "error": error_msg})
                        error_count += 1
                        continue
                
                # 调用添加商品API
                result = self.add_product(product)
                
                if result['success']:
                    success_count += 1
                    log_message(f"商品上传成功: {product.get('product_name', '未命名')}")
                else:
                    error_msg = result.get('error', '未知错误')
                    log_message(f"商品上传失败: {error_msg}", "ERROR")
                    error_list.append({"index": i, "product_id": product.get("product_id"), "error": error_msg})
                    error_count += 1
                
                # 避免请求过于频繁
                time.sleep(1)
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            
            # 生成结果报告
            report = {
                "success": True,
                "total": total_count,
                "success_count": success_count,
                "error_count": error_count,
                "error_list": error_list,
                "elapsed_time": f"{elapsed_time:.2f}秒",
                "timestamp": datetime.now().isoformat()
            }
            
            # 添加到操作历史
            self.operation_history.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "batch_upload_products_from_data",
                "report": report
            })
            
            return report
            
        except Exception as e:
            error_msg = f"批量上传过程中发生错误: {str(e)}"
            log_message(error_msg, "ERROR")
            return {
                "success": False,
                "error": error_msg,
                "total": total_count,
                "processed_count": success_count + error_count,
                "success_count": success_count,
                "error_count": error_count,
                "error_list": error_list
            }
    
    def batch_upload_products(self, csv_file):
        """
        批量上传商品
        :param csv_file: CSV文件路径
        :return: 上传结果统计
        """
        # 验证CSV文件
        if not os.path.exists(csv_file):
            return {"success": False, "error": f"CSV文件不存在: {csv_file}"}
        
        # 加载商品数据
        products = load_products_from_csv(csv_file)
        if not products:
            return {"success": False, "error": "未加载到商品数据"}
        
        # 调用数据上传方法
        return self.batch_upload_products_from_data(products)
    
    def get_product(self, product_id):
        """
        获取商品详情
        :param product_id: 商品ID
        :return: 商品详情
        """
        try:
            data = {"product_id": product_id}
            result = self._api_request(self.api_paths['get_product'], method="post", data=data)
            
            # 记录操作历史
            self.operation_history.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "get_product",
                "product_id": product_id,
                "result": result
            })
            
            return result
            
        except Exception as e:
            error_msg = f"获取商品详情失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return {"success": False, "error": error_msg}
    
    def get_shop_info(self):
        """
        获取店铺信息
        :return: 店铺信息
        """
        try:
            result = self._api_request(self.api_paths['get_shop_info'], method="get")
            
            # 记录操作历史
            self.operation_history.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "get_shop_info",
                "result": result
            })
            
            return result
            
        except Exception as e:
            error_msg = f"获取店铺信息失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return {"success": False, "error": error_msg}
    
    def update_shop_info(self, shop_info):
        """
        更新店铺信息
        :param shop_info: 店铺信息字典
        :return: 更新结果
        """
        try:
            result = self._api_request(self.api_paths['update_shop_info'], method="post", data=shop_info)
            
            # 记录操作历史
            self.operation_history.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "update_shop_info",
                "result": result
            })
            
            return result
            
        except Exception as e:
            error_msg = f"更新店铺信息失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return {"success": False, "error": error_msg}
    
    def verify_upload_result(self, report=None):
        """
        验证上传结果
        :param report: 上传报告（可选），如果不提供则使用最后一次批量上传的报告
        :return: 验证结果
        """
        if not report:
            # 查找最后一次批量上传记录
            for record in reversed(self.operation_history):
                if record.get("operation") == "batch_upload_products" and "report" in record:
                    report = record["report"]
                    break
            
        if not report:
            return {"success": False, "error": "未找到上传记录"}
        
        # 生成验证报告
        verify_report = {
            "success": True,
            "total_products": report.get("total", 0),
            "successfully_uploaded": report.get("success_count", 0),
            "failed_uploads": report.get("error_count", 0),
            "verification_time": datetime.now().isoformat(),
            "details": report
        }
        
        # 对于上传失败的商品，可以在这里进行额外的验证逻辑
        # 例如重新尝试上传，或者获取更多错误详情
        
        return verify_report
    
    def get_channels_product_list(self, page=1, size=10, product_id=None, title=None, product_status=None):
        """
        获取视频号小店商品列表
        参考文档: https://developers.weixin.qq.com/doc/store/shop/API/channels-shop-product/shop/api_getproductlist.html
        
        :param page: 页码，从1开始，默认1
        :param size: 每页大小，默认10，最大100
        :param product_id: 商品ID，可选
        :param title: 商品标题，可选
        :param product_status: 商品状态，可选
        :return: 商品列表数据，包含product_ids、next_key、total_num等信息
        """
        try:
            # 确保access_token有效
            if not self._refresh_access_token():
                log_message("获取商品列表失败：无法获取有效的access_token", "ERROR")
                return None
            
            # 构建查询参数（只有access_token）
            params = {
                "access_token": self.access_token
            }
            
            # 构建请求体
            data = {
                "page_size": min(size, 100),  # 每页数量，必填
                "page": page  # 页码
            }
            
            # 添加可选参数
            if product_id:
                data["product_id"] = product_id
            if title:
                data["title"] = title
            if product_status is not None:
                data["status"] = product_status
            
            # 调用API（使用POST请求）
            api_path = self.api_paths["get_channels_product_list"]
            response = self._api_request(api_path, method="post", params=params, data=data)
            
            # 处理API响应
            if response and response.get("success"):
                # 检查响应数据
                data_content = response.get("data", {})
                
                # 检查API是否返回了嵌套的错误码
                if "errcode" in data_content and data_content["errcode"] == 0:
                    log_message(f"成功获取第{page}页视频号小店商品列表")
                    
                    # 记录操作历史
                    self.operation_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "operation": "get_channels_product_list",
                        "params": params,
                        "success": True,
                        "result": {
                            "total_num": data_content.get("total_num", 0),
                            "product_count": len(data_content.get("product_ids", [])),
                            "page": page,
                            "size": size
                        }
                    })
                    
                    return {
                        "success": True,
                        "product_ids": data_content.get("product_ids", []),
                        "next_key": data_content.get("next_key"),
                        "total_num": data_content.get("total_num", 0)
                    }
                # 处理直接在根级别的成功响应
                elif "product_ids" in data_content:
                    log_message(f"成功获取第{page}页视频号小店商品列表，共{data_content.get('total_num', 0)}个商品")
                    
                    # 记录操作历史
                    self.operation_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "operation": "get_channels_product_list",
                        "params": params,
                        "success": True,
                        "result": {
                            "total_num": data_content.get("total_num", 0),
                            "product_count": len(data_content.get("product_ids", [])),
                            "page": page,
                            "size": size
                        }
                    })
                    
                    return data_content
                # 处理传统格式的响应
                elif data_content:
                    log_message(f"成功获取第{page}页视频号小店商品列表")
                    return data_content
            
            # 处理错误情况
            error_msg = f"获取视频号小店商品列表失败: {response}"
            log_message(error_msg, "ERROR")
            
            # 记录操作历史
            self.operation_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operation": "get_channels_product_list",
                "params": params,
                "success": False,
                "error": error_msg
            })
            
            return response if response else None
            
        except Exception as e:
            error_msg = f"获取视频号小店商品列表异常: {str(e)}"
            log_message(error_msg, "ERROR")
            
            # 记录操作历史
            self.operation_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operation": "get_channels_product_list",
                "params": {"page": page, "size": size, "product_id": product_id, "title": title, "product_status": product_status},
                "success": False,
                "error": error_msg
            })
            
            return None
    
    def get_category(self):
        """
        获取微信小店商品类目（传统API）
        使用API路径: /merchant/category/getall
        获取所有可用的商品类目信息
        
        :return: 类目信息列表
        """
        try:
            # 调用获取类目API
            path = self.api_paths['get_category']
            result = self._api_request(path, method="get")
            
            # 记录操作历史
            self._record_operation("get_category", "success" if result.get("success") else "error", path)
            
            return result
            
        except Exception as e:
            error_msg = f"获取商品类目失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return {"success": False, "error": error_msg}
    
    def get_all_category(self):
         """
         获取所有视频号小店类目信息（官方标准接口）
         根据文档：https://developers.weixin.qq.com/doc/store/shop/API/channels-shop-category/api_getallcategory.html
         支持获取全部类目信息、资质信息、商品资质信息
         
         :return: 类目数据结果
         """
         try:
             # 发送请求 - 注意：官方文档显示这个接口不需要请求体参数
             # 使用GET请求，参数通过query string传递access_token
             path = self.api_paths["get_all_category"]
             result = self._api_request(path, method="GET")
             
             # 记录操作历史
             self._record_operation("get_all_category", "success" if result.get("success") else "error", path)
             
             # 直接返回_api_request的结果，保持一致性
             return result
             
         except Exception as e:
             # 记录错误
             error_msg = f"获取视频号小店类目失败: {str(e)}"
             log_message(error_msg, "ERROR")
             return {
                 "success": False,
                 "error": error_msg
             }
    
    def get_channels_category(self):
        """
        获取视频号小店商品类目
        使用API路径: /channels/ec/category/batchget
        获取视频号小店平台的商品类目信息
        
        :return: 类目信息列表
        """
        try:
            # 准备请求参数
            data = {
                "need_all": 1,  # 获取所有层级类目
                "get_child": 1  # 获取子类目
            }
            
            # 调用视频号小店类目API
            path = self.api_paths['get_channels_category']
            log_message(f"准备调用类目API，路径: {path}，参数: {data}", "DEBUG")
            result = self._api_request(path, method="post", data=data)
            
            # 详细记录返回结果
            log_message(f"API返回结果: {result}", "DEBUG")
            
            # 记录操作历史
            self._record_operation("get_channels_category", "success" if result.get("success") else "error", path)
            
            return result
            
        except Exception as e:
            error_msg = f"获取视频号小店商品类目失败: {str(e)}"
            log_message(error_msg, "ERROR")
            log_message(f"异常详情: {repr(e)}", "DEBUG")
            return {"success": False, "error": error_msg}
            
    def get_operation_history(self):
        """
        获取操作历史
        :return: 操作历史列表
        """
        return self.operation_history
    
    def get_product_detail(self, product_id):
        """
        获取视频号小店商品详情
        参考文档: https://developers.weixin.qq.com/doc/store/shop/API/channels-shop-product/shop/api_productdetail.html
        
        :param product_id: 商品ID
        :return: 商品详情数据
        """
        try:
            # 确保access_token有效
            if not self._refresh_access_token():
                log_message("获取商品详情失败：无法获取有效的access_token", "ERROR")
                return None
            
            # 构建请求参数
            data = {
                "product_id": product_id,
                "data_type": 1  # 1: 获取线上数据
            }
            
            # 调用API
            api_path = self.api_paths["get_product_detail"]
            response = self._api_request(api_path, method="post", data=data)
            
            if response and response.get("success"):
                log_message(f"成功获取商品详情，商品ID: {product_id}")
                
                # 记录操作历史
                self.operation_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "operation": "get_product_detail",
                    "params": {"product_id": product_id},
                    "success": True,
                    "result": "获取成功"
                })
                
                return response
            else:
                error_msg = f"获取商品详情失败: {response.get('error', '未知错误') if response else '未知错误'}"
                log_message(error_msg, "ERROR")
                
                # 记录操作历史
                self.operation_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "operation": "get_product_detail",
                    "params": {"product_id": product_id},
                    "success": False,
                    "error": error_msg
                })
                
                return response if response else None
                
        except Exception as e:
            error_msg = f"获取商品详情异常: {str(e)}"
            log_message(error_msg, "ERROR")
            
            # 记录操作历史
            self.operation_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operation": "get_product_detail",
                "params": {"product_id": product_id},
                "success": False,
                "error": error_msg
            })
            
            return None
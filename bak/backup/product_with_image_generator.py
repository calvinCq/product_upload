#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from typing import Dict, List, Any, Optional
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入所需模块
from volcano_image_generator import VolcanoImageGenerator
from config_manager import ConfigManager

# 尝试导入微信小店API模块
try:
    from wechat_shop_api import WechatShopAPI, log_message
    WECHAT_API_AVAILABLE = True
except ImportError as e:
    logger.warning(f"无法导入微信小店API模块: {e}")
    WECHAT_API_AVAILABLE = False


class ProductWithImageGenerator:
    """
    商品图片生成与上传集成类
    负责生成商品图片并上传商品到微信小店
    """
    
    def __init__(self, wechat_api_client=None, volcano_config=None, config_path: str = None):
        """
        初始化集成类
        
        Args:
            wechat_api_client: 微信小店API客户端实例，可选
            volcano_config: 火山大模型配置对象，可选
            config_path: 配置文件路径，可选
        """
        # 加载配置
        self.config_manager = ConfigManager(config_path) if config_path else ConfigManager("product_generator_config.json")
        self.config_manager.load_config()
        
        # 直接使用传入的volcano_config或从配置管理器获取
        if volcano_config is None:
            volcano_config = self.config_manager.get_volcano_api_config()
        
        # 设置火山大模型配置相关属性
        self.main_images_count = volcano_config.get("main_images_count", 3)
        self.detail_images_count = volcano_config.get("detail_images_count", 2)
        self.image_save_dir = volcano_config.get("image_save_dir", "./temp_images")
        
        # 初始化火山大模型图片生成器
        self.image_generator = VolcanoImageGenerator(config=volcano_config)
        
        # 初始化微信小店API客户端
        self.wechat_api = wechat_api_client
        if not self.wechat_api and WECHAT_API_AVAILABLE:
            api_config = self.config_manager.get_api_config()
            if api_config.get("appid") and api_config.get("appsecret"):
                self.wechat_api = WechatShopAPI(
                    appid=api_config["appid"],
                    appsecret=api_config["appsecret"]
                )
            else:
                logger.warning("缺少微信小店API配置")
    
    def generate_images_and_upload_product(self, product_description: str, 
                                          product_data: Dict[str, Any],
                                          shop_type: str = None) -> Dict[str, Any]:
        """
        生成图片并上传商品
        
        Args:
            product_description: 商品描述文本或包含商品描述的文件路径
            product_data: 商品基本数据
            shop_type: 店铺类型，可选值：'traditional'(传统小店) 或 'video_shop'(视频号小店)
                      如果不提供，会根据product_data中是否包含video_info字段自动判断
        
        Returns:
            上传结果字典
        """
        try:
            # 根据shop_type参数或product_data内容确定商品类型
            if shop_type:
                is_video_shop = shop_type == 'video_shop'
            else:
                is_video_shop = 'video_info' in product_data
            
            # 1. 生成商品图片
            logger.info("开始生成商品图片...")
            main_image_paths = self.image_generator.generate_product_images(
                product_description=product_description,
                count=self.main_images_count,
                image_type="main",
                save_dir=self.image_save_dir
            )
            
            detail_image_paths = self.image_generator.generate_product_images(
                product_description=product_description,
                count=self.detail_images_count,
                image_type="detail",
                save_dir=self.image_save_dir
            )
            
            logger.info(f"成功生成 {len(main_image_paths)} 张主图和 {len(detail_image_paths)} 张详情图")
            
            # 2. 上传图片到微信小店
            logger.info("开始上传图片到微信小店...")
            main_image_urls = self._upload_generated_images(main_image_paths)
            detail_image_urls = self._upload_generated_images(detail_image_paths)
            
            logger.info(f"成功上传 {len(main_image_urls)} 张主图和 {len(detail_image_urls)} 张详情图")
            
            # 3. 更新商品数据，添加图片URL
            updated_product_data = self._update_product_data_with_images(
                product_data, main_image_urls, detail_image_urls, is_video_shop
            )
            
            # 4. 上传商品到微信小店
            logger.info(f"开始上传商品到微信小店... (商品类型: {'视频号小店' if is_video_shop else '传统小店'})")
            upload_result = self._upload_product(updated_product_data, is_video_shop)
            
            # 5. 返回完整结果
            result = {
                "success": True,
                "message": "商品上传成功",
                "product_id": upload_result.get("product_id"),
                "generated_images": {
                    "main": main_image_paths,
                    "detail": detail_image_paths
                },
                "uploaded_image_urls": {
                    "main": main_image_urls,
                    "detail": detail_image_urls
                },
                "upload_result": upload_result
            }
            
            logger.info(f"商品上传完成: {result.get('product_id')}")
            return result
            
        except Exception as e:
            logger.error(f"处理过程中发生错误: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "error_type": type(e).__name__
            }
    
    def _upload_generated_images(self, image_paths: List[str]) -> List[str]:
        """
        上传生成的图片到微信小店
        
        Args:
            image_paths: 图片文件路径列表
        
        Returns:
            上传后的图片URL列表
        """
        if not self.wechat_api:
            raise Exception("微信小店API客户端未初始化")
        
        uploaded_urls = []
        
        for image_path in image_paths:
            try:
                if not os.path.exists(image_path):
                    logger.warning(f"图片文件不存在: {image_path}")
                    continue
                
                # 调用微信小店API上传图片
                upload_result = self.wechat_api.upload_image(image_path)
                
                if upload_result.get("errcode") == 0 and "image_url" in upload_result:
                    uploaded_urls.append(upload_result["image_url"])
                    logger.info(f"图片上传成功: {image_path} -> {upload_result['image_url']}")
                else:
                    logger.error(f"图片上传失败: {image_path}, 错误: {upload_result}")
                    
            except Exception as e:
                logger.error(f"上传图片 {image_path} 时发生错误: {str(e)}")
        
        if not uploaded_urls:
            raise Exception("无法上传任何图片")
        
        return uploaded_urls
    
    def _update_product_data_with_images(self, product_data: Dict[str, Any], 
                                        main_image_urls: List[str], 
                                        detail_image_urls: List[str],
                                        is_video_shop: bool = None) -> Dict[str, Any]:
        """
        更新商品数据，添加图片URL
        
        Args:
            product_data: 原始商品数据
            main_image_urls: 主图URL列表
            detail_image_urls: 详情图URL列表
            is_video_shop: 是否为视频号小店商品，如果为None则自动判断
        
        Returns:
            更新后的商品数据
        """
        # 创建副本以避免修改原始数据
        updated_data = product_data.copy()
        
        # 确定是否为视频号小店商品
        if is_video_shop is None:
            is_video_shop = 'video_info' in updated_data
        
        if is_video_shop:
            # 视频号小店商品格式
            if "head_img_list" not in updated_data:
                updated_data["head_img_list"] = []
            
            # 添加主图
            updated_data["head_img_list"].extend(main_image_urls)
            
            # 添加详情图
            if "desc_info" not in updated_data:
                updated_data["desc_info"] = {}
            if "img_list" not in updated_data["desc_info"]:
                updated_data["desc_info"]["img_list"] = []
            updated_data["desc_info"]["img_list"].extend(detail_image_urls)
            
        else:
            # 传统小店商品格式
            if "main_img" not in updated_data:
                updated_data["main_img"] = []
            
            # 添加主图
            updated_data["main_img"].extend(main_image_urls)
            
            # 添加详情图
            if "desc_img" not in updated_data:
                updated_data["desc_img"] = []
            updated_data["desc_img"].extend(detail_image_urls)
        
        logger.info("商品数据已更新，添加了图片URL")
        return updated_data
    
    def _upload_product(self, product_data: Dict[str, Any], is_video_shop: bool = None) -> Dict[str, Any]:
        """
        上传商品到微信小店
        
        Args:
            product_data: 完整的商品数据
            is_video_shop: 是否为视频号小店商品，如果为None则自动判断
        
        Returns:
            上传结果
        """
        if not self.wechat_api:
            raise Exception("微信小店API客户端未初始化")
        
        try:
            # 确定是否为视频号小店商品
            if is_video_shop is None:
                is_video_shop = 'video_info' in product_data
            
            # 根据商品类型调用相应的上传方法
            if is_video_shop:
                # 视频号小店商品
                result = self.wechat_api.upload_product(product_data)
            else:
                # 传统小店商品
                result = self.wechat_api.add_product(product_data)
            
            return result
            
        except Exception as e:
            logger.error(f"上传商品时发生错误: {str(e)}")
            raise
    
    def generate_images_only(self, product_description: str) -> Dict[str, List[str]]:
        """
        只生成图片，不进行上传
        
        Args:
            product_description: 商品描述文本或包含商品描述的文件路径
        
        Returns:
            生成的图片路径字典
        """
        main_image_paths = self.image_generator.generate_product_images(
            product_description=product_description,
            count=self.main_images_count,
            image_type="main",
            save_dir=self.image_save_dir
        )
        
        detail_image_paths = self.image_generator.generate_product_images(
            product_description=product_description,
            count=self.detail_images_count,
            image_type="detail",
            save_dir=self.image_save_dir
        )
        
        return {
            "main": main_image_paths,
            "detail": detail_image_paths
        }
    
    def cleanup_temp_images(self) -> None:
        """
        清理临时图片文件
        """
        try:
            if os.path.exists(self.image_save_dir):
                for filename in os.listdir(self.image_save_dir):
                    file_path = os.path.join(self.image_save_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"已删除临时文件: {file_path}")
        except Exception as e:
            logger.error(f"清理临时文件时发生错误: {str(e)}")


def main():
    """
    测试商品图片生成与上传集成功能
    """
    # 从环境变量获取API密钥
    volcano_api_key = os.environ.get("VOLCANO_API_KEY")
    
    if not volcano_api_key:
        print("错误: 请设置VOLCANO_API_KEY环境变量")
        print("可以通过以下方式设置:")
        print("1. 在命令行中: set VOLCANO_API_KEY=your_api_key")
        print("2. 在.env文件中添加: VOLCANO_API_KEY=your_api_key")
        print("3. 在配置文件中添加volcano_api部分的api_key配置")
        return
    
    # 创建集成实例
    # 创建火山配置对象
    volcano_config = {
        "api_key": volcano_api_key
    }
    generator = ProductWithImageGenerator(volcano_config=volcano_config)
    
    # 测试数据
    product_description = "一款时尚的智能手机，黑色机身，全面屏设计，高清摄像头"
    
    # 简单的商品数据结构（根据实际需求调整）
    product_data = {
        "title": "测试智能手机",
        "desc": "这是一款高性能智能手机，配备最新处理器和高清摄像头",
        "price": 299900,  # 价格（分）
        "original_price": 399900,
        "stock": 100,
        "category_id1": "381003",
        "category_id2": "380003",
        "sku_list": [
            {
                "price": 299900,
                "original_price": 399900,
                "stock": 100,
                "sku_attr": ["黑色", "128GB"]
            }
        ]
    }
    
    try:
        print("测试生成图片功能...")
        # 只生成图片，不上传
        images = generator.generate_images_only(product_description)
        print(f"生成了 {len(images['main'])} 张主图和 {len(images['detail'])} 张详情图")
        print(f"主图路径: {images['main']}")
        print(f"详情图路径: {images['detail']}")
        
        # 注意：要完整测试上传功能，需要正确配置微信小店API
        print("\n注意：要测试完整的上传功能，请确保微信小店API配置正确")
        
    except Exception as e:
        print(f"错误: {str(e)}")
    finally:
        # 清理临时文件
        print("\n清理临时图片文件...")
        generator.cleanup_temp_images()


if __name__ == "__main__":
    main()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
from datetime import datetime

# 尝试导入必要的模块
import time

try:
    from config_manager import ConfigManager
except ImportError:
    logging.error("警告：无法导入ConfigManager模块")

try:
    from volcano_image_generator import VolcanoImageGenerator
except ImportError:
    logging.error("警告：无法导入VolcanoImageGenerator模块")

try:
    from product_with_image_generator import ProductWithImageGenerator
except ImportError:
    logging.error("警告：无法导入ProductWithImageGenerator模块")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='test_execution.log',
    filemode='w'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger('test_image_and_product')

class TestImageAndProduct:
    """
    测试图片生成和商品上传功能
    """
    
    def __init__(self):
        """
        初始化测试类
        """
        self.config_manager = None
        self.volcano_generator = None
        self.product_generator = None
        self.test_results = {
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': None,
            'environment_check': {},
            'image_generation': {},
            'product_upload': {}
        }
    
    def check_environment(self):
        """
        检查环境配置
        """
        logger.info("开始环境配置检查...")
        
        # 检查.env文件
        env_file_path = '.env'
        env_exists = os.path.exists(env_file_path)
        self.test_results['environment_check']['env_file_exists'] = env_exists
        
        if not env_exists:
            logger.warning(f"未找到.env文件，尝试从.env.example复制")
            if os.path.exists('.env.example'):
                try:
                    with open('.env.example', 'r', encoding='utf-8') as f:
                        with open('.env', 'w', encoding='utf-8') as out_f:
                            out_f.write(f.read())
                    logger.info("已复制.env.example到.env")
                    env_exists = True
                    self.test_results['environment_check']['env_file_exists'] = True
                except Exception as e:
                    logger.error(f"复制.env.example失败: {str(e)}")
        
        # 初始化配置管理器，提供默认配置文件路径
        try:
            # 尝试使用默认配置文件路径
            config_path = 'product_generator_config.json'
            if os.path.exists(config_path):
                logger.info(f"使用配置文件: {config_path}")
                self.config_manager = ConfigManager(config_path)
            else:
                logger.info("配置文件不存在，使用默认配置")
                self.config_manager = ConfigManager()
                
            # 尝试加载配置
            if hasattr(self.config_manager, 'load_config'):
                self.config_manager.load_config()
                
            self.test_results['environment_check']['config_manager_init'] = True
            logger.info("配置管理器初始化成功")
            
            # 检查必要的配置项
            try:
                volcano_config = self.config_manager.get_volcano_api_config()
                
                self.test_results['environment_check']['volcano_api_key_exists'] = 'api_key' in volcano_config and volcano_config['api_key']
                self.test_results['environment_check']['volcano_model_name_exists'] = 'model_name' in volcano_config and volcano_config['model_name']
                
                logger.info(f"火山大模型API密钥: {'已配置' if self.test_results['environment_check']['volcano_api_key_exists'] else '未配置'}")
                logger.info(f"火山大模型模型名称: {'已配置' if self.test_results['environment_check']['volcano_model_name_exists'] else '未配置'}")
            except Exception as e:
                logger.error(f"检查火山配置时出错: {str(e)}")
                self.test_results['environment_check']['volcano_api_key_exists'] = False
                self.test_results['environment_check']['volcano_model_name_exists'] = False
                
        except Exception as e:
            logger.error(f"配置管理器初始化失败: {str(e)}")
            self.test_results['environment_check']['config_manager_init'] = False
            self.test_results['environment_check']['error'] = str(e)
        
        logger.info("环境配置检查完成")
        
        # 为了测试目的，即使检查不完全通过也尝试继续，不再检查微信相关配置
        can_proceed = self.test_results['environment_check'].get('config_manager_init', False) and \
                      self.test_results['environment_check'].get('volcano_api_key_exists', False)
        
        if not can_proceed:
            logger.warning("环境检查未完全通过，但尝试继续测试...")
        
        return True  # 总是返回True以允许继续测试
    
    def test_image_generation(self):
        """
        测试图片生成功能
        """
        logger.info("开始图片生成测试...")
        
        try:
            # 初始化图片生成器
            volcano_config = self.config_manager.get_volcano_api_config()
            logger.info(f"火山配置信息: {volcano_config}")  # 打印配置信息用于调试
            self.volcano_generator = VolcanoImageGenerator(config=volcano_config)
            self.test_results['image_generation']['init_success'] = True
            logger.info(f"图片生成器初始化成功，使用模型: {getattr(self.volcano_generator, 'model_name', '默认模型')}")
            
            # 准备测试商品描述
            product_description = "时尚休闲运动鞋，舒适透气，防滑耐磨，适合日常穿着和轻度运动"
            image_count = 1
            save_dir = './test_generated_images'
            os.makedirs(save_dir, exist_ok=True)
            
            # 直接调用底层方法进行更详细的调试
            try:
                prompt = self.volcano_generator._build_prompt(product_description, "main")
                logger.info(f"构建的提示词: {prompt}")
                
                # 手动发送请求并打印响应
                import requests
                import json
                
                url = f"{self.volcano_generator.api_base_url}{self.volcano_generator.image_generation_endpoint}"
                payload = {
                    "model": self.volcano_generator.model_name or "doubao-seedream-4-0-250828",
                    "prompt": prompt,
                    "size": "2K",
                    "sequential_image_generation": "disabled",
                    "stream": False,
                    "response_format": "url",
                    "watermark": True
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.volcano_generator.api_key}"  # 完整密钥
                }
                
                logger.info(f"发送请求到URL: {url}")
                logger.info(f"请求头: {headers}")
                logger.info(f"请求体: {payload}")
                
                # 发送测试请求
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                logger.info(f"HTTP状态码: {response.status_code}")
                logger.info(f"响应内容类型: {response.headers.get('Content-Type')}")
                logger.info(f"响应内容长度: {len(response.content)}字节")
                
                # 尝试打印响应内容的前500个字符
                response_text = response.text
                logger.info(f"响应内容前500字符: {response_text[:500]}...")
                
                # 检查是否是JSON格式
                try:
                    response_json = response.json()
                    logger.info(f"响应是有效的JSON格式")
                    logger.info(f"JSON响应前200字符: {str(response_json)[:200]}...")
                except json.JSONDecodeError:
                    logger.error(f"响应不是有效的JSON格式")
                    
            except Exception as api_test_error:
                logger.error(f"API测试请求失败: {str(api_test_error)}")
                import traceback
                logger.error(f"API测试错误堆栈: {traceback.format_exc()}")
            
            # 记录开始时间
            start_time = time.time()
            
            # 尝试正常生成图片
            try:
                image_paths = self.volcano_generator.generate_product_images(
                    product_description=product_description,
                    count=image_count,
                    image_type="main",
                    save_dir=save_dir
                )
                
                # 记录结束时间
                end_time = time.time()
                
                if image_paths:
                    self.test_results['image_generation']['success'] = True
                    self.test_results['image_generation']['image_count'] = len(image_paths)
                    self.test_results['image_generation']['image_paths'] = image_paths
                    self.test_results['image_generation']['generation_time'] = round(end_time - start_time, 2)
                    self.test_results['image_generation']['model_used'] = getattr(self.volcano_generator, 'model_name', '默认模型')
                    
                    logger.info(f"图片生成成功，生成了 {len(image_paths)} 张图片")
                    logger.info(f"图片路径: {image_paths}")
                    logger.info(f"生成耗时: {self.test_results['image_generation']['generation_time']} 秒")
                    
                    # 验证图片文件存在
                    for img_path in image_paths:
                        if os.path.exists(img_path):
                            logger.info(f"图片文件存在: {img_path}, 大小: {os.path.getsize(img_path)}字节")
                        else:
                            logger.warning(f"图片文件不存在: {img_path}")
                    
                    return image_paths
                else:
                    logger.error("未能生成任何图片")
                    self.test_results['image_generation']['success'] = False
                    self.test_results['image_generation']['error'] = "未能生成任何图片"
                    return []
                    
            except Exception as generate_error:
                logger.error(f"生成图片时发生错误: {str(generate_error)}")
                self.test_results['image_generation']['success'] = False
                self.test_results['image_generation']['error'] = str(generate_error)
                import traceback
                logger.error(f"生成图片错误堆栈: {traceback.format_exc()}")
                return []
            
        except Exception as e:
            logger.error(f"图片生成测试框架异常: {str(e)}")
            self.test_results['image_generation']['success'] = False
            self.test_results['image_generation']['error'] = str(e)
            # 打印详细的错误堆栈
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return []
    
    def test_product_upload(self, image_paths=None):
        """
        测试商品上传功能
        """
        logger.info("开始商品上传测试...")
        
        # 暂时跳过商品上传测试，优先测试图片生成功能
        logger.info("暂未实现商品上传测试，将在图片生成测试成功后实现")
        self.test_results['product_upload']['success'] = False
        self.test_results['product_upload']['error'] = "暂未实现商品上传测试，将在图片生成测试成功后实现"
        return {}
    
    def run_complete_test(self):
        """
        运行完整的测试流程，优先测试图片生成功能
        """
        logger.info("开始测试流程，优先测试图片生成功能...")
        
        try:
            # 1. 检查环境
            if not self.check_environment():
                logger.error("环境检查失败，无法继续测试")
                return False
            
            # 2. 测试图片生成（优先测试）
            image_paths = self.test_image_generation()
            
            # 3. 暂时跳过商品上传测试
            logger.info("暂时跳过商品上传测试，专注于图片生成功能验证")
            
            # 4. 保存测试结果
            self.test_results['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('test_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
            logger.info("测试流程执行完成")
            logger.info(f"测试结果已保存到: test_results.json")
            
            # 更新验收文档
            self.update_acceptance_document()
            
            return True
            
        except Exception as e:
            logger.error(f"测试流程执行失败: {str(e)}")
            return False
    
    def update_acceptance_document(self):
        """
        更新验收文档
        """
        try:
            # 简化的验收文档更新，创建新的报告文件
            doc_content = f"""# 测试验收文档

## 测试概述
测试开始时间: {self.test_results.get('start_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
测试结束时间: {self.test_results.get('end_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}

## 环境检查
配置文件存在: {'✓' if self.test_results.get('environment_check', {}).get('env_file_exists', False) else '✗'}
配置管理器初始化: {'✓' if self.test_results.get('environment_check', {}).get('config_manager_init', False) else '✗'}
API密钥有效: {'✓' if self.test_results.get('environment_check', {}).get('volcano_api_key_exists', False) else '✗'}

## 图片生成测试
测试结果: {'通过' if self.test_results.get('image_generation', {}).get('success', False) else '失败'}
生成图片数量: {self.test_results.get('image_generation', {}).get('image_count', 0)}
生成耗时: {self.test_results.get('image_generation', {}).get('generation_time', 0)} 秒
错误信息: {self.test_results.get('image_generation', {}).get('error', '')}

## 商品上传测试
状态: 暂未测试

## 结论
{'图片生成功能测试通过' if self.test_results.get('image_generation', {}).get('success', False) else '图片生成功能测试失败，需要排查问题'}
"""
            
            # 保存验收报告
            doc_path = "验收测试报告.md"
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(doc_content)
            
            logger.info(f"验收测试报告已更新: {doc_path}")
            
        except Exception as e:
            logger.error(f"更新验收文档失败: {str(e)}")

if __name__ == "__main__":
    # 创建测试实例
    test = TestImageAndProduct()
    
    # 运行完整测试
    success = test.run_complete_test()
    
    # 输出测试总结
    if success:
        logger.info("测试完成！请查看测试日志和测试结果文件获取详细信息。")
    else:
        logger.error("测试执行过程中出现错误！")
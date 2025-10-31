import json
import os
import sys
from typing import Dict, Any, Optional, List, Union, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入工具模块
from utils.logger import log_message, get_logger
from utils.exceptions import ValidationError, ConfigError, catch_exceptions
from utils.standardized_interface import ClientInfo, ProductInfo, ValidationResult


class DataLoader:
    """
    数据加载器类，负责从不同来源加载数据
    支持从JSON文件、命令行参数和环境变量加载数据
    集成统一的异常处理和日志记录机制
    """
    
    def __init__(self, config_manager=None):
        """
        初始化数据加载器
        
        :param config_manager: 配置管理器实例，可选
        """
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.logger.info("数据加载器初始化完成")
    
    def load_data_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从JSON文件加载数据
        
        :param file_path: JSON文件路径
        :return: 加载的数据字典
        :raises FileNotFoundError: 当文件不存在时
        :raises ValidationError: 当文件格式错误时
        :raises Exception: 其他加载错误
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"成功从文件加载数据: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"文件格式错误: {file_path}, 错误: {str(e)}")
            raise ValidationError(f"文件格式错误: {file_path}, 错误: {str(e)}")
        except Exception as e:
            self.logger.error(f"加载文件失败: {file_path}, 错误: {str(e)}")
            raise Exception(f"加载文件失败: {file_path}, 错误: {str(e)}")
    
    def load_client_data(self, file_path: Optional[str] = None) -> Union[Dict[str, Any], ClientInfo]:
        """
        加载客户数据
        
        :param file_path: 客户数据文件路径
        :return: 客户数据字典或ClientInfo对象
        :raises ConfigError: 当配置错误时
        :raises ValidationError: 当数据格式错误时
        """
        # 1. 尝试从文件加载
        if file_path:
            return self.load_data_from_file(file_path)
        
        # 2. 尝试从配置中获取文件路径
        if self.config_manager:
            try:
                generation_config = self.config_manager.get_generation_config()
                config_file_path = generation_config.get('client_data_file')
                if config_file_path:
                    return self.load_data_from_file(config_file_path)
            except Exception as e:
                self.logger.error(f"从配置获取客户数据文件路径失败: {str(e)}")
                raise ConfigError(f"从配置获取客户数据文件路径失败: {str(e)}")
        
        # 3. 尝试从环境变量加载JSON字符串
        env_data = os.environ.get('CLIENT_DATA')
        if env_data:
            try:
                data = json.loads(env_data)
                self.logger.info("从环境变量加载客户数据成功")
                return data
            except json.JSONDecodeError as e:
                self.logger.warning(f"环境变量中的客户数据格式错误: {str(e)}")
                raise ValidationError(f"环境变量中的客户数据格式错误: {str(e)}")
        
        # 4. 返回空字典并记录警告
        self.logger.warning("未找到客户数据，返回空字典")
        return {}
    
    @catch_exceptions
    def load_openids_from_file(self, file_path: Optional[str] = None) -> List[str]:
        """
        从文件加载openid列表
        
        :param file_path: openid文件路径
        :return: openid列表
        :raises ConfigError: 当配置错误时
        :raises FileNotFoundError: 当文件不存在时
        :raises Exception: 其他加载错误
        """
        # 1. 尝试从指定文件加载
        if file_path:
            if not os.path.exists(file_path):
                self.logger.error(f"openid文件不存在: {file_path}")
                raise FileNotFoundError(f"openid文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                openids = [line.strip() for line in f if line.strip()]
            self.logger.info(f"成功从文件加载 {len(openids)} 个openid")
            return openids
        
        # 2. 尝试从配置中获取
        if self.config_manager:
            try:
                points_config = self.config_manager.get_points_config()
                # 2.1 尝试从配置文件路径获取
                config_file_path = points_config.get('openids_file')
                if config_file_path:
                    if not os.path.exists(config_file_path):
                        self.logger.error(f"配置中的openid文件不存在: {config_file_path}")
                        raise FileNotFoundError(f"配置中的openid文件不存在: {config_file_path}")
                    
                    with open(config_file_path, 'r', encoding='utf-8') as f:
                        openids = [line.strip() for line in f if line.strip()]
                    self.logger.info(f"从配置指定的文件加载 {len(openids)} 个openid")
                    return openids
                
                # 2.2 尝试从配置中的openids字段获取
                if 'openids' in points_config:
                    openids = points_config['openids']
                    if isinstance(openids, list):
                        self.logger.info(f"从配置加载 {len(openids)} 个openid")
                        return openids
                    else:
                        self.logger.error("配置中的openids字段不是列表类型")
                        raise ValidationError("配置中的openids字段必须是列表类型")
            except Exception as e:
                self.logger.error(f"从配置获取openid失败: {str(e)}")
                if isinstance(e, (FileNotFoundError, ValidationError)):
                    raise
                raise ConfigError(f"从配置获取openid失败: {str(e)}")
        
        self.logger.warning("未找到openid列表，返回空列表")
        return []
    
    @catch_exceptions
    def load_products_from_file(self, file_path: str) -> Union[List[Dict[str, Any]], List[ProductInfo]]:
        """
        从文件加载商品数据
        
        :param file_path: 商品数据文件路径
        :return: 商品列表
        :raises FileNotFoundError: 当文件不存在时
        :raises ValidationError: 当文件格式错误时
        :raises Exception: 其他加载错误
        """
        if not os.path.exists(file_path):
            self.logger.error(f"商品文件不存在: {file_path}")
            raise FileNotFoundError(f"商品文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            # 确保返回的是列表
            if not isinstance(products, list):
                self.logger.error(f"商品文件格式错误，期望列表类型，但得到 {type(products).__name__}")
                raise ValidationError(f"商品文件格式错误，期望列表类型，但得到 {type(products).__name__}")
            
            # 验证每个商品的数据格式
            for i, product in enumerate(products):
                if not isinstance(product, dict):
                    self.logger.error(f"商品 {i} 不是有效的字典格式")
                    raise ValidationError(f"商品 {i} 不是有效的字典格式")
            
            self.logger.info(f"成功从文件加载 {len(products)} 个商品")
            return products
            
        except json.JSONDecodeError as e:
            self.logger.error(f"商品文件格式错误: {file_path}, 错误: {str(e)}")
            raise ValidationError(f"商品文件格式错误: {file_path}, 错误: {str(e)}")
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValidationError)):
                raise
            self.logger.error(f"加载商品文件失败: {file_path}, 错误: {str(e)}")
            raise Exception(f"加载商品文件失败: {file_path}, 错误: {str(e)}")
    
    def validate_client_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证客户数据的有效性
        
        :param data: 客户数据字典
        :return: ValidationResult对象，包含验证结果和详细信息
        """
        errors = []
        
        # 检查数据是否为字典
        if not isinstance(data, dict):
            error_msg = "客户数据必须是字典类型"
            self.logger.error(error_msg)
            errors.append(error_msg)
            return ValidationResult(is_valid=False, errors=errors)
        
        # 必需字段
        required_fields = ['course_name', 'teacher_info', 'course_content', 'target_audience', 'learning_outcomes']
        
        # 检查必需字段
        for field in required_fields:
            if field not in data:
                error_msg = f"客户数据缺少必需字段: {field}"
                self.logger.error(error_msg)
                errors.append(error_msg)
            elif not data[field]:
                error_msg = f"客户数据字段 '{field}' 值为空"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        # 检查teacher_info字段结构
        if 'teacher_info' in data and data['teacher_info']:
            if not isinstance(data.get('teacher_info'), dict):
                error_msg = "客户数据中teacher_info必须是字典类型"
                self.logger.error(error_msg)
                errors.append(error_msg)
            else:
                # teacher_info必需字段
                teacher_required_fields = ['name', 'title', 'experience', 'background']
                for field in teacher_required_fields:
                    if field not in data['teacher_info']:
                        error_msg = f"客户数据中teacher_info缺少必需字段: {field}"
                        self.logger.error(error_msg)
                        errors.append(error_msg)
                    elif not data['teacher_info'][field]:
                        error_msg = f"客户数据中teacher_info字段 '{field}' 值为空"
                        self.logger.error(error_msg)
                        errors.append(error_msg)
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        else:
            self.logger.info("客户数据验证通过")
            return ValidationResult(is_valid=True, message="客户数据验证通过")
    
    @catch_exceptions
    def save_data_to_file(self, data: Any, file_path: str) -> bool:
        """
        保存数据到JSON文件
        
        :param data: 要保存的数据
        :param file_path: 文件路径
        :return: 是否成功
        :raises IOError: 当文件写入失败时
        :raises Exception: 其他保存错误
        """
        try:
            # 验证文件路径
            if not file_path:
                self.logger.error("文件路径不能为空")
                raise ValueError("文件路径不能为空")
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                self.logger.debug(f"确保目录存在: {dir_path}")
            
            # 验证数据可序列化
            try:
                json.dumps(data, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                self.logger.error(f"数据不可JSON序列化: {str(e)}")
                raise ValidationError(f"数据不可JSON序列化: {str(e)}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"成功保存数据到文件: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {file_path}, 错误: {str(e)}")
            if isinstance(e, (ValueError, ValidationError)):
                raise
            raise IOError(f"保存数据失败: {file_path}, 错误: {str(e)}")


def load_products_from_file(file_path: str) -> Union[List[Dict[str, Any]], List[ProductInfo]]:
    """
    从文件加载商品数据的便捷函数
    
    :param file_path: 商品数据文件路径
    :return: 商品列表
    :raises Exception: 加载过程中的异常
    """
    loader = DataLoader()
    return loader.load_products_from_file(file_path)


@catch_exceptions
def load_openids_from_file(file_path: Optional[str] = None) -> List[str]:
    """
    从文件加载openid列表的便捷函数
    
    :param file_path: openid文件路径
    :return: openid列表
    :raises Exception: 加载过程中的异常
    """
    loader = DataLoader()
    return loader.load_openids_from_file(file_path)


def load_client_data(file_path: Optional[str] = None) -> Union[Dict[str, Any], ClientInfo]:
    """
    加载客户数据的便捷函数
    
    :param file_path: 客户数据文件路径
    :return: 客户数据字典或ClientInfo对象
    :raises Exception: 加载过程中的异常
    """
    loader = DataLoader()
    return loader.load_client_data(file_path)


def validate_client_data(data: Dict[str, Any]) -> ValidationResult:
    """
    验证客户数据的便捷函数
    
    :param data: 客户数据字典
    :return: ValidationResult对象
    :raises Exception: 验证过程中的异常
    """
    loader = DataLoader()
    return loader.validate_client_data(data)


if __name__ == "__main__":
    # 测试数据加载器
    logger = get_logger("data_loader_test")
    logger.info("开始测试数据加载器")
    
    loader = DataLoader()
    
    # 测试加载客户数据示例
    sample_client_data = {
        'course_name': 'Python数据分析实战',
        'teacher_info': {
            'name': '张老师',
            'title': '数据科学专家',
            'experience': '10年数据分析和教学经验',
            'background': '统计学硕士'
        },
        'course_content': '本课程讲解Python数据分析技能...',
        'target_audience': '希望转行数据分析的职场人士',
        'learning_outcomes': '掌握Python数据分析核心技能'
    }
    
    # 验证示例数据
    validation_result = loader.validate_client_data(sample_client_data)
    logger.info(f"示例数据验证结果: {validation_result.is_valid}")
    if not validation_result.is_valid:
        for error in validation_result.errors:
            logger.error(f"验证错误: {error}")
    
    logger.info("数据加载器测试完成")
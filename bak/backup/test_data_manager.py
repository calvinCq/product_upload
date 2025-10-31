import os
import json
import copy
from datetime import datetime

# 测试数据目录
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')

# 确保测试数据目录存在
def ensure_test_data_dir():
    """
    确保测试数据目录存在，如果不存在则创建
    """
    if not os.path.exists(TEST_DATA_DIR):
        os.makedirs(TEST_DATA_DIR)
        print(f"创建测试数据目录: {TEST_DATA_DIR}")

# 加载测试数据
def load_test_data(filename, env='default'):
    """
    加载测试数据文件
    :param filename: 文件名（不含路径）
    :param env: 环境标识（如 'dev', 'test', 'prod'）
    :return: 测试数据字典
    """
    ensure_test_data_dir()
    
    # 环境特定的数据文件
    if env != 'default':
        env_filename = f"{filename}_{env}.json"
        env_file_path = os.path.join(TEST_DATA_DIR, env_filename)
        if os.path.exists(env_file_path):
            print(f"加载环境特定测试数据: {env_filename}")
            return _load_json_file(env_file_path)
    
    # 默认数据文件
    default_file_path = os.path.join(TEST_DATA_DIR, f"{filename}.json")
    if os.path.exists(default_file_path):
        print(f"加载默认测试数据: {filename}.json")
        return _load_json_file(default_file_path)
    
    print(f"测试数据文件不存在: {filename}.json")
    return None

# 保存测试数据
def save_test_data(filename, data, env=None):
    """
    保存测试数据到文件
    :param filename: 文件名（不含路径）
    :param data: 要保存的数据
    :param env: 环境标识（可选）
    :return: 是否保存成功
    """
    ensure_test_data_dir()
    
    # 构建文件名
    if env and env != 'default':
        filename = f"{filename}_{env}"
    
    # 添加时间戳信息
    save_data = copy.deepcopy(data)
    if isinstance(save_data, dict):
        save_data['_meta'] = {
            'saved_at': datetime.now().isoformat(),
            'environment': env or 'default'
        }
    
    # 保存文件
    file_path = os.path.join(TEST_DATA_DIR, f"{filename}.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        print(f"测试数据已保存到: {file_path}")
        return True
    except Exception as e:
        print(f"保存测试数据失败: {str(e)}")
        return False

# 创建默认商品测试数据
def create_default_product_data():
    """
    创建默认的商品测试数据
    :return: 商品数据字典
    """
    return {
        "title": f"测试商品 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "desc": "这是一个测试商品，用于API测试。",
        "head_img": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg"
        ],
        "detail_img": [
            "https://example.com/detail1.jpg",
            "https://example.com/detail2.jpg"
        ],
        "category_id1": 6706,  # 电脑、办公
        "category_id2": 6733,  # 外设产品
        "category_id3": 6741,  # 电脑工具
        "sku_list": [
            {
                "price": 10000,  # 100元（分）
                "original_price": 12000,  # 120元（分）
                "stock": 100,
                "sku_code": "test-sku-001"
            }
        ],
        "freight_type": 0,  # 0: 统一运费
        "freight": 1000  # 10元（分）
    }

# 生成测试结果记录
def create_test_result_record(test_name, success, data=None, error=None):
    """
    创建测试结果记录
    :param test_name: 测试名称
    :param success: 是否成功
    :param data: 成功时的数据（可选）
    :param error: 失败时的错误信息（可选）
    :return: 测试结果记录字典
    """
    return {
        "test_name": test_name,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "data": data,
        "error": error
    }

# 保存测试结果
def save_test_result(result_data):
    """
    保存测试结果
    :param result_data: 测试结果数据
    :return: 是否保存成功
    """
    ensure_test_data_dir()
    
    # 测试结果文件路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(TEST_DATA_DIR, f"test_result_{timestamp}.json")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"测试结果已保存到: {file_path}")
        return True
    except Exception as e:
        print(f"保存测试结果失败: {str(e)}")
        return False

# 内部辅助函数：加载JSON文件
def _load_json_file(file_path):
    """
    加载JSON文件的内部辅助函数
    :param file_path: 文件路径
    :return: 解析后的数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON文件失败 {file_path}: {str(e)}")
        return None

# 初始化测试数据
def initialize_test_data():
    """
    初始化测试数据，创建默认测试数据文件
    """
    ensure_test_data_dir()
    
    # 创建默认商品数据文件
    default_product_data = create_default_product_data()
    save_test_data('default_product', default_product_data)
    
    print("测试数据初始化完成")

# 如果直接运行此模块，则初始化测试数据
if __name__ == "__main__":
    initialize_test_data()
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.wechat_shop_api import WeChatShopAPIClient
from src.utils.logger import log_message

def test_api_connection():
    """
    测试微信小店API连接
    """
    try:
        # 初始化API客户端
        log_message("初始化微信小店API客户端")
        api_client = WeChatShopAPIClient()
        
        # 测试获取access_token
        log_message("尝试获取access_token")
        token_result = api_client.get_access_token()
        
        if token_result:
            log_message(f"获取access_token成功: {token_result}", "INFO")
            log_message("API连接测试通过！", "SUCCESS")
        else:
            log_message("获取access_token失败", "ERROR")
            log_message("API连接测试失败！", "ERROR")
            
    except Exception as e:
        log_message(f"测试过程中发生异常: {str(e)}", "ERROR")

if __name__ == "__main__":
    log_message("===== 开始测试微信小店API连接 =====")
    test_api_connection()
    log_message("===== 测试结束 =====")
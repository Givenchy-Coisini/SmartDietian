# app/common/logger.py
import logging
import sys
# 配置日志格式：时间 - 级别 - 模块 - 消息
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def setup_logging():
    """配置日志记录"""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

# 创建一个全局的 logger 实例
logger = logging.getLogger("smart_dietian")

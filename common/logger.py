import logging
import os
from datetime import datetime

def init_logger(log_dir: str = "./logs") -> logging.Logger:
    """初始化日志配置：同时输出到控制台和文件"""
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"extractor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # 日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 配置日志器
    logger = logging.getLogger("SensitiveDataExtractor")
    logger.setLevel(logging.INFO)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(file_handler)

    return logger

# 初始化全局日志器
logger = init_logger()
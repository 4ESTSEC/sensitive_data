import os
import sys
from common.logger import logger
from common.exception_handler import ProxyError

def set_proxy(proxy: str) -> None:
    """设置全局代理（支持 HTTP/SOCKS5）"""
    if not proxy:
        logger.info("未配置代理，使用默认网络")
        return

    try:
        # 验证代理格式
        if not (proxy.startswith("http://") or proxy.startswith("socks5://")):
            raise ProxyError(proxy, "代理格式错误，需为 http://ip:port 或 socks5://ip:port")

        # 设置环境变量（部分数据库驱动会读取环境变量代理）
        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy
        os.environ["ALL_PROXY"] = proxy

        logger.info(f"已配置代理：{proxy}")
    except ProxyError:
        raise
    except Exception as e:
        raise ProxyError(proxy, str(e)) from e

def clear_proxy() -> None:
    """清除代理配置"""
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]:
        if key in os.environ:
            del os.environ[key]
    logger.info("已清除代理配置")
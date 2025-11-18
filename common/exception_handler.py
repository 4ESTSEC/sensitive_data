from common.logger import logger

class BaseExtractorError(Exception):
    """基础异常类"""
    pass

class DBConnectionError(BaseExtractorError):
    """数据库连接异常"""
    def __init__(self, db_type: str, msg: str):
        self.db_type = db_type
        self.msg = msg
        super().__init__(f"[{db_type}] 连接失败：{msg}")
        logger.error(self.__str__())

class DBQueryError(BaseExtractorError):
    """数据库查询异常"""
    def __init__(self, db_name: str, table_name: str, msg: str):
        self.db_name = db_name
        self.table_name = table_name
        self.msg = msg
        super().__init__(f"[{db_name}.{table_name}] 查询失败：{msg}")
        logger.error(self.__str__())

class ProxyError(BaseExtractorError):
    """代理配置异常"""
    def __init__(self, proxy: str, msg: str):
        self.proxy = proxy
        self.msg = msg
        super().__init__(f"代理配置失败（{proxy}）：{msg}")
        logger.error(self.__str__())

class ExportError(BaseExtractorError):
    """导出异常"""
    def __init__(self, export_type: str, msg: str):
        self.export_type = export_type
        self.msg = msg
        super().__init__(f"[{export_type}] 导出失败：{msg}")
        logger.error(self.__str__())
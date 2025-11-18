from typing import List, Dict, Tuple
from abc import ABCMeta, abstractmethod
from config.sensitive_keywords import SENSITIVE_FIELD_KEYWORDS

class BaseDatabase(metaclass=ABCMeta):
    def __init__(self, host: str, port: int, user: str, password: str, timeout: int, extract_rows: int):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        self.extract_rows = extract_rows
        self.connection = None
        self.cursor = None

    @abstractmethod
    def connect(self) -> bool:
        """连接数据库，返回是否成功"""
        pass

    @abstractmethod
    def list_databases(self) -> List[str]:
        """获取所有非系统数据库"""
        pass

    @abstractmethod
    def list_tables(self, db_name: str) -> List[str]:
        """获取指定数据库下的所有表"""
        pass

    @abstractmethod
    def list_columns(self, db_name: str, table_name: str) -> List[Dict]:
        """获取表的字段信息（含敏感字段标记）"""
        pass

    @abstractmethod
    def query_top_rows(self, db_name: str, table_name: str) -> List[Dict]:
        """查询表的前 N 行数据（所有字段）"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开数据库连接"""
        pass

    def is_sensitive_column(self, column_name: str, column_comment: str = "") -> Tuple[bool, str]:
        """判断字段是否为敏感字段（所有数据库通用逻辑）"""
        column_info = (column_name + " " + (column_comment or "")).lower()
        for sensitive_type, keywords in SENSITIVE_FIELD_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in column_info:
                    return True, sensitive_type
        return False, ""
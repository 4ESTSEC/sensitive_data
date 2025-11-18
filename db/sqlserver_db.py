import pyodbc
from typing import List, Dict
from db.base_db import BaseDatabase
from config.default_config import SYSTEM_DATABASES
from common.logger import logger
from common.exception_handler import DBConnectionError, DBQueryError

class SQLServerDatabase(BaseDatabase):
    def __init__(self, host: str, port: int, user: str, password: str, timeout: int, extract_rows: int):
        super().__init__(host, port, user, password, timeout, extract_rows)
        # 获取可用的SQL Server ODBC驱动
        self.driver = self._get_available_driver()
        if not self.driver:
            raise DBConnectionError("sqlserver", "未找到可用的SQL Server ODBC驱动")
        
        # SQL Server 连接字符串模板
        self.conn_str = (
            r"DRIVER={{{driver}}};"
            r"SERVER={host},{port};"
            r"DATABASE=master;"
            r"UID={user};"
            r"PWD={password};"
            r"Timeout={timeout};"
            r"TrustServerCertificate=yes;"
            r"Encrypt=no;"
        )
    
    def _get_available_driver(self):
        """获取可用的SQL Server ODBC驱动"""
        try:
            # 列出所有可用的ODBC驱动
            drivers = [driver for driver in pyodbc.drivers() if "SQL Server" in driver]
            logger.info(f"可用的SQL Server ODBC驱动: {drivers}")
            
            # 优先使用更新的驱动版本
            for version in [18, 17, 13, 11]:
                for driver in drivers:
                    if f"{version}" in driver:
                        return driver
            
            # 如果有任何SQL Server驱动，返回第一个
            if drivers:
                return drivers[0]
            return None
        except Exception as e:
            logger.error(f"获取ODBC驱动列表失败: {str(e)}")
            return None

    def connect(self) -> bool:
        """SQL Server 连接实现"""
        try:
            # 填充连接参数
            conn_str = self.conn_str.format(
                driver=self.driver,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                timeout=self.timeout
            )
            self.connection = pyodbc.connect(conn_str)
            self.cursor = self.connection.cursor()
            logger.info(f"SQL Server 连接成功：{self.host}:{self.port}（用户：{self.user}，驱动：{self.driver}）")
            return True
        except Exception as e:
            raise DBConnectionError("sqlserver", str(e)) from e

    def list_databases(self) -> List[str]:
        """获取 SQL Server 非系统数据库"""
        try:
            # 查询所有数据库
            self.cursor.execute("SELECT name FROM sys.databases;")
            all_dbs = [row[0] for row in self.cursor.fetchall()]
            # 排除系统库
            system_dbs = SYSTEM_DATABASES.get("sqlserver", [])
            return [db for db in all_dbs if db not in system_dbs]
        except Exception as e:
            raise DBQueryError("system", "show_databases", str(e)) from e

    def list_tables(self, db_name: str) -> List[str]:
        """获取指定数据库下的表"""
        try:
            # 切换数据库
            self.cursor.execute(f"USE [{db_name}];")
            # 查询用户表（排除系统表）
            self.cursor.execute("""
                SELECT name FROM sys.tables 
                WHERE type = 'U'  -- U = User Table（用户表）
                ORDER BY name;
            """)
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            raise DBQueryError(db_name, "show_tables", str(e)) from e

    def list_columns(self, db_name: str, table_name: str) -> List[Dict]:
        """获取表字段信息（含敏感字段标记）"""
        try:
            self.cursor.execute(f"USE [{db_name}];")
            # 查询字段信息（名称、类型、注释、是否允许为空）
            self.cursor.execute(f"""
                SELECT 
                    col.name AS column_name,
                    t.name AS column_type,
                    col.is_nullable,
                    ISNULL(ep.value, '') AS column_comment
                FROM 
                    sys.columns col
                JOIN 
                    sys.types t ON col.system_type_id = t.system_type_id
                LEFT JOIN 
                    sys.extended_properties ep 
                    ON col.object_id = ep.major_id 
                    AND col.column_id = ep.minor_id 
                    AND ep.name = 'MS_Description'
                WHERE 
                    col.object_id = OBJECT_ID('[{table_name}]')
                ORDER BY 
                    col.column_id;
            """)

            columns = self.cursor.fetchall()
            result = []
            for col in columns:
                column_name = col.column_name
                is_sensitive, sensitive_type = self.is_sensitive_column(
                    column_name, col.column_comment
                )
                result.append({
                    "column_name": column_name,
                    "column_type": col.column_type,
                    "is_nullable": col.is_nullable == 1,
                    "column_comment": col.column_comment,
                    "is_sensitive": is_sensitive,
                    "sensitive_type": sensitive_type
                })
            return result
        except Exception as e:
            raise DBQueryError(db_name, table_name, f"获取字段信息失败：{str(e)}") from e

    def query_top_rows(self, db_name: str, table_name: str) -> List[Dict]:
        """查询表前 N 行数据（所有字段）"""
        try:
            self.cursor.execute(f"USE [{db_name}];")
            # 查询前 N 行，转换为字典格式（键为字段名）
            self.cursor.execute(f"SELECT TOP {self.extract_rows} * FROM [{table_name}];")
            
            # 获取字段名列表
            columns = [column[0] for column in self.cursor.description]
            # 转换行数据为字典
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            raise DBQueryError(db_name, table_name, f"查询数据失败：{str(e)}") from e

    def disconnect(self) -> None:
        """断开 SQL Server 连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("SQL Server 连接已断开")
        except Exception as e:
            logger.error(f"断开 SQL Server 连接失败：{str(e)}")
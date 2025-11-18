import pymysql
from typing import List, Dict
from db.base_db import BaseDatabase
from config.default_config import SYSTEM_DATABASES
from common.logger import logger
from common.exception_handler import DBConnectionError, DBQueryError

class MySQLDatabase(BaseDatabase):
    def __init__(self, host: str, port: int, user: str, password: str, timeout: int, extract_rows: int, charset: str = "utf8mb4"):
        super().__init__(host, port, user, password, timeout, extract_rows)
        self.charset = charset

    def connect(self) -> bool:
        """MySQL 连接实现"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset=self.charset,
                connect_timeout=self.timeout,
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            logger.info(f"MySQL 连接成功：{self.host}:{self.port}（用户：{self.user}）")
            return True
        except Exception as e:
            raise DBConnectionError("mysql", str(e)) from e

    def list_databases(self) -> List[str]:
        """获取 MySQL 非系统数据库"""
        try:
            self.cursor.execute("SHOW DATABASES;")
            all_dbs = [item["Database"] for item in self.cursor.fetchall()]
            # 排除系统库
            system_dbs = SYSTEM_DATABASES.get("mysql", [])
            return [db for db in all_dbs if db not in system_dbs]
        except Exception as e:
            raise DBQueryError("system", "show_databases", str(e)) from e

    def list_tables(self, db_name: str) -> List[str]:
        """获取指定数据库下的表"""
        try:
            self.cursor.execute(f"USE `{db_name}`;")
            self.cursor.execute("SHOW TABLES;")
            return [list(item.values())[0] for item in self.cursor.fetchall()]
        except Exception as e:
            raise DBQueryError(db_name, "show_tables", str(e)) from e

    def list_columns(self, db_name: str, table_name: str) -> List[Dict]:
        """获取表字段信息（含敏感字段标记）"""
        try:
            self.cursor.execute(f"USE `{db_name}`;")
            # 获取字段基本信息（类型、是否为空等）
            self.cursor.execute(f"DESCRIBE `{table_name}`;")
            columns = self.cursor.fetchall()

            # 获取字段注释
            self.cursor.execute(f"""
                SELECT COLUMN_NAME, COLUMN_COMMENT 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s;
            """, (db_name, table_name))
            comments = {item["COLUMN_NAME"]: item["COLUMN_COMMENT"] for item in self.cursor.fetchall()}

            # 整理字段信息，添加敏感字段标记
            result = []
            for col in columns:
                field_name = col["Field"]
                is_sensitive, sensitive_type = self.is_sensitive_column(
                    field_name, comments.get(field_name, "")
                )
                result.append({
                    "column_name": field_name,
                    "column_type": col["Type"],
                    "is_nullable": col["Null"] == "YES",
                    "column_comment": comments.get(field_name, ""),
                    "is_sensitive": is_sensitive,
                    "sensitive_type": sensitive_type
                })
            return result
        except Exception as e:
            raise DBQueryError(db_name, table_name, f"获取字段信息失败：{str(e)}") from e

    def query_top_rows(self, db_name: str, table_name: str) -> List[Dict]:
        """查询表前 N 行数据（所有字段）"""
        try:
            self.cursor.execute(f"USE `{db_name}`;")
            self.cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {self.extract_rows};")
            return self.cursor.fetchall()
        except Exception as e:
            raise DBQueryError(db_name, table_name, f"查询数据失败：{str(e)}") from e

    def disconnect(self) -> None:
        """断开 MySQL 连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("MySQL 连接已断开")
        except Exception as e:
            logger.error(f"断开 MySQL 连接失败：{str(e)}")
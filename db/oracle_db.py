import oracledb
from typing import List, Dict
from db.base_db import BaseDatabase
from config.default_config import SYSTEM_DATABASES
from common.logger import logger
from common.exception_handler import DBConnectionError, DBQueryError

class OracleDatabase(BaseDatabase):
    def __init__(self, host: str, port: int, user: str, password: str, timeout: int, extract_rows: int, service_name: str = None):
        super().__init__(host, port, user, password, timeout, extract_rows)
        # Oracle 连接配置
        # 如果没有提供service_name，默认使用ORCL
        service_name = service_name or "ORCL"
        self.dsn = f"{host}:{port}/{service_name}"  # 使用指定的服务名或默认服务名
        # 设置超时时间
        self.connection_params = {
            'user': user,
            'password': password,
            'dsn': self.dsn,
        }

    def connect(self) -> bool:
        """Oracle 连接实现"""
        try:
            # 连接 Oracle 数据库
            self.connection = oracledb.connect(**self.connection_params)
            self.cursor = self.connection.cursor()
            logger.info(f"Oracle 连接成功：{self.host}:{self.port}（用户：{self.user}）")
            return True
        except Exception as e:
            raise DBConnectionError("oracle", str(e)) from e

    def list_databases(self) -> List[str]:
        """获取 Oracle 非系统用户（Oracle 没有真正的数据库概念，这里返回用户列表）"""
        try:
            # 查询所有用户（排除系统用户）
            # 使用all_users代替dba_users，普通用户也能访问
            self.cursor.execute("""
                SELECT username 
                FROM all_users
                ORDER BY username
            """)
            all_users = [row[0] for row in self.cursor.fetchall()]
            
            # 排除系统用户
            system_users = SYSTEM_DATABASES.get("oracle", [])
            return [user for user in all_users if user not in system_users]
        except Exception as e:
            raise DBQueryError("system", "show_databases", str(e)) from e

    def list_tables(self, db_name: str) -> List[str]:
        """获取指定用户下的表（在 Oracle 中，db_name 实际上是用户名）"""
        try:
            # 查询指定用户下的表
            self.cursor.execute("""
                SELECT table_name 
                FROM all_tables 
                WHERE owner = :owner
                ORDER BY table_name
            """, owner=db_name)
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            raise DBQueryError(db_name, "show_tables", str(e)) from e

    def list_columns(self, db_name: str, table_name: str) -> List[Dict]:
        """获取表字段信息（含敏感字段标记）"""
        try:
            # 查询字段信息（名称、类型、注释、是否允许为空）
            self.cursor.execute("""
                SELECT 
                    column_name, 
                    data_type, 
                    nullable,
                    (SELECT comments 
                     FROM all_col_comments 
                     WHERE owner = :owner 
                     AND table_name = :table_name 
                     AND column_name = cols.column_name)
                FROM all_tab_columns cols
                WHERE owner = :owner 
                AND table_name = :table_name
                ORDER BY column_id
            """, owner=db_name, table_name=table_name)

            columns = self.cursor.fetchall()
            result = []
            for col in columns:
                column_name = col[0]
                column_comment = col[3] or ""
                is_sensitive, sensitive_type = self.is_sensitive_column(
                    column_name, column_comment
                )
                result.append({
                    "column_name": column_name,
                    "column_type": col[1],
                    "is_nullable": col[2] == 'Y',
                    "column_comment": column_comment,
                    "is_sensitive": is_sensitive,
                    "sensitive_type": sensitive_type
                })
            return result
        except Exception as e:
            raise DBQueryError(db_name, table_name, f"获取字段信息失败：{str(e)}") from e

    def query_top_rows(self, db_name: str, table_name: str) -> List[Dict]:
        """查询表前 N 行数据（所有字段）"""
        try:
            # 查询前 N 行，转换为字典格式（键为字段名）
            full_table_name = f"{db_name}.{table_name}"
            self.cursor.execute(f"""
                SELECT * FROM {full_table_name} 
                WHERE ROWNUM <= :limit
            """, limit=self.extract_rows)
            
            # 获取字段名列表
            columns = [column[0] for column in self.cursor.description]
            # 转换行数据为字典
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            raise DBQueryError(db_name, table_name, f"查询数据失败：{str(e)}") from e

    def disconnect(self) -> None:
        """断开 Oracle 连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("Oracle 连接已断开")
        except Exception as e:
            logger.error(f"断开 Oracle 连接失败：{str(e)}")
import os
import argparse
import time
import sys
from dotenv import load_dotenv
from typing import Dict, Optional
from config.default_config import DB_DEFAULT_CONFIG, COMMON_CONFIG
from db.base_db import BaseDatabase  # 新增：导入基类
from db.mysql_db import MySQLDatabase
from common.logger import logger
from common.proxy_handler import set_proxy, clear_proxy
from common.exporter import ResultExporter
from common.exception_handler import BaseExtractorError

def parse_args() -> argparse.Namespace:
    """解析命令行参数（修复 -h 冲突，改用 -H 作为 --host 缩写）"""
    parser = argparse.ArgumentParser(description="敏感数据提取工具（支持 MySQL/SQL Server/Oracle）")

    # 数据库核心参数：--host 缩写改为 -H（避免与帮助参数 -h 冲突）
    parser.add_argument("-t", "--db-type", type=str, default="mysql",
                        choices=["mysql", "sqlserver", "oracle"], help="数据库类型（默认：mysql）")
    parser.add_argument("-H", "--host", type=str, help="数据库IP/主机名（默认：127.0.0.1）")  # 关键修改：-h → -H
    parser.add_argument("-P", "--port", type=int, help="数据库端口（默认：mysql=3306，sqlserver=1433，oracle=1521）")
    parser.add_argument("-u", "--user", type=str, help="数据库用户名（默认：mysql=root，sqlserver=sa，oracle=system）")
    parser.add_argument("-pwd", "--password", type=str, help="数据库密码（默认：空）")
    parser.add_argument("-s", "--service-name", type=str, help="Oracle服务名（默认：ORCL）")

    # 扩展参数
    parser.add_argument("-px", "--proxy", type=str, help="代理地址（格式：http://ip:port 或 socks5://ip:port）")
    parser.add_argument("-to", "--timeout", type=int, help="连接超时时间（秒，默认：10）")
    parser.add_argument("-r", "--extract-rows", type=int, help="提取表数据行数（默认：5）")
    parser.add_argument("-e", "--export-type", type=str, default="all",
                        choices=["csv", "json", "all"], help="导出格式（默认：all）")
    parser.add_argument("-o", "--output-dir", type=str, help="导出文件目录（默认：./output）")

    return parser.parse_args()

def load_config(args: argparse.Namespace) -> Dict:
    """加载配置：命令行参数 > 环境变量 > 默认配置"""
    load_dotenv()  # 加载 .env 文件
    db_type = args.db_type
    config = {
        "db_type": db_type,
        "host": args.host or os.getenv("DB_HOST") or DB_DEFAULT_CONFIG[db_type]["host"],
        "port": args.port or int(os.getenv("DB_PORT", DB_DEFAULT_CONFIG[db_type]["port"])),
        "user": args.user or os.getenv("DB_USER") or DB_DEFAULT_CONFIG[db_type]["user"],
        "password": args.password or os.getenv("DB_PASSWORD") or DB_DEFAULT_CONFIG[db_type]["password"],
        "timeout": args.timeout or int(os.getenv("TIMEOUT", COMMON_CONFIG["timeout"])),
        "extract_rows": args.extract_rows or int(os.getenv("EXTRACT_ROWS", COMMON_CONFIG["extract_rows"])),
        "export_type": args.export_type or os.getenv("EXPORT_TYPE", COMMON_CONFIG["export_type"]),
        "output_dir": args.output_dir or os.getenv("OUTPUT_DIR", COMMON_CONFIG["output_dir"]),
        "proxy": args.proxy or os.getenv("PROXY") or COMMON_CONFIG["proxy"]
    }
    
    # Oracle 额外配置
    if db_type == "oracle":
        config["service_name"] = args.service_name or os.getenv("DB_SERVICE_NAME") or "ORCL"

    # MySQL 额外配置
    if db_type == "mysql":
        config["charset"] = os.getenv("DB_CHARSET") or DB_DEFAULT_CONFIG[db_type]["charset"]

    logger.info("=" * 50)
    logger.info("当前配置：")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")
    logger.info("=" * 50)
    return config

def create_db_instance(config: Dict) -> Optional[BaseDatabase]:
    """创建数据库实例（支持 MySQL + SQL Server + Oracle）"""
    db_type = config["db_type"]
    try:
        if db_type == "mysql":
            return MySQLDatabase(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                timeout=config["timeout"],
                extract_rows=config["extract_rows"],
                charset=config["charset"]
            )
        elif db_type == "sqlserver":  # 新增 SQL Server 支持
            from db.sqlserver_db import SQLServerDatabase
            return SQLServerDatabase(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                timeout=config["timeout"],
                extract_rows=config["extract_rows"]
            )
        elif db_type == "oracle":  # 新增 Oracle 支持
            from db.oracle_db import OracleDatabase
            return OracleDatabase(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                timeout=config["timeout"],
                extract_rows=config["extract_rows"],
                service_name=config.get("service_name")
            )
        else:
            logger.error(f"暂未支持 {db_type} 数据库，当前支持：mysql/sqlserver/oracle")
            return None
    except Exception as e:
        logger.error(f"创建数据库实例失败：{str(e)}")
        return None

def main():
    start_time = time.time()
    
    # 关键修改：初始化变量
    db_instance: Optional[BaseDatabase] = None
    proxy_set = False  # 标记是否设置了代理
    
    try:
        # 1. 解析参数
        args = parse_args()
        
        # 2. 只有在实际执行任务时才显示任务开始日志，帮助模式不显示
        # 注意：args已经通过parse_args()成功返回，说明不是帮助模式
        logger.info("=" * 50)
        logger.info("开始执行敏感数据提取任务")
        logger.info("=" * 50)
        
        # 3. 加载配置
        config = load_config(args)

        # 2. 配置代理
        if config["proxy"]:
            set_proxy(config["proxy"])
            proxy_set = True

        # 3. 创建数据库实例 + 连接
        db_instance = create_db_instance(config)
        if not db_instance or not db_instance.connect():
            raise BaseExtractorError("数据库连接失败，任务终止")

        # 4. 提取敏感数据
        sensitive_results = []
        databases = db_instance.list_databases()
        logger.info(f"\n共发现 {len(databases)} 个非系统数据库")

        for db_name in databases:
            logger.info(f"\n--- 开始处理数据库：{db_name} ---")
            tables = db_instance.list_tables(db_name)
            logger.info(f"数据库 {db_name} 包含 {len(tables)} 个表")

            for table_name in tables:
                # 获取字段信息，判断是否含敏感字段
                columns = db_instance.list_columns(db_name, table_name)
                sensitive_cols = [col for col in columns if col["is_sensitive"]]
                if not sensitive_cols:
                    logger.info(f"  表 {table_name}：无敏感字段，跳过")
                    continue

                # 提取表数据
                logger.info(f"  表 {table_name}：发现 {len(sensitive_cols)} 个敏感字段 → 提取前 {config['extract_rows']} 行数据")
                rows = db_instance.query_top_rows(db_name, table_name)

                # 整理结果
                sensitive_results.append({
                    "数据库类型": config["db_type"],
                    "数据库名": db_name,
                    "表名": table_name,
                    "敏感字段数": len(sensitive_cols),
                    "敏感字段列表": [col["column_name"] for col in sensitive_cols],
                    "敏感字段详情": columns,
                    "提取数据行数": len(rows),
                    "提取时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "rows": rows
                })

        # 5. 导出结果
        logger.info("\n" + "=" * 50)
        logger.info(f"数据提取完成！共发现 {len(sensitive_results)} 个含敏感数据的表")
        logger.info("=" * 50)

        if sensitive_results:
            # 控制台打印摘要
            for idx, result in enumerate(sensitive_results, 1):
                logger.info(f"\n{idx}. 数据库：{result['数据库名']} → 表：{result['表名']}")
                logger.info(f"   敏感字段：{result['敏感字段列表']}")
                logger.info(f"   提取数据：{result['提取数据行数']} 行")

            # 导出文件
            exporter = ResultExporter(config["output_dir"])
            exporter.export(sensitive_results, config["export_type"])
        else:
            logger.info("\n未发现任何含敏感数据的表")

        # 6. 统计耗时
        end_time = time.time()
        logger.info(f"\n任务总耗时：{end_time - start_time:.2f} 秒")

    except BaseExtractorError as e:
        logger.error(f"\n任务执行失败：{str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n任务执行异常：{str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # 清理资源（db_instance 已初始化，不会报错）
        if db_instance:
            db_instance.disconnect()
        
        # 只在实际设置了代理时才清理代理
        if proxy_set:
            clear_proxy()
            logger.info("已清除代理配置")
            
        # 简化判断逻辑，只有在正常执行过程中(非-h帮助模式)才显示结束日志
        # 避免访问可能未定义的args变量
        try:
            # 检查是否有异常或是否正常执行完毕
            # 如果args已定义且不是帮助模式，显示结束日志
            if 'args' in locals() and args:
                logger.info("\n任务结束，资源已清理")
        except:
            # 静默处理任何异常，确保程序能够正常退出
            pass

if __name__ == "__main__":
    main()
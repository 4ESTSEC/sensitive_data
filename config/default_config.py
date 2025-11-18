# 数据库默认配置（按类型区分）
DB_DEFAULT_CONFIG = {
    "mysql": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "",
        "charset": "utf8mb4"
    },
    "sqlserver": {
        "host": "127.0.0.1",
        "port": 1433,
        "user": "sa",
        "password": ""
    },
    "oracle": {
        "host": "127.0.0.1",
        "port": 1521,
        "user": "system",
        "password": "oracle"
    }
}

# 通用默认配置
COMMON_CONFIG = {
    "extract_rows": 5,          # 默认提取行数
    "timeout": 10,              # 连接超时时间（秒）
    "export_type": "all",       # 默认导出格式（csv/json/all）
    "output_dir": "./output",   # 默认导出目录
    "proxy": None               # 默认不使用代理
}

# 系统数据库排除列表（避免扫描系统库）
SYSTEM_DATABASES = {
    "mysql": ["information_schema", "mysql", "performance_schema", "sys"],
    "sqlserver": ["master", "model", "msdb", "tempdb"],
    "oracle": [
        # 核心系统用户
        "SYS", "SYSTEM", "SYSMAN", "DBSNMP", "OUTLN", "SCOTT", 
        # 数据和存储相关用户
        "ORDSYS", "MDSYS", "OLAPSYS", "XDB", "WMSYS", "MDDATA", 
        # 安全相关用户
        "APPQOSSYS", "AUDSYS", "CTXSYS", "DBSFWUSER", "DVF", "DVSYS", 
        "LBACSYS", "SYSBACKUP", "SYSDG", "SYSKM", "SYSRAC", "XS$NULL", 
        # 复制和网格用户
        "GGSYS", "GSMADMIN_INTERNAL", "GSMCATUSER", "GSMROOTUSER", "GSMUSER", 
        # 其他系统用户
        "ANONYMOUS", "DIP", "OJVMSYS", "ORACLE_OCM", "ORDDATA", 
        "ORDPLUGINS", "PDBADMIN", "REMOTE_SCHEDULER_AGENT", "SI_INFORMTN_SCHEMA", 
        "SYS$UMF", 
        # 文本搜索相关
        "DR$NUMBER_SEQUENCE", "DR$OBJECT_ATTRIBUTE", "DR$POLICY_TAB", "DR$THS", "DR$THS_PHRASE"
    ]
}
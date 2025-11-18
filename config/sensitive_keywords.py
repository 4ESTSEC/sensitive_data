# 敏感字段关键词（按类型分类，支持中英文）
SENSITIVE_FIELD_KEYWORDS = {
    "account": ["account", "user", "username", "login", "usr", "member", "账号", "用户名", "登录名"],
    "password": ["password", "pwd", "pass", "secret", "auth", "密码", "密钥"],
    "access_key": ["accesskey", "access_key", "ak", "sk", "secretkey", "secret_key", "token", "api_key", "apikey", "访问密钥"],
    "id_card": ["idcard", "id_card", "identity", "身份证", "身份证号", "证件号"],
    "phone": ["phone", "mobile", "tel", "telephone", "手机号", "电话"],
    "other": ["email", "mail", "address", "地址", "银行卡", "bank_card", "credit_card", "cc", "邮箱", "住址"]
}

# 敏感数据正则匹配规则（用于字段值校验，可选）
SENSITIVE_DATA_PATTERNS = {
    "phone": r"^1[3-9]\d{9}$",
    "id_card": r"^\d{17}[\dXx]$|^\d{15}$",
    "bank_card": r"^\d{16,19}$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "access_key": r"^[A-Za-z0-9]{16,40}$"
}
import os
import json
import csv
import decimal
from datetime import datetime
from typing import List, Dict
from common.logger import logger
from common.exception_handler import ExportError

class ResultExporter:
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _serialize_datetime(self, obj):
        """序列化 datetime、decimal 和 bytes 类型（JSON 导出用）"""
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, decimal.Decimal):
            # 将Decimal转换为字符串以保持精度
            return str(obj)
        elif isinstance(obj, bytes):
            # 将bytes转换为字符串，尝试UTF-8解码，失败则返回base64编码
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                import base64
                return f"[BINARY] {base64.b64encode(obj).decode('utf-8')[:50]}..."
        raise TypeError(f"Type {type(obj)} not serializable")

    def export_json(self, data: List[Dict]) -> None:
        """导出 JSON 格式"""
        file_path = os.path.join(self.output_dir, f"sensitive_data_{self.timestamp}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=self._serialize_datetime)
            logger.info(f"JSON 结果已保存：{file_path}")
        except Exception as e:
            raise ExportError("json", str(e)) from e

    def export_csv(self, data: List[Dict]) -> None:
        """导出 CSV 格式（按「库名→表名→字段→数据」层级）"""
        file_path = os.path.join(self.output_dir, f"sensitive_data_{self.timestamp}.csv")
        if not data:
            logger.warning("无敏感数据可导出 CSV")
            return

        try:
            with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                current_db = ""

                for item in data:
                    db_name = item["数据库名"]
                    table_name = item["表名"]
                    columns = [col["column_name"] for col in item["敏感字段详情"]]  # 所有字段
                    rows = item["rows"]

                    # 数据库名（切换时写入）
                    if db_name != current_db:
                        current_db = db_name
                        writer.writerow([f"📊 数据库：{db_name}"])
                        writer.writerow([])  # 空行分隔

                    # 表名 + 字段名 + 数据
                    writer.writerow([f"🗂️  表名：{table_name}"])
                    writer.writerow(columns)  # 字段行
                    for row in rows:
                        # 按字段顺序提取数据，确保对齐
                        data_row = [row.get(col, "") for col in columns]
                        writer.writerow(data_row)
                    writer.writerow([])  # 表之间空行分隔

            logger.info(f"CSV 结果已保存：{file_path}")
            logger.info("提示：CSV 文件可直接用 Excel 打开，层级结构清晰")
        except Exception as e:
            raise ExportError("csv", str(e)) from e

    def export(self, data: List[Dict], export_type: str = "all") -> None:
        """统一导出入口"""
        if export_type == "json" or export_type == "all":
            self.export_json(data)
        if export_type == "csv" or export_type == "all":
            self.export_csv(data)

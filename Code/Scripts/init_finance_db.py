import os
import pandas as pd
import sqlite3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

DATA_DIR = PROJECT_ROOT / "Data" / "财务数据"
DB_PATH = PROJECT_ROOT / "Model" / "finance_data.db"


def init_database():
    print(f"开始创建本地 SQLite 财务数据库: {DB_PATH}")

    if not DATA_DIR.exists():
        print(f"财务数据目录不存在: {DATA_DIR}，已自动创建。请放入 .xlsx 文件后重新运行。")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    total_tables = 0
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".xlsx") and not file.startswith("~$"):
                file_path = os.path.join(root, file)
                table_name = os.path.splitext(file)[0]
                # 清理表名：移除特殊字符
                table_name = table_name.replace(" ", "_").replace("-", "_").replace("（", "_").replace("）", "")

                print(f"正在导入表: {table_name} ...")
                try:
                    df = pd.read_excel(file_path, nrows=5000)
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    print(f"  成功导入 {len(df)} 行 x {len(df.columns)} 列")
                    total_tables += 1
                except Exception as e:
                    print(f"  导入失败: {e}")

    conn.close()
    print(f"\n全部财务数据入库完成！共导入 {total_tables} 张表。")


if __name__ == "__main__":
    init_database()

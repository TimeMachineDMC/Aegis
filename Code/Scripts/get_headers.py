import os
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

DATA_DIR = PROJECT_ROOT / "Data" / "财务数据"
OUTPUT_FILE = SCRIPT_DIR / "headers.txt"


def scan_headers():
    print("开始扫描所有 Excel 表头...")

    if not DATA_DIR.exists():
        print(f"财务数据目录不存在: {DATA_DIR}")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                if file.endswith(".xlsx") and not file.startswith("~$"):
                    file_path = os.path.join(root, file)
                    try:
                        df = pd.read_excel(file_path, nrows=0)
                        headers = list(df.columns)
                        rel = os.path.relpath(file_path, DATA_DIR)
                        f.write(f"【文件】: {rel}\n")
                        f.write(f"【表头】: {headers}\n")
                        f.write("-" * 50 + "\n\n")
                        print(f"已提取: {file}")
                    except Exception as e:
                        rel = os.path.relpath(file_path, DATA_DIR)
                        f.write(f"【文件】: {rel}\n")
                        f.write(f"【读取失败】: {e}\n")
                        f.write("-" * 50 + "\n\n")
                        print(f"读取失败: {file}, {e}")

    print(f"\n全部表头提取完成！结果保存在: {OUTPUT_FILE}")


if __name__ == "__main__":
    scan_headers()

"""
数据清洗脚本 - 修复 RAM 和电池字段中的垃圾文本

问题:
- RAM: "12GB游戏运行良好大于78.29%手机内存行业最高：24G＞" → 应为 12
- Battery: "6620mAh电池类型：不可拆卸式电池" → 应为 6620
- "未知" / "暂无数据" → NULL

用法: python -m backend.data.clean_ram_battery
"""
import re
import sqlite3
import sys
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "data" / "phones.db"


def extract_ram_value(raw: str) -> int | None:
    """从 RAM 文本中提取数值（GB）"""
    if not raw or raw in ("未知", "暂无数据"):
        return None
    # 匹配第一个数字（可能带小数点）
    m = re.search(r'(\d+(?:\.\d+)?)\s*[Gg]', raw)
    if m:
        val = float(m.group(1))
        return int(val) if val == int(val) else int(val)
    # 纯数字
    m = re.search(r'^(\d+)$', raw.strip())
    if m:
        return int(m.group(1))
    return None


def extract_battery_value(raw: str) -> int | None:
    """从电池文本中提取数值（mAh）"""
    if not raw or "暂无" in raw:
        return None
    # 匹配第一个数字
    m = re.search(r'(\d{3,5})', raw)
    if m:
        return int(m.group(1))
    return None


def clean_database(dry_run: bool = True):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # --- RAM ---
    c.execute("SELECT id, brand, model, ram FROM phones WHERE typeof(ram) = 'text'")
    ram_rows = c.fetchall()
    ram_fixed = 0
    ram_null = 0
    for row_id, brand, model, raw in ram_rows:
        val = extract_ram_value(raw)
        if val is not None:
            if not dry_run:
                c.execute("UPDATE phones SET ram = ? WHERE id = ?", (val, row_id))
            ram_fixed += 1
        else:
            if not dry_run:
                c.execute("UPDATE phones SET ram = NULL WHERE id = ?", (row_id,))
            ram_null += 1

    # --- Battery ---
    c.execute("SELECT id, brand, model, battery FROM phones WHERE typeof(battery) = 'text'")
    bat_rows = c.fetchall()
    bat_fixed = 0
    bat_null = 0
    for row_id, brand, model, raw in bat_rows:
        val = extract_battery_value(raw)
        if val is not None:
            if not dry_run:
                c.execute("UPDATE phones SET battery = ? WHERE id = ?", (val, row_id))
            bat_fixed += 1
        else:
            if not dry_run:
                c.execute("UPDATE phones SET battery = NULL WHERE id = ?", (row_id,))
            bat_null += 1

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"{'[DRY RUN] ' if dry_run else ''}清洗完成:")
    print(f"  RAM: {len(ram_rows)} 条文本 → {ram_fixed} 提取成功, {ram_null} 设为 NULL")
    print(f"  Battery: {len(bat_rows)} 条文本 → {bat_fixed} 提取成功, {bat_null} 设为 NULL")


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("=== 预览模式（加 --apply 实际执行）===\n")
    clean_database(dry_run=dry_run)

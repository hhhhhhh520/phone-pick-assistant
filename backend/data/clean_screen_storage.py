"""
清洗 screen_size / storage 列的爬虫残留文本 (2026-09-06)

与 clean_ram_battery.py (C1/C2) 同类问题：
- screen_size: '6.75英寸纠错'、'6.67英寸主屏分辨率：1604x720px' 等 129 条
- storage: '256GB'、'未知' 等 5 条

处理：提取前导数值；提取不到置 NULL。幂等，可重复执行。
用法:
    .venv/Scripts/python.exe -m backend.data.clean_screen_storage
"""
import re
import sqlite3
from datetime import datetime

from backend.config import get_settings


def extract_number(value: str, as_float: bool = False):
    """提取字符串前导数值，失败返回 None"""
    match = re.match(r"\s*(\d+(?:\.\d+)?)", str(value))
    if not match:
        return None
    return float(match.group(1)) if as_float else int(float(match.group(1)))


def main() -> None:
    db_path = get_settings().database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    now = datetime.now().isoformat()
    stats = {"screen_size": {"fixed": 0, "nulled": 0}, "storage": {"fixed": 0, "nulled": 0}}

    for col, as_float in (("screen_size", True), ("storage", False)):
        rows = cur.execute(
            f"SELECT id, {col} FROM phones "
            f"WHERE {col} IS NOT NULL AND CAST({col} AS TEXT) GLOB '*[^0-9.]*'"
        ).fetchall()
        for phone_id, raw in rows:
            value = extract_number(raw, as_float=as_float)
            if value is None:
                stats[col]["nulled"] += 1
            else:
                stats[col]["fixed"] += 1
            cur.execute(
                f"UPDATE phones SET {col} = ?, updated_at = ? WHERE id = ?",
                (value, now, phone_id),
            )
        print(f"{col}: {len(rows)} 条脏数据 -> 数值提取 {stats[col]['fixed']}, 置 NULL {stats[col]['nulled']}")

    conn.commit()
    conn.close()

    # 复检：应无残留
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for col in ("screen_size", "storage"):
        remain = cur.execute(
            f"SELECT COUNT(*) FROM phones WHERE {col} IS NOT NULL AND CAST({col} AS TEXT) GLOB '*[^0-9.]*'"
        ).fetchone()[0]
        assert remain == 0, f"{col} 仍有 {remain} 条脏数据"
    conn.close()
    print("复检通过：两列已无非数值数据")


if __name__ == "__main__":
    main()

"""
将清洗后的数据导入数据库
"""

import json
import sqlite3
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "phones_cleaned.json"
DB_FILE = ROOT / "backend" / "data" / "phones.db"

# 品牌名称统一
BRAND_MAP = {
    'HUAWEI': '华为',
    'Apple': '苹果',
    'Redmi': '红米',
    'realme': '真我',
    'iQOO': 'iQOO',
}


def parse_int(value: str, pattern: str = r'(\d+)') -> int:
    """从字符串提取整数"""
    if not value:
        return None
    match = re.search(pattern, str(value))
    return int(match.group(1)) if match else None


def parse_float(value: str, pattern: str = r'([\d.]+)') -> float:
    """从字符串提取浮点数"""
    if not value:
        return None
    match = re.search(pattern, str(value))
    return float(match.group(1)) if match else None


def import_phone(phone: dict, cursor) -> tuple:
    """导入单条手机数据，返回 (插入, 更新) 计数"""
    name = phone.get('name', '')
    if not name:
        return (0, 0)

    # 统一品牌名称
    brand = phone.get('brand', '')
    brand = BRAND_MAP.get(brand, brand)

    # 解析字段
    price = phone.get('price') or parse_int(phone.get('params', {}).get('电商报价'), r'￥(\d+)')
    processor = phone.get('processor', '')
    ram = parse_int(phone.get('ram'))
    storage = parse_int(phone.get('storage'))
    battery = parse_int(phone.get('battery'))
    screen_size = parse_float(phone.get('screen_size'))
    weight = parse_int(phone.get('weight'))
    refresh_rate = parse_int(phone.get('refresh_rate'))
    os = phone.get('os', '')

    # 解析摄像头
    camera_main = parse_int(phone.get('camera_main'))
    camera_front = parse_int(phone.get('camera_front'))

    # 图片
    images = phone.get('images', [])
    image_url = images[0] if images else None

    # 检查是否已存在（按名称模糊匹配）
    cursor.execute("SELECT id FROM phones WHERE model LIKE ?", (f"%{name[:30]}%",))
    existing = cursor.fetchone()

    now = datetime.now().isoformat()

    if existing:
        # 更新
        cursor.execute("""
            UPDATE phones SET
                brand = ?, price = ?, processor = ?, ram = ?, storage = ?,
                battery = ?, screen_size = ?, weight = ?, screen_refresh = ?,
                camera_main = ?, camera_front = ?, image_url = ?, updated_at = ?
            WHERE id = ?
        """, (brand, price or 0, processor, ram, storage, battery, screen_size,
              weight, refresh_rate, camera_main, camera_front, image_url, now, existing[0]))
        return (0, 1)
    else:
        # 插入
        cursor.execute("""
            INSERT INTO phones (brand, model, price, processor, ram, storage,
                battery, screen_size, weight, screen_refresh, camera_main, camera_front,
                image_url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (brand, name, price or 0, processor, ram, storage, battery, screen_size,
              weight, refresh_rate, camera_main, camera_front, image_url, now, now))
        return (1, 0)


def main():
    print("=" * 60)
    print("导入清洗数据到数据库")
    print("=" * 60)

    # 读取清洗后的数据
    with open(DATA_FILE, encoding='utf-8') as f:
        phones = json.load(f)

    print(f"待导入: {len(phones)} 条")

    # 连接数据库
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 查看当前数据量
    cursor.execute("SELECT COUNT(*) FROM phones")
    before = cursor.fetchone()[0]
    print(f"数据库当前: {before} 条")

    # 导入
    inserted, updated = 0, 0
    for phone in phones:
        ins, upd = import_phone(phone, cursor)
        inserted += ins
        updated += upd

    conn.commit()

    # 查看导入后数据量
    cursor.execute("SELECT COUNT(*) FROM phones")
    after = cursor.fetchone()[0]

    print(f"\n导入结果:")
    print(f"  新增: {inserted} 条")
    print(f"  更新: {updated} 条")
    print(f"  数据库总计: {after} 条")

    # 显示品牌分布
    cursor.execute("SELECT brand, COUNT(*) FROM phones GROUP BY brand ORDER BY COUNT(*) DESC")
    print("\n品牌分布:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()
    print("\n完成!")


if __name__ == "__main__":
    main()

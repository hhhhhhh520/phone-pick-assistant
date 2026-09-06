"""
从 phones_export.json 恢复/重建 phones.db（export_phones_json.py 的逆操作）。

用于数据库丢失后的恢复：先用 backend/data/schema.sql 建表，
再从 JSON 副本灌回全量数据。默认全量替换（先清空 phones 表）。

用法:
    .venv/Scripts/python.exe scripts/import_phones_json.py [--yes]
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from backend.config import get_settings  # noqa: E402
from backend.models.domain import Phone, init_db  # noqa: E402


# to_dict 的嵌套结构 -> Phone 列
def _num(value, cast=float):
    """数值字段容错：库里的历史数据可能混入 '6.75英寸纠错' 类文本，提取前导数值"""
    import re
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return cast(value)
    match = re.match(r"\s*(\d+(?:\.\d+)?)", str(value))
    return cast(float(match.group(1))) if match else None


def row_to_phone(row: dict) -> Phone:
    screen = row.get("screen") or {}
    camera = row.get("camera") or {}
    charging = row.get("charging") or {}
    dump = lambda v: json.dumps(v, ensure_ascii=False) if v is not None else None  # noqa: E731
    now = datetime.now().isoformat()
    return Phone(
        id=row.get("id"),
        brand=row["brand"],
        model=row["model"],
        price=_num(row.get("price"), cast=int),
        release_date=row.get("release_date"),
        screen_size=_num(screen.get("size")),
        screen_type=screen.get("type"),
        screen_refresh=_num(screen.get("refresh"), cast=int),
        processor=row.get("processor"),
        ram=_num(row.get("ram"), cast=int),
        storage=_num(row.get("storage"), cast=int),
        camera_main=_num(camera.get("main"), cast=int),
        camera_ultra=_num(camera.get("ultra"), cast=int),
        camera_telephoto=_num(camera.get("telephoto"), cast=int),
        camera_front=_num(camera.get("front"), cast=int),
        sensor_main=camera.get("sensorMain"),
        telephoto_type=camera.get("telephotoType"),
        has_ois=camera.get("hasOis"),
        image_brand=camera.get("imageBrand"),
        camera_score=_num(camera.get("score"), cast=int),
        battery=_num(row.get("battery"), cast=int),
        charging_wired=_num(charging.get("wired"), cast=int),
        charging_wireless=_num(charging.get("wireless"), cast=int),
        weight=_num(row.get("weight"), cast=int),
        url=row.get("url"),
        image_url=row.get("imageUrl"),
        features=dump(row.get("features")),
        suitable_for=dump(row.get("suitable_for")),
        pros=dump(row.get("pros")),
        cons=dump(row.get("cons")),
        created_at=now,
        updated_at=now,
    )


def main() -> None:
    if "--yes" not in sys.argv:
        print("警告：将清空并全量替换 phones 表。确认请加 --yes")
        sys.exit(1)

    settings = get_settings()
    init_db()  # 确保表结构存在（幂等）

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)

    json_path = Path(__file__).parent.parent / "backend" / "data" / "phones_export.json"
    with open(json_path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    with Session() as db:
        db.query(Phone).delete()
        db.add_all(row_to_phone(r) for r in rows)
        db.commit()

    print(f"Restored {len(rows)} phones -> {settings.database_url}")


if __name__ == "__main__":
    main()

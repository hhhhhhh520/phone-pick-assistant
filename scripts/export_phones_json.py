"""
把 phones.db 全量导出为 JSON，作为数据的版本控制副本。

phones.db 被 .gitignore 的 *.db 规则排除，数据库本身（353 款手机、
多轮爬取+清洗的成果）没有任何版本控制——磁盘故障即全部丢失。
本脚本导出一份 JSON 进 git 作为异地副本；恢复脚本见 import_phones_json.py。

用法:
    .venv/Scripts/python.exe scripts/export_phones_json.py
"""
import json
import sys
from pathlib import Path

# 保证可以以任意 CWD 运行
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from backend.config import get_settings  # noqa: E402
from backend.models.domain import Phone  # noqa: E402


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        phones = db.query(Phone).order_by(Phone.id).all()
        data = [p.to_dict() for p in phones]

    out_path = Path(__file__).parent.parent / "backend" / "data" / "phones_export.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"Exported {len(data)} phones -> {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

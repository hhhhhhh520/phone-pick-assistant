"""
影像数据补全（2026-09-06）
============================

两项，全部是"可靠推导值"，不编造规格：

1. camera_score 缓存列：用 camera_scoring_service 批量计算综合影像评分入库。
   此前列几乎全空，详情接口每次现算；入库后展示直接可读，也便于排查排序。
   （芯片分已改为按安兔兔跑分分档，新芯片不再被冤枉为入门档。）

2. "影像"标签下放：满足任一条件的机型在 features 中追加"影像"——
   - 主摄 >= 1亿像素（硬件规格上以影像为卖点）
   - 有明确主摄传感器型号（sensor_main 非空，厂商公布过影像细节）
   目的：让"拍照"场景的 tier-1 检索在中高价位不再恒为空。
   幂等，可重复执行。

用法:
    .venv/Scripts/python.exe -m backend.data.enrich_camera_data
"""
import json
import sqlite3
from datetime import datetime

from backend.config import get_settings
from backend.models.domain import Phone
from backend.services.camera_score import camera_scoring_service

STRONG_PIXEL_THRESHOLD = 10000  # 万，即 1 亿


def _append_feature(features_raw, tag: str) -> tuple:
    """向 features JSON 数组追加标签，已存在则原样返回。返回 (新值, 是否修改)。"""
    try:
        tags = json.loads(features_raw) if features_raw else []
        if not isinstance(tags, list):
            tags = []
    except (json.JSONDecodeError, TypeError):
        tags = []
    if tag in tags:
        return features_raw, False
    tags.append(tag)
    return json.dumps(tags, ensure_ascii=False), True


def main() -> None:
    db_path = get_settings().database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    now = datetime.now().isoformat()

    rows = cur.execute("SELECT * FROM phones").fetchall()
    score_updated = 0
    tag_updated = 0
    score_stats = []

    for r in rows:
        phone = Phone(**{c: r[c] for c in r.keys()})

        # 1. 影像评分缓存
        total = camera_scoring_service.calc_total_score(phone)["total"]
        if r["camera_score"] != total:
            cur.execute(
                "UPDATE phones SET camera_score = ?, updated_at = ? WHERE id = ?",
                (total, now, r["id"]),
            )
            score_updated += 1
        score_stats.append((total, r["brand"], r["model"]))

        # 2. 影像标签下放
        pixels = phone.camera_main or 0
        qualifies = pixels >= STRONG_PIXEL_THRESHOLD or bool(phone.sensor_main)
        if qualifies:
            new_features, changed = _append_feature(r["features"], "影像")
            if changed:
                cur.execute(
                    "UPDATE phones SET features = ?, updated_at = ? WHERE id = ?",
                    (new_features, now, r["id"]),
                )
                tag_updated += 1

    conn.commit()

    score_stats.sort(reverse=True)
    n = len(score_stats)
    print(f"camera_score 入库: 更新 {score_updated}/{n} 行")
    print(f"\"影像\"标签新增: {tag_updated} 行")
    top = ", ".join(f"{b}{m}({s})" for s, b, m in score_stats[:5])
    print(f"评分 Top5: {top}")
    print(f"评分分布: 90+={sum(1 for s, *_ in score_stats if s >= 90)}, "
          f"70-89={sum(1 for s, *_ in score_stats if 70 <= s < 90)}, "
          f"50-69={sum(1 for s, *_ in score_stats if 50 <= s < 69)}, "
          f"<50={sum(1 for s, *_ in score_stats if s < 50)}")

    conn.close()


if __name__ == "__main__":
    main()

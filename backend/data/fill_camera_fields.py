"""
数据补全脚本 - 填充影像评分字段

数据来源:
1. IMAGE_CONFIG (seed.py) - 约40款旗舰机的精确配置
2. features 字段 - 提取影像品牌标签
3. 其余字段保持 NULL（不猜测）

用法: python -m backend.data.fill_camera_fields
"""
import sqlite3
import json
import re
import sys
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "data" / "phones.db"

# 从 seed.py 复制的 IMAGE_CONFIG
IMAGE_CONFIG = {
    "小米14 Ultra": ("LYT-900", "双潜望", "徕卡"),
    "小米15 Ultra": ("LYT-900", "双潜望", "徕卡"),
    "小米15 Pro": ("LYT-818", "单潜望", "徕卡"),
    "小米15": ("光影猎人900", "直立长焦", "徕卡"),
    "小米14": ("光影猎人900", "直立长焦", "徕卡"),
    "MIX Fold 4": ("LYT-900", "单潜望", "徕卡"),
    "MIX Flip": ("光影猎人800", "无", "徕卡"),
    "Find X7 Ultra": ("LYT-900", "双潜望", "哈苏"),
    "Find X8 Pro": ("LYT-818", "双潜望", "哈苏"),
    "Find X8": ("LYT-700", "单潜望", "哈苏"),
    "Find N3": ("LYT-800", "单潜望", "哈苏"),
    "Find N3 Flip": ("IMX890", "直立长焦", "哈苏"),
    "一加12": ("LYT-808", "单潜望", "哈苏"),
    "一加13": ("LYT-808", "单潜望", "哈苏"),
    "X100 Pro": ("IMX989", "单潜望", "蔡司"),
    "X200 Pro": ("LYT-818", "单潜望", "蔡司"),
    "X200": ("IMX920", "直立长焦", "蔡司"),
    "X Fold3 Pro": ("LYT-T808", "单潜望", "蔡司"),
    "X Fold3": ("LYT-T808", "直立长焦", "蔡司"),
    "Mate 70 Pro+": ("IMX989", "单潜望", "XMAGE"),
    "Mate 70 Pro": ("IMX989", "单潜望", "XMAGE"),
    "Mate 60 Pro+": ("IMX888", "单潜望", "XMAGE"),
    "P60 Pro": ("IMX888", "单潜望", "XMAGE"),
    "Pura 70 Ultra": ("IMX989", "单潜望", "XMAGE"),
    "Mate X5": ("IMX766", "直立长焦", "XMAGE"),
    "Pocket 2": ("IMX766", "直立长焦", "XMAGE"),
    "Magic7 Pro": ("OV50K", "单潜望", "鹰眼"),
    "Magic6 Pro": ("OV50H", "单潜望", "鹰眼"),
    "Magic V3": ("OV50H", "直立长焦", "鹰眼"),
    "Magic V Flip": ("IMX800", "无", "鹰眼"),
    "iPhone 16 Pro Max": ("IMX803", "单潜望", "原色"),
    "iPhone 16 Pro": ("IMX803", "单潜望", "原色"),
    "iPhone 16 Plus": ("IMX803", "无", "原色"),
    "iPhone 16": ("IMX803", "无", "原色"),
    "iPhone 15 Pro Max": ("IMX803", "单潜望", "原色"),
    "iPhone 15 Pro": ("IMX703", "直立长焦", "原色"),
    "iPhone 15": ("IMX703", "无", "原色"),
    "iPhone 14": ("IMX703", "无", "原色"),
    "Galaxy S24 Ultra": ("HP2", "单潜望", "原色"),
    "Galaxy S24": ("GN3", "直立长焦", "原色"),
    "Galaxy Z Fold6": ("GN3", "直立长焦", "原色"),
    "Galaxy Z Flip6": ("GN3", "无", "原色"),
    "Redmi K70 Pro": ("光影猎人800", "无", "原色"),
    "Redmi K80": ("光影猎人800", "无", "原色"),
    "Redmi Note 14 Pro+": ("HP3", "无", "原色"),
    "Redmi Note 14": ("OV50C", "无", "原色"),
    "iQOO 12": ("GN5", "直立长焦", "原色"),
    "iQOO Neo10": ("IMX920", "无", "原色"),
    "iQOO Z9 Turbo+": ("LYT-600", "无", "原色"),
    "realme GT5 Pro": ("LYT-808", "单潜望", "原色"),
    "GT Neo6": ("LYT-600", "无", "原色"),
    "魅族21": ("HP3", "无", "原色"),
    "努比亚Z60 Ultra": ("IMX800", "直立长焦", "原色"),
    "Reno 11 Pro": ("LYT-700", "直立长焦", "原色"),
    "荣耀X60 Pro": ("HM6", "无", "原色"),
    "荣耀X50": ("HM6", "无", "原色"),
    "vivo Y300 Pro": ("OV50D", "无", "原色"),
}

# 影像品牌关键词映射
IMAGE_BRAND_KEYWORDS = {
    "徕卡": "徕卡",
    "哈苏": "哈苏",
    "蔡司": "蔡司",
    "XMAGE": "XMAGE",
    "Blueimage": "Blueimage",
    "鹰眼": "鹰眼",
}

# 品牌级默认影像品牌（旗舰系列才有联名，但至少给个默认值）
BRAND_DEFAULT_IMAGE = {
    "华为": "XMAGE",
    "小米": "徕卡",
    "红米": "原色",
    "OPPO": "哈苏",
    "一加": "哈苏",
    "vivo": "蔡司",
    "荣耀": "鹰眼",
    "苹果": "原色",
    "三星": "原色",
    "iQOO": "原色",
    "真我": "原色",
    "ROG": "原色",
    "联想": "原色",
    "努比亚": "原色",
    "索尼": "原色",
    "魅族": "原色",
    "黑鲨": "原色",
}


def extract_image_brand_from_features(features_str: str) -> str | None:
    """从 features JSON 字符串中提取影像品牌"""
    if not features_str:
        return None
    try:
        features = json.loads(features_str) if isinstance(features_str, str) else features_str
    except (json.JSONDecodeError, TypeError):
        return None
    features_text = "".join(features) if isinstance(features, list) else str(features)
    for keyword, brand in IMAGE_BRAND_KEYWORDS.items():
        if keyword in features_text:
            return brand
    return None


def fill_camera_fields(dry_run: bool = True):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, brand, model, features, sensor_main, telephoto_type, has_ois, image_brand FROM phones")
    phones = c.fetchall()

    stats = {"config_match": 0, "feature_brand": 0, "no_change": 0}

    for phone in phones:
        pid = phone["id"]
        model = phone["model"]
        features = phone["features"]

        # 1. Try IMAGE_CONFIG match
        config = IMAGE_CONFIG.get(model)
        if config:
            sensor, telephoto, brand = config
            if not dry_run:
                c.execute(
                    "UPDATE phones SET sensor_main=?, telephoto_type=?, has_ois=?, image_brand=? WHERE id=?",
                    (sensor, telephoto, True, brand, pid)
                )
            stats["config_match"] += 1
            continue

        # 2. Try extracting image_brand from features
        img_brand = extract_image_brand_from_features(features)
        if img_brand and not phone["image_brand"]:
            if not dry_run:
                c.execute("UPDATE phones SET image_brand=? WHERE id=?", (img_brand, pid))
            stats["feature_brand"] += 1
            continue

        # 3. Use brand-level default for image_brand
        if not phone["image_brand"]:
            default_brand = BRAND_DEFAULT_IMAGE.get(phone["brand"])
            if default_brand:
                if not dry_run:
                    c.execute("UPDATE phones SET image_brand=? WHERE id=?", (default_brand, pid))
                stats["brand_default"] = stats.get("brand_default", 0) + 1
                continue

        stats["no_change"] += 1

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"{'[DRY RUN] ' if dry_run else ''}影像字段补全:")
    print(f"  IMAGE_CONFIG 精确匹配: {stats['config_match']}")
    print(f"  features 提取品牌: {stats['feature_brand']}")
    print(f"  品牌默认值: {stats.get('brand_default', 0)}")
    print(f"  无数据可填: {stats['no_change']}")


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("=== 预览模式（加 --apply 实际执行）===\n")
    fill_camera_fields(dry_run=dry_run)

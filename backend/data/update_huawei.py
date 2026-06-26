"""
补充华为品牌缺失数据脚本
运行: python -m backend.data.update_huawei
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from backend.models.domain import SessionLocal


# 华为机型数据补充规则
# 格式: "型号": {字段: 值}
# 无线充电: Mate/Pura系列支持，nova部分支持，畅享不支持
# 影像品牌: Mate/Pura系列为XMAGE，nova和畅享无联名
HUAWEI_UPDATE_RULES = {
    # Mate 系列 - 旗舰商务
    "Mate 70 Pro+": {
        "wireless_charging": 80,
        "image_brand": "XMAGE",
        "wired_charging": 100,
        "camera_main": 50,
    },
    "Mate 70 Pro": {
        "wireless_charging": 80,
        "image_brand": "XMAGE",
        "wired_charging": 100,
        "camera_main": 50,
    },
    "Mate 60 Pro+": {
        "wireless_charging": 50,
        "image_brand": "XMAGE",
        "wired_charging": 88,
        "camera_main": 48,
    },
    # Pura 系列 - 影像旗舰
    "Pura 70 Ultra": {
        "wireless_charging": 80,
        "image_brand": "XMAGE",
        "wired_charging": 100,
        "camera_main": 50,
    },
    # P 系列 (旧命名)
    "P60 Pro": {
        "wireless_charging": 50,
        "image_brand": "XMAGE",
        "wired_charging": 88,
        "camera_main": 48,
    },
    # 折叠屏
    "Mate X5": {
        "wireless_charging": 50,
        "image_brand": "XMAGE",
        "wired_charging": 66,
        "camera_main": 50,
    },
    "Pocket 2": {
        "wireless_charging": 40,
        "image_brand": "XMAGE",
        "wired_charging": 66,
        "camera_main": 50,
    },
    # nova 系列 - 时尚年轻 (部分支持无线充电)
    # nova 12 Ultra: 支持
    # nova 12 Pro: 支持
    # nova 12: 不支持
    # nova 11 系列: 部分支持
    "nova 12 Ultra": {
        "wireless_charging": 50,
        "image_brand": None,  # 无联名
        "wired_charging": 100,
        "camera_main": 50,
    },
    "nova 12 Pro": {
        "wireless_charging": 50,
        "image_brand": None,
        "wired_charging": 100,
        "camera_main": 50,
    },
    "nova 12": {
        "wireless_charging": 0,  # 不支持
        "image_brand": None,
        "wired_charging": 66,
        "camera_main": 50,
    },
    "nova 11 Ultra": {
        "wireless_charging": 50,
        "image_brand": None,
        "wired_charging": 100,
        "camera_main": 50,
    },
    "nova 11 Pro": {
        "wireless_charging": 0,  # 不支持
        "image_brand": None,
        "wired_charging": 66,
        "camera_main": 50,
    },
    "nova 11": {
        "wireless_charging": 0,
        "image_brand": None,
        "wired_charging": 66,
        "camera_main": 50,
    },
    # 畅享系列 - 入门级 (不支持无线充电)
    "畅享 70 Pro": {
        "wireless_charging": 0,
        "image_brand": None,
        "wired_charging": 40,
        "camera_main": 108,
    },
    "畅享 70": {
        "wireless_charging": 0,
        "image_brand": None,
        "wired_charging": 22.5,
        "camera_main": 50,
    },
    "畅享 60 Pro": {
        "wireless_charging": 0,
        "image_brand": None,
        "wired_charging": 40,
        "camera_main": 48,
    },
    "畅享 60": {
        "wireless_charging": 0,
        "image_brand": None,
        "wired_charging": 22.5,
        "camera_main": 48,
    },
    "畅享 50 Pro": {
        "wireless_charging": 0,
        "image_brand": None,
        "wired_charging": 40,
        "camera_main": 50,
    },
    "畅享 50": {
        "wireless_charging": 0,
        "image_brand": None,
        "wired_charging": 22.5,
        "camera_main": 13,
    },
}


def get_series_from_model(model: str) -> str:
    """从型号名称判断系列"""
    model_lower = model.lower()
    if "mate" in model_lower:
        return "Mate"
    elif "pura" in model_lower or model_lower.startswith("p "):
        return "Pura"
    elif model_lower.startswith("p"):
        return "P"  # 旧P系列
    elif "nova" in model_lower:
        return "nova"
    elif "畅享" in model:
        return "畅享"
    return "未知"


def get_default_values(series: str) -> dict:
    """根据系列获取默认值"""
    defaults = {
        "Mate": {
            "wireless_charging": 50,  # 默认支持
            "image_brand": "XMAGE",
            "wired_charging": 66,
        },
        "Pura": {
            "wireless_charging": 50,
            "image_brand": "XMAGE",
            "wired_charging": 66,
        },
        "P": {
            "wireless_charging": 50,
            "image_brand": "XMAGE",
            "wired_charging": 66,
        },
        "nova": {
            "wireless_charging": 0,  # 默认不支持
            "image_brand": None,
            "wired_charging": 66,
        },
        "畅享": {
            "wireless_charging": 0,  # 不支持
            "image_brand": None,
            "wired_charging": 22.5,
        },
    }
    return defaults.get(series, {})


def update_huawei_data():
    """更新华为品牌缺失数据"""
    db = SessionLocal()
    stats = {
        "total": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
    }

    try:
        # 查询所有华为手机
        phones = db.execute(
            text("SELECT id, model, charging_wireless, image_brand, charging_wired, camera_main FROM phones WHERE brand = '华为'")
        ).fetchall()

        stats["total"] = len(phones)
        print(f"找到 {len(phones)} 款华为手机")

        for phone in phones:
            phone_id, model, wireless, img_brand, wired, main_cam = phone
            series = get_series_from_model(model)

            # 获取更新规则
            rules = HUAWEI_UPDATE_RULES.get(model, None)
            if not rules:
                rules = get_default_values(series)

            # 检查是否需要更新
            needs_update = False
            update_fields = {}

            # 无线充电
            if wireless is None:
                update_fields["charging_wireless"] = rules.get("wireless_charging", 0)
                needs_update = True

            # 影像品牌
            if img_brand is None:
                update_fields["image_brand"] = rules.get("image_brand")
                needs_update = True

            # 有线充电
            if wired is None:
                update_fields["charging_wired"] = rules.get("wired_charging")
                needs_update = True

            # 主摄像素
            if main_cam is None:
                update_fields["camera_main"] = rules.get("camera_main")
                needs_update = True

            if needs_update:
                # 构建更新SQL
                set_clauses = []
                params = {"phone_id": phone_id}

                for field, value in update_fields.items():
                    if value is not None:
                        set_clauses.append(f"{field} = :{field}")
                        params[field] = value
                    elif field == "image_brand":
                        # image_brand 可以为 None
                        set_clauses.append(f"{field} = :{field}")
                        params[field] = value

                if set_clauses:
                    # 字段名来自代码硬编码的 update_fields 字典，使用参数化查询防止注入
                    sql = f"UPDATE phones SET {', '.join(set_clauses)} WHERE id = :phone_id"  # nosec B608
                    db.execute(text(sql), params)
                    stats["updated"] += 1
                    print(f"  更新: {model} -> {update_fields}")
            else:
                stats["skipped"] += 1

        db.commit()
        print("\n更新完成:")
        print(f"  总数: {stats['total']}")
        print(f"  已更新: {stats['updated']}")
        print(f"  已跳过: {stats['skipped']}")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        stats["errors"] += 1
        raise
    finally:
        db.close()

    return stats


if __name__ == "__main__":
    update_huawei_data()

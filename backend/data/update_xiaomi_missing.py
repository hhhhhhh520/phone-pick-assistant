"""
补充小米/Redmi品牌缺失数据脚本
运行: python -m backend.data.update_xiaomi_missing
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models.domain import SessionLocal, Phone


# 小米/Redmi机型配置表
# 格式: "型号": {"wireless_charging": 功率(不支持为0), "image_brand": 影像品牌}
XIAOMI_CONFIG = {
    # 小米数字系列 - 徕卡影像，支持无线充电
    "小米15 Ultra": {"wireless_charging": 80, "image_brand": "徕卡"},
    "小米15 Pro": {"wireless_charging": 50, "image_brand": "徕卡"},
    "小米15": {"wireless_charging": 50, "image_brand": "徕卡"},
    "小米14 Ultra": {"wireless_charging": 80, "image_brand": "徕卡"},
    "小米14": {"wireless_charging": 50, "image_brand": "徕卡"},

    # 小米MIX系列 - 徕卡影像，支持无线充电
    "MIX Fold 4": {"wireless_charging": 50, "image_brand": "徕卡"},
    "MIX Flip": {"wireless_charging": 0, "image_brand": "徕卡"},  # MIX Flip不支持无线充电

    # Redmi K系列 - 无联名，部分Pro支持无线充电
    "Redmi K70 Pro": {"wireless_charging": 0, "image_brand": "原色"},
    "Redmi K80": {"wireless_charging": 0, "image_brand": "原色"},
    "Redmi K80 Pro": {"wireless_charging": 50, "image_brand": "原色"},  # K80 Pro支持无线充电
    "Redmi K60 Pro": {"wireless_charging": 30, "image_brand": "原色"},  # K60 Pro支持无线充电
    "Redmi K60": {"wireless_charging": 30, "image_brand": "原色"},  # K60标准版也支持无线充电

    # Redmi Note系列 - 无联名，不支持无线充电
    "Redmi Note 14 Pro+": {"wireless_charging": 0, "image_brand": "原色"},
    "Redmi Note 14": {"wireless_charging": 0, "image_brand": "原色"},
    "Redmi Note 13 Pro+": {"wireless_charging": 0, "image_brand": "原色"},
    "Redmi Note 13": {"wireless_charging": 0, "image_brand": "原色"},
}


def update_missing_data():
    """补充小米/Redmi品牌缺失数据"""
    db = SessionLocal()

    stats = {
        "total_updated": 0,
        "wireless_updated": 0,
        "wireless_not_supported": 0,
        "image_brand_updated": 0,
        "camera_updated": 0,
    }

    try:
        # 查询小米/Redmi品牌的所有手机
        phones = db.query(Phone).filter(Phone.brand.in_(["小米", "Redmi"])).all()

        print(f"找到 {len(phones)} 款小米/Redmi手机\n")

        for phone in phones:
            updated = False

            # 获取机型配置
            config = XIAOMI_CONFIG.get(phone.model, {})

            # 1. 补充无线充电
            if phone.charging_wireless is None:
                wireless = config.get("wireless_charging")
                if wireless is not None:
                    phone.charging_wireless = wireless
                    stats["wireless_updated"] += 1
                    if wireless == 0:
                        stats["wireless_not_supported"] += 1
                    updated = True
                    print(f"  {phone.model}: 无线充电 -> {wireless}W" if wireless > 0 else f"  {phone.model}: 无线充电 -> 不支持")

            # 2. 补充影像品牌
            if phone.image_brand is None or phone.image_brand == "":
                image_brand = config.get("image_brand")
                if image_brand:
                    phone.image_brand = image_brand
                    stats["image_brand_updated"] += 1
                    updated = True
                    print(f"  {phone.model}: 影像品牌 -> {image_brand}")

            # 3. 补充摄像头参数（超广角/长焦为None时标记为0）
            if phone.camera_ultra is None:
                phone.camera_ultra = 0
                stats["camera_updated"] += 1
                updated = True

            if phone.camera_telephoto is None:
                phone.camera_telephoto = 0
                stats["camera_updated"] += 1
                updated = True

            if updated:
                stats["total_updated"] += 1

        db.commit()

        # 输出统计
        print("\n" + "="*50)
        print(f"已更新: {stats['total_updated']}条记录")
        print(f"- 无线充电补充: {stats['wireless_updated']}条（其中{stats['wireless_not_supported']}条不支持）")
        print(f"- 影像品牌补充: {stats['image_brand_updated']}条")
        print(f"- 摄像头参数补充: {stats['camera_updated']}条")

        return stats

    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_missing_data()

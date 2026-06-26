"""
手机标签自动填充脚本

基于 feature_tags.py 的定义，为数据库中的手机自动填充 features 和 suitable_for 字段。
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.domain import Phone
from backend.data.feature_tags import (
    find_matching_feature_tags,
    find_matching_suitable_for_tags,
    get_tag_statistics
)


def get_db_session():
    """获取数据库会话"""
    db_path = project_root / "backend" / "data" / "phones.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    return Session()


def phone_to_dict(phone: Phone) -> dict:
    """将 Phone 对象转换为字典"""
    # 构建屏幕信息字符串
    screen_info = ""
    if phone.screen_type:
        screen_info += phone.screen_type
    if phone.screen_refresh:
        screen_info += f" {phone.screen_refresh}Hz"

    return {
        "model": phone.model,
        "brand": phone.brand,
        "price": phone.price,
        "processor": phone.processor,
        "ram": phone.ram,
        "storage": phone.storage,
        "battery": phone.battery,
        "screen": screen_info.strip(),
        "screen_type": phone.screen_type,
        "screen_refresh": phone.screen_refresh,
        "camera_main": phone.camera_main,
        "charging_wired": phone.charging_wired,
        "charging_wireless": phone.charging_wireless,
        "features": phone.features,
        "suitable_for": phone.suitable_for,
    }


def fill_tags(dry_run: bool = False, limit: int = 0) -> dict:
    """
    为数据库中的手机自动填充标签

    Args:
        dry_run: 预览模式，不实际写入数据库
        limit: 限制处理的手机数量，0 表示不限制

    Returns:
        统计信息字典
    """
    session = get_db_session()

    # 查询所有手机
    query = session.query(Phone)
    if limit > 0:
        query = query.limit(limit)

    phones = query.all()

    stats = {
        "total": len(phones),
        "updated": 0,
        "skipped": 0,
        "features_added": 0,
        "suitable_for_added": 0,
        "details": []
    }

    for phone in phones:
        phone_data = phone_to_dict(phone)

        # 匹配特性标签
        feature_tags = find_matching_feature_tags(phone_data)

        # 匹配适用人群标签
        suitable_for_tags = find_matching_suitable_for_tags(phone_data)

        # 检查是否需要更新
        existing_features = json.loads(phone.features) if phone.features else []
        existing_suitable_for = json.loads(phone.suitable_for) if phone.suitable_for else []

        # 合并现有标签和新标签
        new_features = list(set(existing_features + feature_tags))
        new_suitable_for = list(set(existing_suitable_for + suitable_for_tags))

        # 统计新增标签
        features_added = len(new_features) - len(existing_features)
        suitable_for_added = len(new_suitable_for) - len(existing_suitable_for)

        if features_added > 0 or suitable_for_added > 0:
            stats["updated"] += 1
            stats["features_added"] += features_added
            stats["suitable_for_added"] += suitable_for_added

            if not dry_run:
                # 更新数据库
                phone.features = json.dumps(new_features, ensure_ascii=False)
                phone.suitable_for = json.dumps(new_suitable_for, ensure_ascii=False)

            stats["details"].append({
                "model": phone.model,
                "brand": phone.brand,
                "features_added": feature_tags,
                "suitable_for_added": suitable_for_tags
            })
        else:
            stats["skipped"] += 1

    if not dry_run:
        session.commit()

    session.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="手机标签自动填充脚本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际写入数据库")
    parser.add_argument("--limit", type=int, default=0, help="限制处理的手机数量，0 表示不限制")
    parser.add_argument("--stats", action="store_true", help="显示标签库统计信息")
    args = parser.parse_args()

    if args.stats:
        print("=== 标签库统计 ===")
        tag_stats = get_tag_statistics()
        print(f"特性标签数量: {tag_stats['feature_tags_count']}")
        print(f"适用人群标签数量: {tag_stats['suitable_for_tags_count']}")
        print(f"\n特性标签: {', '.join(tag_stats['feature_tags'])}")
        print(f"\n适用人群标签: {', '.join(tag_stats['suitable_for_tags'])}")
        return

    print("=== 手机标签自动填充 ===")
    print(f"模式: {'预览' if args.dry_run else '实际写入'}")
    print(f"限制: {'无限制' if args.limit == 0 else f'{args.limit} 条'}")
    print()

    stats = fill_tags(dry_run=args.dry_run, limit=args.limit)

    print(f"处理总数: {stats['total']}")
    print(f"更新数量: {stats['updated']}")
    print(f"跳过数量: {stats['skipped']}")
    print(f"新增特性标签: {stats['features_added']}")
    print(f"新增适用人群标签: {stats['suitable_for_added']}")

    if stats['details']:
        print("\n=== 更新详情（前10条）===")
        for detail in stats['details'][:10]:
            print(f"\n{detail['brand']} {detail['model']}")
            if detail['features_added']:
                print(f"  新增特性: {', '.join(detail['features_added'])}")
            if detail['suitable_for_added']:
                print(f"  新增适用人群: {', '.join(detail['suitable_for_added'])}")


if __name__ == "__main__":
    main()

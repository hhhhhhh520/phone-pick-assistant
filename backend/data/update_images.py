"""
数据库图片URL迁移脚本
更新 phones 表的 image_url 字段

运行方式:
  python -m backend.data.update_images           # 执行更新
  python -m backend.data.update_images --dry-run  # 仅显示变更预览
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models.domain import SessionLocal, Phone

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def load_image_mappings(mappings_file: str) -> Dict[str, Dict[str, Any]]:
    """
    加载图片映射文件

    Args:
        mappings_file: 映射文件路径

    Returns:
        图片映射字典，键为 "brand model" 格式
    """
    with open(mappings_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    mappings = data.get("mappings", {})
    logger.info(f"加载映射文件: {mappings_file}")
    logger.info(f"映射条目数: {len(mappings)}")

    stats = data.get("statistics", {})
    logger.info(f"统计: 官方URL {stats.get('with_official_url', 0)} 个, "
                f"本地图片 {stats.get('with_local_path', 0)} 个, "
                f"无图片 {stats.get('placeholder', 0)} 个")

    return mappings


def get_image_url_from_mapping(
    mappings: Dict[str, Dict[str, Any]],
    brand: str,
    model: str
) -> Optional[str]:
    """
    从映射中获取图片URL

    Args:
        mappings: 图片映射字典
        brand: 品牌名
        model: 型号名

    Returns:
        图片URL，无图片返回 None
    """
    key = f"{brand} {model}"
    if key in mappings:
        mapping = mappings[key]
        url = mapping.get("url")
        source = mapping.get("source", "unknown")
        # placeholder 类型的 url 为 null，不更新
        if source == "placeholder":
            return None
        return url
    return None


def update_image_urls(dry_run: bool = False) -> Dict[str, int]:
    """
    更新数据库中的图片URL

    Args:
        dry_run: True 表示仅预览变更，不实际执行

    Returns:
        更新统计信息
    """
    # 映射文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mappings_file = os.path.join(script_dir, "phone_images.json")

    if not os.path.exists(mappings_file):
        logger.error(f"映射文件不存在: {mappings_file}")
        return {"error": "映射文件不存在"}

    # 加载映射
    mappings = load_image_mappings(mappings_file)

    # 统计信息
    stats = {
        "total_phones": 0,
        "updated": 0,
        "unchanged": 0,
        "no_mapping": 0,
        "placeholder": 0,
        "errors": 0
    }

    db = SessionLocal()

    try:
        # 获取所有手机
        phones = db.query(Phone).all()
        stats["total_phones"] = len(phones)
        logger.info(f"数据库中共有 {len(phones)} 款手机")

        changes = []  # 记录变更详情

        for phone in phones:
            brand = phone.brand
            model = phone.model
            current_url = phone.image_url

            # 获取新URL
            new_url = get_image_url_from_mapping(mappings, brand, model)

            if new_url is None:
                # 检查是否在映射中但标记为 placeholder
                key = f"{brand} {model}"
                if key in mappings and mappings[key].get("source") == "placeholder":
                    stats["placeholder"] += 1
                    logger.debug(f"[Placeholder] {brand} {model} - 无图片")
                else:
                    stats["no_mapping"] += 1
                    logger.warning(f"[No Mapping] {brand} {model} - 未找到映射")
                continue

            # 检查是否需要更新
            if current_url == new_url:
                stats["unchanged"] += 1
                logger.debug(f"[Unchanged] {brand} {model}")
                continue

            # 记录变更
            change_detail = {
                "brand": brand,
                "model": model,
                "old_url": current_url,
                "new_url": new_url,
                "source": mappings.get(f"{brand} {model}", {}).get("source", "unknown")
            }
            changes.append(change_detail)

            if dry_run:
                stats["updated"] += 1
                logger.info(f"[Dry-Run] {brand} {model}")
                logger.info(f"  旧值: {current_url}")
                logger.info(f"  新值: {new_url}")
            else:
                # 执行更新
                try:
                    phone.image_url = new_url
                    stats["updated"] += 1
                    logger.info(f"[Updated] {brand} {model}")
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"[Error] {brand} {model}: {e}")

        # 提交事务
        if not dry_run and stats["updated"] > 0:
            db.commit()
            logger.info("数据库更新已提交")
        elif dry_run:
            logger.info("Dry-run 模式，未执行实际更新")

        # 输出变更汇总
        if changes:
            logger.info("\n" + "=" * 60)
            logger.info("变更详情:")
            logger.info("=" * 60)
            for i, change in enumerate(changes, 1):
                logger.info(f"\n{i}. {change['brand']} {change['model']}")
                logger.info(f"   来源: {change['source']}")
                logger.info(f"   旧值: {change['old_url']}")
                logger.info(f"   新值: {change['new_url']}")

        return stats

    except Exception as e:
        logger.error(f"更新过程发生错误: {e}")
        db.rollback()
        stats["errors"] += 1
        return stats
    finally:
        db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="更新数据库中手机图片URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m backend.data.update_images           # 执行更新
  python -m backend.data.update_images --dry-run  # 仅显示变更预览
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示变更预览，不执行实际更新"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("手机图片URL迁移脚本")
    logger.info("=" * 60)
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"模式: {'预览模式 (dry-run)' if args.dry_run else '执行模式'}")
    logger.info("=" * 60)

    stats = update_image_urls(dry_run=args.dry_run)

    # 输出统计汇总
    logger.info("\n" + "=" * 60)
    logger.info("更新统计:")
    logger.info("=" * 60)
    logger.info(f"  总记录数: {stats.get('total_phones', 0)}")
    logger.info(f"  已更新: {stats.get('updated', 0)}")
    logger.info(f"  未变更: {stats.get('unchanged', 0)}")
    logger.info(f"  无映射: {stats.get('no_mapping', 0)}")
    logger.info(f"  占位符: {stats.get('placeholder', 0)}")
    logger.info(f"  错误数: {stats.get('errors', 0)}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("\n提示: 使用 --dry-run 参数仅预览变更，移除该参数以执行实际更新")


if __name__ == "__main__":
    main()

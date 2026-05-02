"""
手机图片映射加载器

提供图片URL查询功能，支持官方URL和本地图片路径
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

# 映射文件路径
MAPPING_FILE = Path(__file__).parent / "phone_images.json"

# 缓存映射数据
_mapping_cache: Optional[Dict[str, Any]] = None


def load_mappings() -> Dict[str, Any]:
    """加载图片映射数据（带缓存）"""
    global _mapping_cache
    if _mapping_cache is None:
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            _mapping_cache = json.load(f)
    return _mapping_cache


def get_image_url(brand: str, model: str) -> Optional[str]:
    """
    获取手机的图片URL

    Args:
        brand: 品牌，如 "Apple", "小米"
        model: 型号，如 "iPhone 15 Pro Max", "小米15"

    Returns:
        图片URL，如果无图片则返回 None
    """
    mappings = load_mappings()
    key = f"{brand} {model}"
    entry = mappings.get("mappings", {}).get(key)
    if entry:
        return entry.get("url")
    return None


def get_image_source(brand: str, model: str) -> str:
    """
    获取图片来源类型

    Args:
        brand: 品牌
        model: 型号

    Returns:
        来源类型: "official", "local", "placeholder"
    """
    mappings = load_mappings()
    key = f"{brand} {model}"
    entry = mappings.get("mappings", {}).get(key)
    if entry:
        return entry.get("source", "placeholder")
    return "placeholder"


def get_all_mappings() -> Dict[str, Dict[str, Any]]:
    """获取所有图片映射"""
    mappings = load_mappings()
    return mappings.get("mappings", {})


def get_statistics() -> Dict[str, int]:
    """获取映射统计信息"""
    mappings = load_mappings()
    return mappings.get("statistics", {})


def get_placeholder_url(brand: str, model: str) -> str:
    """
    生成占位符图片URL

    Args:
        brand: 品牌
        model: 型号

    Returns:
        占位符图片URL
    """
    # 使用品牌和型号首字母生成占位符
    text = f"{brand}+{model}".replace(" ", "+")
    return f"https://via.placeholder.com/200x200?text={text}"


if __name__ == "__main__":
    # 测试
    print("=== 图片映射统计 ===")
    stats = get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n=== 测试查询 ===")
    test_cases = [
        ("Apple", "iPhone 16 Pro Max"),
        ("小米", "小米15"),
        ("三星", "Galaxy S24 Ultra"),
        ("一加", "一加13"),
    ]
    for brand, model in test_cases:
        url = get_image_url(brand, model)
        source = get_image_source(brand, model)
        print(f"  {brand} {model}: {source} - {url or '(无图片)'}")

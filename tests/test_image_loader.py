"""
图片加载器测试
测试 get_image_url, get_image_source, get_all_mappings, get_statistics 等函数
"""
import pytest
from backend.data.image_loader import (
    get_image_url,
    get_image_source,
    get_all_mappings,
    get_statistics,
    get_placeholder_url,
    load_mappings,
)


class TestGetImageUrl:
    """获取图片URL测试"""

    def test_existing_phone_with_official_url(self):
        """存在官方URL的手机"""
        url = get_image_url("Apple", "iPhone 16 Pro Max")
        assert url is not None
        assert "apple.com" in url

    def test_existing_phone_with_local_url(self):
        """存在本地路径的手机"""
        url = get_image_url("小米", "小米15")
        assert url is not None
        assert url.startswith("/images/")

    def test_phone_with_placeholder(self):
        """使用占位符的手机（url为null）"""
        url = get_image_url("一加", "一加13")
        assert url is None

    def test_nonexistent_phone(self):
        """不存在的手机返回None"""
        url = get_image_url("不存在的品牌", "不存在的型号")
        assert url is None

    def test_case_sensitive(self):
        """品牌型号大小写敏感"""
        # 正确的大小写
        url1 = get_image_url("Apple", "iPhone 16")
        assert url1 is not None
        # 错误的大小写
        url2 = get_image_url("apple", "iphone 16")
        assert url2 is None

    def test_samsung_phone(self):
        """三星手机官方URL"""
        url = get_image_url("三星", "Galaxy S24 Ultra")
        assert url is not None
        assert "samsung.com" in url

    def test_huawei_phone(self):
        """华为手机本地路径"""
        url = get_image_url("华为", "Mate 70 Pro+")
        assert url is not None
        assert url.startswith("/images/")

    def test_vivo_phone(self):
        """vivo手机本地路径"""
        url = get_image_url("vivo", "X200 Pro")
        assert url is not None
        assert url.startswith("/images/")


class TestGetImageSource:
    """获取图片来源测试"""

    def test_official_source(self):
        """官方来源"""
        source = get_image_source("Apple", "iPhone 16 Pro")
        assert source == "official"

    def test_local_source(self):
        """本地来源"""
        source = get_image_source("小米", "小米15 Pro")
        assert source == "local"

    def test_placeholder_source(self):
        """占位符来源"""
        source = get_image_source("一加", "一加12")
        assert source == "placeholder"

    def test_nonexistent_phone(self):
        """不存在的手机返回placeholder"""
        source = get_image_source("不存在的品牌", "不存在的型号")
        assert source == "placeholder"

    def test_samsung_official(self):
        """三星官方来源"""
        source = get_image_source("三星", "Galaxy Z Fold6")
        assert source == "official"


class TestGetAllMappings:
    """获取所有映射测试"""

    def test_returns_dict(self):
        """返回字典"""
        mappings = get_all_mappings()
        assert isinstance(mappings, dict)

    def test_not_empty(self):
        """映射不为空"""
        mappings = get_all_mappings()
        assert len(mappings) > 0

    def test_contains_known_phones(self):
        """包含已知手机"""
        mappings = get_all_mappings()
        assert "Apple iPhone 16 Pro Max" in mappings
        assert "小米 小米15" in mappings

    def test_mapping_structure(self):
        """映射结构正确"""
        mappings = get_all_mappings()
        entry = mappings.get("Apple iPhone 16 Pro Max")
        assert "url" in entry
        assert "source" in entry


class TestGetStatistics:
    """获取统计信息测试"""

    def test_returns_dict(self):
        """返回字典"""
        stats = get_statistics()
        assert isinstance(stats, dict)

    def test_has_required_fields(self):
        """包含必需字段"""
        stats = get_statistics()
        assert "total_models" in stats
        assert "with_official_url" in stats
        assert "with_local_path" in stats
        assert "placeholder" in stats

    def test_statistics_values(self):
        """统计值正确"""
        stats = get_statistics()
        assert stats["total_models"] == 60
        assert stats["with_official_url"] == 11
        assert stats["with_local_path"] == 31
        assert stats["placeholder"] == 18

    def test_statistics_sum(self):
        """统计总和等于总数"""
        stats = get_statistics()
        total = stats["with_official_url"] + stats["with_local_path"] + stats["placeholder"]
        assert total == stats["total_models"]


class TestGetPlaceholderUrl:
    """生成占位符URL测试"""

    def test_returns_url(self):
        """返回URL字符串"""
        url = get_placeholder_url("Apple", "iPhone 16")
        assert isinstance(url, str)
        assert url.startswith("https://via.placeholder.com/")

    def test_contains_brand_and_model(self):
        """URL包含品牌和型号"""
        url = get_placeholder_url("小米", "小米15")
        assert "小米" in url
        assert "小米15" in url

    def test_space_replacement(self):
        """空格被替换为加号"""
        url = get_placeholder_url("Apple", "iPhone 16 Pro Max")
        # 品牌和型号之间的空格应该被替换
        assert "Apple+iPhone" in url or "Apple+iPhone+16+Pro+Max" in url

    def test_different_phones_different_url(self):
        """不同手机生成不同URL"""
        url1 = get_placeholder_url("Apple", "iPhone 16")
        url2 = get_placeholder_url("小米", "小米15")
        assert url1 != url2


class TestLoadMappings:
    """加载映射数据测试"""

    def test_returns_dict(self):
        """返回字典"""
        mappings = load_mappings()
        assert isinstance(mappings, dict)

    def test_has_mappings_key(self):
        """包含mappings键"""
        mappings = load_mappings()
        assert "mappings" in mappings

    def test_has_statistics_key(self):
        """包含statistics键"""
        mappings = load_mappings()
        assert "statistics" in mappings

    def test_caching(self):
        """缓存生效（多次调用返回同一对象）"""
        mappings1 = load_mappings()
        mappings2 = load_mappings()
        assert mappings1 is mappings2

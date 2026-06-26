"""
测试 _safe_battery_value 和 _safe_ram_value 函数处理混合类型的电池容量和内存数据
"""
import pytest
from backend.services.retrieval import _safe_battery_value, _safe_ram_value


class TestSafeBatteryValue:
    """测试安全电池数值提取"""

    def test_int_input(self):
        """整数输入应直接返回"""
        assert _safe_battery_value(5000) == 5000
        assert _safe_battery_value(0) == 0
        assert _safe_battery_value(10000) == 10000

    def test_none_input(self):
        """None 输入应返回 0"""
        assert _safe_battery_value(None) == 0

    def test_string_with_mah(self):
        """带 mAh 后缀的字符串应正确解析"""
        assert _safe_battery_value("5000mAh") == 5000
        assert _safe_battery_value("6000mAh") == 6000
        assert _safe_battery_value("4500mAh") == 4500

    def test_string_with_chinese_suffix(self):
        """带中文后缀的字符串应正确解析"""
        assert _safe_battery_value("5000mAh（典型值）") == 5000
        assert _safe_battery_value("7000mAh泰国产") == 7000

    def test_string_numeric_only(self):
        """纯数字字符串应正确解析"""
        assert _safe_battery_value("5000") == 5000

    def test_invalid_string(self):
        """无效字符串应返回 0"""
        assert _safe_battery_value("unknown") == 0
        assert _safe_battery_value("") == 0

    def test_float_input(self):
        """浮点数输入应被处理"""
        # 浮点数目前返回 0（不是 int 也不是 str）
        assert _safe_battery_value(5000.5) == 0


class TestSafeRamValue:
    """测试安全内存数值提取"""

    def test_int_input(self):
        """整数输入应直接返回"""
        assert _safe_ram_value(8) == 8
        assert _safe_ram_value(0) == 0
        assert _safe_ram_value(16) == 16

    def test_none_input(self):
        """None 输入应返回 0"""
        assert _safe_ram_value(None) == 0

    def test_string_with_gb(self):
        """带 GB 后缀的字符串应正确解析"""
        assert _safe_ram_value("8GB") == 8
        assert _safe_ram_value("12GB") == 12
        assert _safe_ram_value("6GB") == 6

    def test_string_with_extra_text(self):
        """带额外描述的字符串应正确解析"""
        assert _safe_ram_value("8GB游戏专用") == 8
        assert _safe_ram_value("6GB游戏性能") == 6

    def test_string_numeric_only(self):
        """纯数字字符串应正确解析"""
        assert _safe_ram_value("8") == 8

    def test_invalid_string(self):
        """无效字符串应返回 0"""
        assert _safe_ram_value("unknown") == 0
        assert _safe_ram_value("") == 0

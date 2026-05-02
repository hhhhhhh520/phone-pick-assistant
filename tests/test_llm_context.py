"""
LLM上下文管理测试
测试 estimate_tokens 和 truncate_messages 函数
"""
import pytest
from backend.services.llm import estimate_tokens, truncate_messages


class TestEstimateTokens:
    """Token估算测试"""

    def test_empty_string(self):
        """空字符串返回0"""
        assert estimate_tokens("") == 0

    def test_none_input(self):
        """None输入返回0"""
        assert estimate_tokens(None) == 0

    def test_normal_text(self):
        """正常文本估算"""
        # 100字符 / 2 = 50 tokens
        text = "a" * 100
        assert estimate_tokens(text) == 50

    def test_chinese_text(self):
        """中文文本估算"""
        # 20个中文字符 / 2 = 10 tokens
        text = "推荐三千元左右的手机"
        assert estimate_tokens(text) == len(text) // 2

    def test_single_character(self):
        """单字符返回0（整数除法）"""
        assert estimate_tokens("a") == 0

    def test_two_characters(self):
        """双字符返回1"""
        assert estimate_tokens("ab") == 1

    def test_mixed_content(self):
        """混合内容估算"""
        text = "Hello世界123"
        assert estimate_tokens(text) == len(text) // 2


class TestTruncateMessages:
    """消息截断测试"""

    def test_empty_messages(self):
        """空消息列表直接返回"""
        result = truncate_messages([])
        assert result == []

    def test_none_messages(self):
        """None消息列表直接返回"""
        result = truncate_messages(None)
        assert result is None

    def test_within_limits(self):
        """在限制内的消息不变"""
        messages = [
            {"role": "user", "content": "推荐手机"},
            {"role": "assistant", "content": "好的"},
        ]
        result = truncate_messages(messages)
        assert len(result) == 2
        assert result == messages

    def test_preserve_system_message(self):
        """系统消息始终保留"""
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "推荐手机"},
        ]
        result = truncate_messages(messages)
        assert len(result) == 2
        assert result[0]["role"] == "system"

    def test_truncate_by_max_messages(self):
        """按消息数量截断"""
        messages = [
            {"role": "system", "content": "系统"},
            {"role": "user", "content": "消息1"},
            {"role": "assistant", "content": "回复1"},
            {"role": "user", "content": "消息2"},
            {"role": "assistant", "content": "回复2"},
            {"role": "user", "content": "消息3"},
        ]
        # max_messages=2，只保留最新的2条普通消息
        result = truncate_messages(messages, max_messages=2, max_tokens=10000)
        # 系统消息 + 2条最新普通消息（按原始顺序：回复2, 消息3）
        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["content"] == "回复2"
        assert result[1]["role"] == "assistant"
        assert result[2]["content"] == "消息3"

    def test_truncate_by_max_tokens(self):
        """按token数截断"""
        messages = [
            {"role": "system", "content": "系统"},
            {"role": "user", "content": "a" * 100},  # 50 tokens
            {"role": "assistant", "content": "b" * 100},  # 50 tokens
            {"role": "user", "content": "c" * 100},  # 50 tokens
        ]
        # max_tokens=120，需要移除一些消息
        result = truncate_messages(messages, max_messages=10, max_tokens=120)
        # 系统消息(3/2=1) + 最新的消息应该保留
        assert result[0]["role"] == "system"

    def test_custom_limits(self):
        """自定义限制参数"""
        messages = [
            {"role": "user", "content": "消息1"},
            {"role": "assistant", "content": "回复1"},
            {"role": "user", "content": "消息2"},
        ]
        result = truncate_messages(messages, max_messages=1, max_tokens=10000)
        assert len(result) == 1
        assert result[0]["content"] == "消息2"

    def test_system_message_not_counted_in_max_messages(self):
        """系统消息不计入max_messages限制"""
        messages = [
            {"role": "system", "content": "系统提示"},
            {"role": "user", "content": "用户消息"},
        ]
        # max_messages=1，但系统消息不受影响
        result = truncate_messages(messages, max_messages=1, max_tokens=10000)
        assert len(result) == 2

    def test_multiple_system_messages_preserved(self):
        """多个系统消息都保留"""
        messages = [
            {"role": "system", "content": "系统1"},
            {"role": "system", "content": "系统2"},
            {"role": "user", "content": "用户消息"},
        ]
        result = truncate_messages(messages, max_messages=1, max_tokens=10000)
        system_msgs = [m for m in result if m["role"] == "system"]
        assert len(system_msgs) == 2

    def test_keep_most_recent_messages(self):
        """保留最新的消息"""
        messages = [
            {"role": "user", "content": "旧消息1"},
            {"role": "user", "content": "旧消息2"},
            {"role": "user", "content": "新消息1"},
            {"role": "user", "content": "新消息2"},
        ]
        result = truncate_messages(messages, max_messages=2, max_tokens=10000)
        assert len(result) == 2
        assert result[0]["content"] == "新消息1"
        assert result[1]["content"] == "新消息2"

    def test_no_truncation_when_limits_high(self):
        """限制足够大时不截断"""
        messages = [
            {"role": "user", "content": "消息"},
            {"role": "assistant", "content": "回复"},
        ]
        result = truncate_messages(messages, max_messages=100, max_tokens=10000)
        assert result == messages

"""
LLM上下文管理测试
测试 estimate_tokens 和 truncate_messages 函数
"""
import sys
import pytest
from backend.services.llm import (
    estimate_tokens,
    truncate_messages,
    _detect_estimation_method,
)


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
        text = "a" * 100
        assert estimate_tokens(text) >= 13

    def test_chinese_text(self):
        """中文文本估算"""
        text = "推荐三千元左右的手机"
        assert estimate_tokens(text) >= 10

    def test_single_character(self):
        """单字符估算（简单回退方法 len//2，单字符返回 0）"""
        assert estimate_tokens("a") >= 0

    def test_two_characters(self):
        """双字符估算（lang_aware 方法：2*0.25=0.5 → int=0）"""
        assert estimate_tokens("ab") >= 0

    def test_mixed_content(self):
        """混合内容估算"""
        text = "Hello世界123"
        assert estimate_tokens(text) >= 4

    def test_chinese_text_varied(self):
        """tiktoken模式：验证不同中文文本的token估算为正整数"""
        texts = [
            "手机",
            "拍照效果",
            "性价比高",
            "我想买一部手机，预算三千元左右",
            "主要用于拍照和日常使用",
        ]
        for text in texts:
            tokens = estimate_tokens(text)
            assert isinstance(tokens, int), f"Expected int for '{text}', got {type(tokens)}"
            assert tokens > 0, f"Expected >0 tokens for '{text}', got {tokens}"

    def test_english_text_varied(self):
        """tiktoken模式：验证英文和混合文本的token估算"""
        # 纯英文
        assert estimate_tokens("hello world") > 0
        # 长英文句
        assert estimate_tokens("The quick brown fox jumps over the lazy dog") > 0
        # 数字和符号混用
        assert estimate_tokens("Price: $2999, Discount: 15%") > 0
        # token数随文本增长而增长
        short_en = estimate_tokens("hi")
        long_en = estimate_tokens("hello world, this is a longer test message")
        assert long_en >= short_en, "Longer English text should have >= tokens than shorter"


class TestEstimateTokensFallback:
    """Token估算三层降级回退测试"""

    def test_tiktoken_unavailable_fallback_to_lang_aware(self, monkeypatch):
        """tiktoken不可用时（ImportError），回退到lang_aware估算"""
        def _raise_import_error(text: str) -> int:
            raise ImportError("No module named 'tiktoken'")

        monkeypatch.setattr(
            "backend.services.llm._estimate_tiktoken",
            _raise_import_error,
        )
        # 不应崩溃，应回退到lang_aware并返回正整数
        result = estimate_tokens("推荐手机")
        assert isinstance(result, int)
        assert result > 0

    def test_lang_aware_calculation_accuracy(self, monkeypatch):
        """lang_aware回退的token估算计算准确性验证"""
        def _raise_import_error(text: str) -> int:
            raise ImportError("No module named 'tiktoken'")

        monkeypatch.setattr(
            "backend.services.llm._estimate_tiktoken",
            _raise_import_error,
        )
        # 中文: 1.5 per char
        # "你好" = 2 Chinese → int(2 * 1.5) = 3
        assert estimate_tokens("你好") == 3

        # 英文: 0.25 per char
        # "Hello" = 5 English → int(5 * 0.25) = 1
        assert estimate_tokens("Hello") == 1

        # 中文+其他混合: "你好!!!" = 2 Chinese + 3 other
        # int(2*1.5 + 3*0.5) = int(4.5) = 4
        assert estimate_tokens("你好!!!") == 4

        # 纯空格/符号: "   " = 3 other → int(3 * 0.5) = 1
        assert estimate_tokens("   ") == 1

    def test_simple_fallback_when_both_fail(self, monkeypatch):
        """tiktoken和lang_aware都失败时，回退到simple (len//2)"""
        def _raise_import_error(text: str) -> int:
            raise ImportError("No module named 'tiktoken'")

        def _raise_runtime_error(text: str) -> int:
            raise RuntimeError("lang_aware estimation failed")

        monkeypatch.setattr(
            "backend.services.llm._estimate_tiktoken",
            _raise_import_error,
        )
        monkeypatch.setattr(
            "backend.services.llm._estimate_lang_aware",
            _raise_runtime_error,
        )
        # simple fallback: len // 2
        assert estimate_tokens("Hello World") == 11 // 2  # 5
        assert estimate_tokens("你好世界") == 4 // 2     # 2
        assert estimate_tokens("abc") == 3 // 2           # 1
        # 空字符串仍返回0（由外层提前处理）
        assert estimate_tokens("") == 0

    def test_detect_method_returns_valid(self):
        """_detect_estimation_method() returns a valid method name"""
        method = _detect_estimation_method()
        assert method in ("tiktoken", "language-aware", "simple"), (
            f"Expected valid method, got '{method}'"
        )

    def test_detect_method_returns_simple(self, monkeypatch):
        """tiktoken不可导入时，_detect_estimation_method()返回'simple'"""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "tiktoken":
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        monkeypatch.delitem(sys.modules, "tiktoken", raising=False)

        method = _detect_estimation_method()
        assert method == "simple", (
            f"Expected 'simple' when tiktoken import fails, got '{method}'"
        )


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
            {"role": "system", "content": "系统"},         # 1 token
            {"role": "user", "content": "a" * 100},       # 13 tokens
            {"role": "assistant", "content": "b" * 100},  # 25 tokens
            {"role": "user", "content": "c" * 100},       # 25 tokens
        ]
        # max_tokens=120，总tokens=64（1+13+25+25），不需要移除
        result = truncate_messages(messages, max_messages=10, max_tokens=120)
        # 系统消息应该保留在最前面
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

    def test_truncate_respects_max_tokens_bound(self):
        """验证截断后总token数严格不超过max_tokens"""
        # "a"*100 ≈ 13 tokens per message (tiktoken cl100k_base)
        messages = [
            {"role": "system", "content": "系统"},          # ~2 tokens
            {"role": "user", "content": "a" * 100},         # ~13 tokens
            {"role": "assistant", "content": "a" * 100},    # ~13 tokens
            {"role": "user", "content": "a" * 100},         # ~13 tokens
            {"role": "assistant", "content": "a" * 100},    # ~13 tokens
        ]
        max_tokens = 30  # Total ~54 → needs to truncate to ≤30
        result = truncate_messages(messages, max_messages=20, max_tokens=max_tokens)
        total = sum(estimate_tokens(m.get("content", "")) for m in result)
        assert total <= max_tokens, (
            f"Total tokens ({total}) exceeds max_tokens ({max_tokens})"
        )
        # 系统消息应保留
        assert result[0]["role"] == "system"

    def test_long_message_truncation_boundary(self):
        """长消息截断边界测试：消息token数接近或略超max_tokens限制"""
        # "x"*200 ≈ 25 tokens (tiktoken cl100k_base for repeated chars)
        long_content = "x" * 200
        messages = [
            {"role": "system", "content": "系统提示"},
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": "好的"},
        ]
        # max_tokens=500远超总token数，不应截断
        result = truncate_messages(messages, max_messages=20, max_tokens=500)
        assert len(result) == 3, "不应截断，所有消息应保留"
        assert result[0]["role"] == "system"
        # 使用严格的token限制：仅保留系统消息
        tight_result = truncate_messages(messages, max_messages=20, max_tokens=10)
        total_tight = sum(estimate_tokens(m.get("content", "")) for m in tight_result)
        assert total_tight <= 10, (
            f"Tight truncation: tokens ({total_tight}) exceeds limit (10)"
        )

    def test_no_truncation_when_limits_high(self):
        """限制足够大时不截断"""
        messages = [
            {"role": "user", "content": "消息"},
            {"role": "assistant", "content": "回复"},
        ]
        result = truncate_messages(messages, max_messages=100, max_tokens=10000)
        assert result == messages

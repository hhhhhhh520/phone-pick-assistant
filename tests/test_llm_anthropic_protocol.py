"""
Anthropic 协议适配器测试（2026-09-06 接入火山方舟编程套餐）

覆盖：
- SSE 增量解析：只放行 text_delta，thinking_delta/事件行/脏行全部过滤
- system 消息拆分 + 相邻同角色消息合并（Anthropic 协议要求）
- 请求负载构建
- openai / anthropic 协议分发
- 配置字段迁移（deepseek_* -> llm_*）
"""
import json
from unittest.mock import patch

import pytest

from backend.services.llm import (
    LLMService,
    extract_anthropic_text_delta,
)

# conftest 的 offline_llm autouse fixture 会类级替换 chat_stream；
# 在导入期（patch 生效前）捕获真实实现供分发测试用
_REAL_CHAT_STREAM = LLMService.chat_stream


class TestAnthropicSseParsing:
    """extract_anthropic_text_delta：从 data 行提取正文增量"""

    def test_text_delta_extracted(self):
        line = 'data: {"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":"你好"}}'
        assert extract_anthropic_text_delta(line) == "你好"

    def test_thinking_delta_filtered(self):
        line = 'data: {"type":"content_block_delta","index":0,"delta":{"type":"thinking_delta","thinking":"嗯，用户"}}'
        assert extract_anthropic_text_delta(line) is None

    def test_non_delta_events_filtered(self):
        assert extract_anthropic_text_delta('data: {"type":"message_start","message":{}}') is None
        assert extract_anthropic_text_delta('data: {"type":"content_block_start","index":0}') is None
        assert extract_anthropic_text_delta('data: {"type":"message_stop"}') is None

    def test_non_data_line_ignored(self):
        assert extract_anthropic_text_delta("event: content_block_delta") is None
        assert extract_anthropic_text_delta("") is None

    def test_malformed_json_ignored(self):
        assert extract_anthropic_text_delta("data: {broken json") is None

    def test_empty_text_returns_none(self):
        line = 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":""}}'
        assert extract_anthropic_text_delta(line) is None


class TestAnthropicMessageBuilding:
    """system 拆分 + 相邻同角色合并 + 负载构建"""

    def test_system_extracted_to_top_level(self):
        messages = [
            {"role": "system", "content": "你是手机选购顾问"},
            {"role": "user", "content": "推荐手机"},
        ]
        payload = LLMService._build_anthropic_payload(messages, 2048, 0.7, "m", False)
        assert payload["system"] == "你是手机选购顾问"
        assert all(m["role"] != "system" for m in payload["messages"])
        assert payload["messages"] == [{"role": "user", "content": "推荐手机"}]

    def test_consecutive_same_role_merged(self):
        """相邻同角色消息必须合并（首轮：历史里的 user 原话 + 追加的 user prompt）"""
        messages = [
            {"role": "user", "content": "推荐手机"},
            {"role": "user", "content": "用户需求: 预算3000"},
            {"role": "assistant", "content": "好的"},
            {"role": "user", "content": "补充说明"},
        ]
        system, merged = LLMService._split_system_messages(messages)
        assert system is None
        assert len(merged) == 3
        # 前两条 user 合并，且顺序保留
        assert merged[0]["role"] == "user"
        assert merged[0]["content"] == "推荐手机\n\n用户需求: 预算3000"
        assert merged[1] == {"role": "assistant", "content": "好的"}
        assert merged[2] == {"role": "user", "content": "补充说明"}

    def test_multiple_system_messages_joined(self):
        messages = [
            {"role": "system", "content": "A"},
            {"role": "system", "content": "B"},
            {"role": "user", "content": "hi"},
        ]
        payload = LLMService._build_anthropic_payload(messages, 2048, 0.7, "m", True)
        assert payload["system"] == "A\n\nB"

    def test_payload_required_fields(self):
        messages = [{"role": "user", "content": "hi"}]
        payload = LLMService._build_anthropic_payload(messages, 4096, 0.7, "ark-code-latest", True)
        assert payload["model"] == "ark-code-latest"
        assert payload["max_tokens"] == 4096
        assert payload["temperature"] == 0.7
        assert payload["stream"] is True
        assert payload["messages"] == messages


@pytest.mark.asyncio
class TestProtocolDispatch:
    """chat_stream 按协议分发（绕过 offline_llm 全局补丁，用导入期捕获的真实实现）"""

    async def _run(self, protocol: str) -> str:
        svc = LLMService()
        svc.protocol = protocol

        async def fake_anthropic(messages):
            yield "from-anthropic"

        async def fake_openai(messages):
            yield "from-openai"

        with patch.object(LLMService, "chat_stream", _REAL_CHAT_STREAM), \
             patch.object(svc, "_chat_stream_anthropic", fake_anthropic), \
             patch.object(svc, "_chat_stream_openai", fake_openai):
            chunks = [c async for c in svc.chat_stream([{"role": "user", "content": "hi"}])]
        return "".join(chunks)

    async def test_anthropic_dispatch(self):
        assert await self._run("anthropic") == "from-anthropic"

    async def test_openai_dispatch(self):
        assert await self._run("openai") == "from-openai"


class TestConfigFieldMigration:
    """配置字段 deepseek_* -> llm_*"""

    def test_new_fields_present(self):
        from backend.config import Settings

        assert "llm_api_key" in Settings.model_fields
        assert "llm_base_url" in Settings.model_fields
        assert "llm_api_protocol" in Settings.model_fields

    def test_old_fields_removed(self):
        from backend.config import Settings

        assert "deepseek_api_key" not in Settings.model_fields
        assert "deepseek_base_url" not in Settings.model_fields

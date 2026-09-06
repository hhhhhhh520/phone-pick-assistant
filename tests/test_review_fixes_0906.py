"""
2026-09-06 审查修复针对性测试

覆盖本轮修复的行为：
- 修复A: intent LLM 网络错误走规则兜底（此前 LLM 不可达时 /api/chat 直接 503）
- 修复B: 红米品牌独立映射（此前兜底路径把红米映射成小米，丢失全部红米机型）
- 修复C: INTENT_PROMPT 预算示例值与规则一致（此前示例 10000 会被 LLM 照抄，
         未提预算的用户被静默过滤掉万元以上机型）
- 修复D: /api/phones 限流 60/min
- 修复E: sqlite URL 锚定项目根（防止错误 CWD 启动静默新建空库）+ 死配置移除
- 修复F: retrieval.py 孤儿死代码清理
"""
import asyncio
import os
from unittest.mock import patch

import pytest

from tests.conftest import _parse_sse_response


# ============================================================================
# 修复A: intent LLM 网络错误兜底
# ============================================================================

class TestIntentNetworkFallback:
    """LLM 不可达时意图识别降级到规则兜底，而不是抛异常"""

    def test_llm_error_falls_back_to_rules(self):
        """chat_stream 抛 LLMError 时返回规则兜底结果（autouse offline_llm 已注入失败）"""
        from backend.services.intent import IntentService

        service = IntentService()
        result = asyncio.run(service.recognize("预算三千，玩游戏用的手机"))

        assert result.budget_min == 2500
        assert result.budget_max == 3500
        assert "游戏" in result.features

    def test_any_llm_exception_falls_back(self):
        """非 LLMError 的异常（如 httpx 连接错误）同样兜底"""
        from backend.services.intent import IntentService

        service = IntentService()
        with patch.object(service.llm, "chat", side_effect=RuntimeError("connection boom")):
            result = asyncio.run(service.recognize("预算三千，玩游戏用的手机"))

        assert result.budget_max == 3500
        assert "游戏" in result.features

    def test_chat_route_returns_200_when_llm_down(self, client):
        """LLM 全挂时 /api/chat 仍是 200 SSE（规则兜底），不再 503"""
        response = client.post("/api/chat", json={"message": "预算三千，玩游戏用的手机"})
        assert response.status_code == 200

        events = _parse_sse_response(response.text)
        assert "session" in events
        assert events.get("intent") == "recommend"
        assert "done" in events


# ============================================================================
# 修复B: 红米品牌独立映射
# ============================================================================

class TestRedmiBrandMapping:
    """规则兜底的品牌提取：红米不再合并进小米"""

    def test_redmi_mapped_to_redmi(self):
        from backend.services.intent import IntentService

        service = IntentService()
        assert service._extract_brands("推荐红米手机") == ["红米"]

    def test_xiaomi_and_redmi_both_extracted(self):
        from backend.services.intent import IntentService

        service = IntentService()
        brands = service._extract_brands("小米和红米哪个好")
        assert set(brands) == {"小米", "红米"}

    def test_redmi_brand_search_finds_redmi_phones(self):
        """端到端：规则兜底识别"红米"后，检索能命中数据库里的红米机型"""
        from backend.models.schemas import IntentResult, IntentType
        from backend.services.retrieval import RetrievalService
        from backend.services.intent import IntentService
        from backend.api.dependencies import get_db

        service = IntentService()
        brands = service._extract_brands("推荐红米手机")
        assert brands == ["红米"]

        db = next(get_db())
        retrieval = RetrievalService(db)
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0, budget_max=100000,
            brands=brands, features=[], no_need_features=[],
            phones_mentioned=[], reset_profile=False,
        )
        phones = retrieval.search(intent, limit=5)
        assert len(phones) > 0
        assert all(p.brand == "红米" for p in phones)


# ============================================================================
# 修复C: INTENT_PROMPT 预算示例值
# ============================================================================

class TestIntentPromptBudgetExample:
    """Prompt 示例值必须与"无预算保持 100000"的规则一致，避免 LLM 照抄示例"""

    def test_budget_example_is_unbounded(self):
        from backend.services.intent import INTENT_PROMPT

        assert '"budget_max": 100000' in INTENT_PROMPT


# ============================================================================
# 修复D: /api/phones 限流
# ============================================================================

class TestPhonesRateLimit:
    """列表/详情 60/min 限流，防止全库爬取"""

    def test_list_rate_limited_after_60(self, client):
        for _ in range(60):
            assert client.get("/api/phones").status_code == 200
        assert client.get("/api/phones").status_code == 429

    def test_detail_rate_limited_after_60(self, client):
        for _ in range(60):
            client.get("/api/phones/1")
        assert client.get("/api/phones/1").status_code == 429


# ============================================================================
# 修复E: sqlite URL 锚定项目根 + 死配置移除
# ============================================================================

class TestDatabaseUrlNormalization:
    """相对 sqlite 路径锚定到项目根，与启动 CWD 无关"""

    def test_relative_url_anchored_to_project_root(self):
        from backend.config import _normalize_sqlite_url

        url = _normalize_sqlite_url("sqlite:///backend/data/phones.db")
        path = url[len("sqlite:///"):]
        assert os.path.isabs(path)
        assert path.replace("\\", "/").endswith("backend/data/phones.db")

    def test_memory_url_untouched(self):
        from backend.config import _normalize_sqlite_url

        assert _normalize_sqlite_url("sqlite:///:memory:") == "sqlite:///:memory:"

    def test_absolute_url_untouched(self):
        from backend.config import _normalize_sqlite_url

        assert _normalize_sqlite_url("sqlite:////abs/path.db") == "sqlite:////abs/path.db"
        assert _normalize_sqlite_url("postgresql://host/db") == "postgresql://host/db"

    def test_settings_database_url_is_absolute(self):
        from backend.config import get_settings

        url = get_settings().database_url
        assert url.startswith("sqlite:///")
        assert os.path.isabs(url[len("sqlite:///"):])

    def test_dead_config_field_removed(self):
        """max_message_length 从未被引用且与 security 的 2000 矛盾，已移除"""
        from backend.config import Settings

        assert "max_message_length" not in Settings.model_fields


# ============================================================================
# 修复F: retrieval.py 死代码清理
# ============================================================================

class TestRetrievalDeadCodeRemoved:
    """孤儿代码（无 def 的 get_all_phones 方法体）已删除"""

    def test_get_all_phones_gone(self):
        from backend.services.retrieval import RetrievalService

        assert not hasattr(RetrievalService, "get_all_phones")

    def test_search_with_fallback_still_works(self):
        """删除死代码后分级回退检索行为不变"""
        from backend.models.schemas import IntentResult, IntentType
        from backend.services.retrieval import RetrievalService
        from backend.api.dependencies import get_db

        db = next(get_db())
        retrieval = RetrievalService(db)
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0, budget_max=100000,
            brands=[], features=[], no_need_features=[],
            phones_mentioned=[], reset_profile=False,
        )
        phones, notice = retrieval.search_with_fallback(intent, limit=5)
        assert len(phones) == 5
        assert notice is None

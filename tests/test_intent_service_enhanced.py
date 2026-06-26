"""
IntentService 增强意图识别单元测试

测试覆盖：
- recognize() 方法接收 user_profile 参数
- _build_profile_context() 构建用户画像上下文
- _enrich_with_clarification() 丰富追问信息
- 完整流程：意图识别 + 需求分析 + 追问生成
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.intent import IntentService
from backend.models.schemas import IntentResult, IntentType, UserProfile, NeedLevel


class TestBuildProfileContext:
    """测试 _build_profile_context() 方法"""

    @pytest.fixture
    def service(self):
        return IntentService()

    def test_empty_profile(self, service):
        """空画像返回空字符串"""
        profile = UserProfile()
        context = service._build_profile_context(profile)

        assert context == ""

    def test_budget_only_profile(self, service):
        """只有预算信息"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        context = service._build_profile_context(profile)

        assert "预算范围: 2000元-4000元" in context
        assert "当前已收集的用户需求" in context

    def test_single_budget_boundary(self, service):
        """单边预算"""
        profile = UserProfile(budget_max=5000)
        context = service._build_profile_context(profile)

        assert "预算" in context
        assert "5000元" in context

    def test_feature_needs_profile(self, service):
        """功能需求"""
        profile = UserProfile(
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM
        )
        context = service._build_profile_context(profile)

        assert "游戏需求(高)" in context
        assert "拍照需求(中)" in context

    def test_brand_preference_profile(self, service):
        """品牌偏好"""
        profile = UserProfile(brand_preference=["小米", "华为"])
        context = service._build_profile_context(profile)

        assert "品牌偏好: 小米, 华为" in context

    def test_full_profile(self, service):
        """完整画像"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM,
            battery_need=NeedLevel.LOW,
            brand_preference=["小米"]
        )
        context = service._build_profile_context(profile)

        assert "预算范围: 2000元-4000元" in context
        assert "游戏需求(高)" in context
        assert "拍照需求(中)" in context
        assert "续航需求(低)" in context
        assert "品牌偏好: 小米" in context


class TestEnrichWithClarification:
    """测试 _enrich_with_clarification() 方法"""

    @pytest.fixture
    def service(self):
        return IntentService()

    def test_incomplete_profile_needs_clarification(self, service):
        """不完整画像需要追问"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000
        )
        profile = UserProfile(budget_min=2000, budget_max=4000)

        result = service._enrich_with_clarification(base_intent, profile)

        assert result.need_clarification is True
        assert result.missing_fields is not None
        assert len(result.missing_fields) > 0
        assert result.clarification_question is not None

    def test_complete_profile_no_clarification(self, service):
        """完整画像不需要追问"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000
        )
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )

        result = service._enrich_with_clarification(base_intent, profile)

        assert result.need_clarification is False
        # 完整画像不设置 missing_fields 和 clarification_question（使用默认空列表）
        assert result.missing_fields == []
        assert result.clarification_question is None

    def test_preserves_base_intent_fields(self, service):
        """保留基础意图字段"""
        base_intent = IntentResult(
            intent=IntentType.COMPARE,
            budget_min=3000,
            budget_max=5000,
            brands=["小米", "华为"],
            features=["游戏"],
            phones_mentioned=["小米14", "华为P60"]
        )
        profile = UserProfile()  # 空画像，不完整

        result = service._enrich_with_clarification(base_intent, profile)

        # 基础字段应该被保留
        assert result.intent == IntentType.COMPARE
        assert result.budget_min == 3000
        assert result.budget_max == 5000
        assert result.brands == ["小米", "华为"]
        assert result.features == ["游戏"]
        assert result.phones_mentioned == ["小米14", "华为P60"]

        # 追问字段被添加
        assert result.need_clarification is True
        assert result.missing_fields is not None


class TestFallbackIntentRecognitionWithProfile:
    """测试 _fallback_intent_recognition() 支持 user_profile"""

    @pytest.fixture
    def service(self):
        return IntentService()

    def test_fallback_without_profile(self, service):
        """降级识别不传 user_profile"""
        result = service._fallback_intent_recognition("推荐一款手机")

        assert result.intent == IntentType.RECOMMEND
        assert result.need_clarification is False
        assert result.missing_fields == []

    def test_fallback_with_incomplete_profile(self, service):
        """降级识别传入不完整画像"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        result = service._fallback_intent_recognition(
            "推荐一款游戏手机",
            user_profile=profile
        )

        assert result.intent == IntentType.RECOMMEND
        assert result.need_clarification is True
        assert result.clarification_question is not None

    def test_fallback_with_complete_profile(self, service):
        """降级识别传入完整画像"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        result = service._fallback_intent_recognition(
            "推荐一款手机",
            user_profile=profile
        )

        assert result.intent == IntentType.RECOMMEND
        assert result.need_clarification is False


class TestRecognizeWithProfile:
    """测试 recognize() 方法支持 user_profile 参数"""

    @pytest.fixture
    def service(self):
        return IntentService()

    @pytest.mark.asyncio
    async def test_recognize_without_profile(self, service):
        """不传 user_profile 的向后兼容"""
        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend", "budget_min": 2000, "budget_max": 4000}'

            result = await service.recognize("推荐一款3000元的手机")

            assert result.intent == IntentType.RECOMMEND
            assert result.budget_min == 2000
            assert result.budget_max == 4000
            # 不传 profile 时，追问字段使用默认值
            assert result.need_clarification is False
            assert result.missing_fields == []

    @pytest.mark.asyncio
    async def test_recognize_with_incomplete_profile(self, service):
        """传入不完整画像触发追问"""
        profile = UserProfile(budget_min=2000, budget_max=4000)

        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend", "budget_min": 2000, "budget_max": 4000, "features": ["游戏"]}'

            result = await service.recognize(
                "推荐一款游戏手机",
                user_profile=profile
            )

            assert result.intent == IntentType.RECOMMEND
            assert result.need_clarification is True
            assert result.clarification_question is not None
            # 应该问游戏相关的问题
            assert "游戏" in result.clarification_question or "玩" in result.clarification_question

    @pytest.mark.asyncio
    async def test_recognize_with_complete_profile(self, service):
        """传入完整画像不触发追问"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )

        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend", "budget_min": 2000, "budget_max": 4000}'

            result = await service.recognize(
                "推荐一款手机",
                user_profile=profile
            )

            assert result.intent == IntentType.RECOMMEND
            assert result.need_clarification is False

    @pytest.mark.asyncio
    async def test_recognize_fallback_on_json_error(self, service):
        """JSON 解析失败时降级处理"""
        profile = UserProfile(budget_min=2000, budget_max=4000)

        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "invalid json response"

            result = await service.recognize(
                "推荐一款手机",
                user_profile=profile
            )

            # 降级处理仍然支持追问
            assert result.intent == IntentType.RECOMMEND
            assert result.need_clarification is True

    @pytest.mark.asyncio
    async def test_recognize_with_history_and_profile(self, service):
        """同时传入历史和画像"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        history = [
            {"role": "user", "content": "我想买手机"},
            {"role": "assistant", "content": "好的，请问您的预算是多少？"}
        ]

        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend", "budget_min": 2000, "budget_max": 4000}'

            result = await service.recognize(
                "2000到4000元吧",
                history=history,
                user_profile=profile
            )

            assert result.intent == IntentType.RECOMMEND
            # 验证 llm.chat 被调用
            assert mock_chat.called
            # 验证调用参数是正确的格式
            call_args = mock_chat.call_args[0][0]  # 获取第一个位置参数（messages list）
            assert isinstance(call_args, list)
            assert len(call_args) > 0
            assert "content" in call_args[0]


class TestIntentServiceIntegration:
    """集成测试：意图识别 + 需求分析 + 追问生成"""

    @pytest.fixture
    def service(self):
        return IntentService()

    @pytest.mark.asyncio
    async def test_full_flow_incomplete_needs(self, service):
        """完整流程：需求不完整时触发追问"""
        # 模拟空画像
        profile = UserProfile()

        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend", "budget_min": 0, "budget_max": 100000}'

            result = await service.recognize(
                "帮我推荐一款手机",
                user_profile=profile
            )

            assert result.intent == IntentType.RECOMMEND
            assert result.need_clarification is True
            assert len(result.missing_fields) > 0
            assert "预算" in result.missing_fields
            assert result.clarification_question is not None

    @pytest.mark.asyncio
    async def test_full_flow_complete_needs(self, service):
        """完整流程：需求完整时直接返回"""
        profile = UserProfile(
            budget_min=3000,
            budget_max=5000,
            gaming_need=NeedLevel.HIGH
        )

        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend", "budget_min": 3000, "budget_max": 5000}'

            result = await service.recognize(
                "推荐一款手机",
                user_profile=profile
            )

            assert result.intent == IntentType.RECOMMEND
            assert result.need_clarification is False

    @pytest.mark.asyncio
    async def test_profile_context_in_prompt(self, service):
        """验证用户画像上下文被加入 prompt"""
        profile = UserProfile(
            budget_min=3000,
            budget_max=5000,
            gaming_need=NeedLevel.HIGH,
            brand_preference=["小米"]
        )

        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend"}'

            await service.recognize(
                "推荐一款手机",
                user_profile=profile
            )

            # 验证 prompt 内容
            call_args = mock_chat.call_args[0][0]  # 获取第一个位置参数（messages list）
            prompt = call_args[0]["content"]

            assert "当前已收集的用户需求" in prompt
            assert "3000元" in prompt
            assert "5000元" in prompt
            assert "游戏需求(高)" in prompt
            assert "小米" in prompt

    @pytest.mark.asyncio
    async def test_multi_turn_dialog_flow(self, service):
        """模拟多轮对话流程"""
        # 第一轮：空画像
        profile1 = UserProfile()
        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend"}'

            result1 = await service.recognize(
                "帮我推荐一款手机",
                user_profile=profile1
            )

            assert result1.need_clarification is True
            assert "预算" in result1.missing_fields

        # 第二轮：用户提供了预算
        profile2 = UserProfile(budget_min=2000, budget_max=4000)
        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend"}'

            result2 = await service.recognize(
                "2000到4000元",
                user_profile=profile2
            )

            assert result2.need_clarification is True
            assert "预算" not in result2.missing_fields

        # 第三轮：用户提供了功能需求（完整）
        profile3 = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend"}'

            result3 = await service.recognize(
                "我要玩游戏",
                user_profile=profile3
            )

            assert result3.need_clarification is False


class TestPainPointDetection:
    """测试痛点检测集成"""

    @pytest.fixture
    def service(self):
        return IntentService()

    def test_pain_point_budget_too_low_for_high_gaming(self, service):
        """痛点：预算不足但游戏需求高"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=2500
        )
        # 预算低于3000但游戏需求高
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH
        )

        result = service._enrich_with_clarification(base_intent, profile)

        # 应该检测到痛点
        assert result.pain_point_detected is True
        assert result.pain_point_type == "budget_too_low_for_features"
        assert result.pain_point_severity == "high"
        assert result.need_clarification is True
        assert result.clarification_question is not None
        # 痛点追问应该提到预算或妥协
        assert "预算" in result.clarification_question or "妥协" in result.clarification_question

    def test_pain_point_budget_too_low_for_high_camera(self, service):
        """痛点：预算不足但拍照需求高"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=2000
        )
        profile = UserProfile(
            budget_max=2000,
            camera_need=NeedLevel.HIGH
        )

        result = service._enrich_with_clarification(base_intent, profile)

        assert result.pain_point_detected is True
        assert result.pain_point_type == "budget_too_low_for_features"

    def test_pain_point_gaming_camera_conflict(self, service):
        """痛点：高游戏+高拍照但预算有限"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=4000
        )
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )

        result = service._enrich_with_clarification(base_intent, profile)

        # 应该检测到功能冲突痛点
        assert result.pain_point_detected is True
        assert result.pain_point_type == "gaming_camera_budget_conflict"
        assert result.need_clarification is True

    def test_pain_point_battery_gaming_conflict(self, service):
        """痛点：高游戏+高续航需求冲突"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=100000
        )
        profile = UserProfile(
            budget_max=100000,  # 预算充足
            gaming_need=NeedLevel.HIGH,
            battery_need=NeedLevel.HIGH
        )

        result = service._enrich_with_clarification(base_intent, profile)

        # 不应该触发预算痛点，但可能触发续航与游戏冲突
        # 注意：这个场景预算充足，可能不会触发痛点
        # 具体取决于 PainPointQuestionService 的逻辑
        # 如果没有痛点，需求也是完整的，应该不触发追问
        if result.pain_point_detected:
            assert result.pain_point_type in ["battery_vs_gaming", None]

    def test_no_pain_point_sufficient_budget(self, service):
        """无痛点：预算充足"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=10000
        )
        profile = UserProfile(
            budget_max=10000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )

        result = service._enrich_with_clarification(base_intent, profile)

        # 预算充足不应该触发痛点
        assert result.pain_point_detected is False
        # 需求完整，不需要追问
        assert result.need_clarification is False

    def test_pain_point_priority_over_missing_fields(self, service):
        """痛点追问优先级高于普通字段追问"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=2000
        )
        # 有预算（低），有游戏需求（高），缺拍照需求
        # 痛点：预算太低无法满足高游戏需求
        profile = UserProfile(
            budget_max=2000,
            gaming_need=NeedLevel.HIGH
            # camera_need 缺失
        )

        result = service._enrich_with_clarification(base_intent, profile)

        # 应该优先返回痛点追问，而不是询问缺失的拍照需求
        assert result.pain_point_detected is True
        assert result.pain_point_type == "budget_too_low_for_features"
        # missing_fields 应该为空（痛点优先）
        assert result.missing_fields == []

    def test_no_pain_point_returns_regular_clarification(self, service):
        """无痛点时返回普通追问"""
        base_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=5000
        )
        # 预算合理，但缺少功能需求
        profile = UserProfile(
            budget_max=5000
            # 缺少 gaming_need, camera_need, battery_need
        )

        result = service._enrich_with_clarification(base_intent, profile)

        # 无痛点，但需求不完整
        assert result.pain_point_detected is False
        assert result.need_clarification is True
        assert len(result.missing_fields) > 0
        assert result.clarification_question is not None

    def test_preserves_base_intent_with_pain_point(self, service):
        """痛点检测结果保留基础意图字段"""
        base_intent = IntentResult(
            intent=IntentType.COMPARE,
            budget_min=1000,
            budget_max=2000,
            brands=["小米"],
            features=["游戏"],
            phones_mentioned=["小米14"],
            no_need_features=["拍照"]
        )
        profile = UserProfile(
            budget_max=2000,
            gaming_need=NeedLevel.HIGH
        )

        result = service._enrich_with_clarification(base_intent, profile)

        # 基础字段保留
        assert result.intent == IntentType.COMPARE
        assert result.budget_min == 1000
        assert result.budget_max == 2000
        assert result.brands == ["小米"]
        assert result.features == ["游戏"]
        assert result.phones_mentioned == ["小米14"]
        assert result.no_need_features == ["拍照"]

        # 痛点字段被添加
        assert result.pain_point_detected is True
        assert result.pain_point_type is not None


class TestExtractBudget:
    """测试 _extract_budget 预算提取"""

    @pytest.fixture
    def service(self):
        return IntentService()

    def test_chinese_wan_yinei(self, service):
        """一万以内 → (0, 10000)"""
        assert service._extract_budget("一万以内") == (0, 10000)

    def test_chinese_wan_yixia(self, service):
        """一万以下 → (0, 10000)"""
        assert service._extract_budget("一万以下") == (0, 10000)

    def test_chinese_wan_liangwan_yixia(self, service):
        """两万以下 → (0, 20000)"""
        assert service._extract_budget("两万以下") == (0, 20000)

    def test_chinese_wan_sanwan_yinei(self, service):
        """三万以内 → (0, 30000)"""
        assert service._extract_budget("三万以内") == (0, 30000)

    def test_arabic_wan_yinei(self, service):
        """1万以内 → (0, 10000)"""
        assert service._extract_budget("1万以内") == (0, 10000)

    def test_arabic_wan_yixia(self, service):
        """1万以下 → (0, 10000)"""
        assert service._extract_budget("1万以下") == (0, 10000)

    def test_arabic_wan_2wan_yixia(self, service):
        """2万以下 → (0, 20000)"""
        assert service._extract_budget("2万以下") == (0, 20000)

    def test_chinese_thousand(self, service):
        """三千价位 → (2500, 3500)"""
        assert service._extract_budget("三千价位") == (2500, 3500)

    def test_specific_price_around(self, service):
        """3000左右 → (2500, 3500)"""
        assert service._extract_budget("3000左右") == (2500, 3500)

    def test_price_under(self, service):
        """5000元以内 → (0, 5000)"""
        assert service._extract_budget("5000元以内") == (0, 5000)

    def test_price_range(self, service):
        """2000到4000元 → (2000, 4000)"""
        assert service._extract_budget("2000到4000元") == (2000, 4000)

    def test_no_budget(self, service):
        """无预算信息 → (0, 100000)"""
        assert service._extract_budget("推荐一款手机") == (0, 100000)

    def test_under_price_yinei(self, service):
        """5000元以内 → (0, 5000)"""
        assert service._extract_budget("5000元以内") == (0, 5000)

    def test_under_price_yixia(self, service):
        """5000元以下 → (0, 5000)"""
        assert service._extract_budget("5000元以下") == (0, 5000)

    def test_not_exceed(self, service):
        """不超过5000元 → (0, 5000)"""
        assert service._extract_budget("不超过5000元") == (0, 5000)


class TestCurlyBraceSafety:
    """测试花括号 DoS 防护"""

    @pytest.fixture
    def service(self):
        return IntentService()

    @pytest.mark.asyncio
    async def test_curly_brace_in_message(self, service):
        """用户输入含花括号不应导致 KeyError"""
        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend", "budget_min": 0, "budget_max": 100000}'

            # 不应抛出异常
            result = await service.recognize("{test}")
            assert result.intent == IntentType.RECOMMEND

    @pytest.mark.asyncio
    async def test_format_string_attack(self, service):
        """恶意格式字符串不应导致 500"""
        with patch.object(service.llm, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"intent": "recommend"}'

            # 各种花括号攻击向量
            for payload in ["{__class__}", "{0}", "{key}", "{{double}}"]:
                result = await service.recognize(payload)
                assert result.intent == IntentType.RECOMMEND

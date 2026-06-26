"""
QuestionService 单元测试

测试覆盖：
- QuestionResponse 数据模型
- generate_question() 追问问题生成
- generate_quick_replies() 快捷回复生成
- generate_full_response() 完整响应生成
- _get_missing_field_names() 缺失字段获取
- get_field_priority() 字段优先级
"""
import pytest
from backend.services.question import QuestionService, QuestionResponse
from backend.models.schemas import UserProfile, NeedLevel


class TestQuestionResponse:
    """测试 QuestionResponse 数据模型"""

    def test_create_question_response(self):
        """创建追问响应"""
        response = QuestionResponse(
            question="您的预算大概是多少？",
            quick_replies=["1000-2000元", "2000-3000元"],
            missing_fields=["预算"]
        )

        assert response.question == "您的预算大概是多少？"
        assert response.quick_replies == ["1000-2000元", "2000-3000元"]
        assert response.missing_fields == ["预算"]

    def test_empty_question_response(self):
        """创建空响应"""
        response = QuestionResponse(
            question="",
            quick_replies=[],
            missing_fields=[]
        )

        assert response.question == ""
        assert response.quick_replies == []
        assert response.missing_fields == []


class TestQuestionServiceGenerateQuestion:
    """测试 generate_question() 方法"""

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_generate_budget_question(self, service):
        """生成预算问题"""
        question = service.generate_question(["budget"])

        assert question is not None
        assert len(question) > 0
        # 应包含预算相关关键词
        assert "预算" in question or "钱" in question

    def test_generate_gaming_question(self, service):
        """生成游戏需求问题"""
        question = service.generate_question(["gaming_need"])

        assert question is not None
        assert "游戏" in question

    def test_generate_camera_question(self, service):
        """生成拍照需求问题"""
        question = service.generate_question(["camera_need"])

        assert question is not None
        assert "拍照" in question or "相机" in question

    def test_generate_battery_question(self, service):
        """生成续航需求问题"""
        question = service.generate_question(["battery_need"])

        assert question is not None
        # 检查问题内容（可能是续航、电池、充电等相关词汇）
        assert len(question) > 0

    def test_generate_brand_question(self, service):
        """生成品牌偏好问题"""
        question = service.generate_question(["brand_preference"])

        assert question is not None
        assert "品牌" in question

    def test_generate_empty_fields(self, service):
        """没有缺失字段返回空字符串"""
        question = service.generate_question([])

        assert question == ""

    def test_generate_two_fields_question(self, service):
        """生成双字段组合问题"""
        question = service.generate_question(["budget", "gaming_need"])

        assert question is not None
        # 应包含预算和游戏相关内容
        has_budget = "预算" in question or "钱" in question
        has_gaming = "游戏" in question
        assert has_budget or has_gaming

    def test_generate_three_fields_question(self, service):
        """生成三字段组合问题"""
        question = service.generate_question(["budget", "gaming_need", "camera_need"])

        assert question is not None
        assert len(question) > 0

    def test_generate_question_with_chinese_field(self, service):
        """接受中文描述的字段名"""
        question = service.generate_question(["预算范围"])

        assert question is not None
        assert "预算" in question or "钱" in question

    def test_generate_question_randomness(self, service):
        """问题生成有随机性"""
        questions = set()
        for _ in range(10):
            q = service.generate_question(["budget"])
            questions.add(q)

        # 所有问题都应该是有效的
        for q in questions:
            assert q is not None
            assert len(q) > 0


class TestQuestionServiceGenerateQuickReplies:
    """测试 generate_quick_replies() 方法"""

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_budget_quick_replies(self, service):
        """预算快捷回复"""
        replies = service.generate_quick_replies("budget")

        assert len(replies) == 4
        assert "1000-2000元" in replies
        assert "5000元以上" in replies

    def test_gaming_quick_replies(self, service):
        """游戏需求快捷回复"""
        replies = service.generate_quick_replies("gaming_need")

        assert len(replies) == 4
        assert "不玩游戏" in replies
        assert "原神/崩铁" in replies

    def test_camera_quick_replies(self, service):
        """拍照需求快捷回复"""
        replies = service.generate_quick_replies("camera_need")

        assert len(replies) == 4
        assert "不太拍照" in replies
        assert "专业摄影" in replies

    def test_battery_quick_replies(self, service):
        """续航需求快捷回复"""
        replies = service.generate_quick_replies("battery_need")

        assert len(replies) == 3
        assert "一天一充就行" in replies
        assert "重度使用" in replies

    def test_brand_quick_replies(self, service):
        """品牌偏好快捷回复"""
        replies = service.generate_quick_replies("brand_preference")

        assert len(replies) == 5
        assert "小米" in replies
        assert "华为" in replies
        assert "苹果" in replies
        assert "都可以" in replies

    def test_unknown_field_quick_replies(self, service):
        """未知字段返回空列表"""
        replies = service.generate_quick_replies("unknown_field")

        assert replies == []

    def test_chinese_field_quick_replies(self, service):
        """接受中文描述的字段名"""
        replies = service.generate_quick_replies("预算")

        assert len(replies) > 0


class TestQuestionServiceGenerateFullResponse:
    """测试 generate_full_response() 方法"""

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_empty_profile_response(self, service):
        """空画像生成响应"""
        profile = UserProfile()
        response = service.generate_full_response(profile)

        assert response.question != ""
        assert len(response.quick_replies) > 0
        assert len(response.missing_fields) > 0
        # 优先问预算
        assert "预算" in response.missing_fields

    def test_complete_profile_response(self, service):
        """完整画像返回空响应"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM,
            battery_need=NeedLevel.LOW,
            brand_preference=["小米"]
        )
        response = service.generate_full_response(profile)

        assert response.question == ""
        assert response.quick_replies == []
        assert response.missing_fields == []

    def test_budget_only_profile(self, service):
        """只有预算的画像"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        response = service.generate_full_response(profile)

        assert response.question != ""
        assert "预算" not in response.missing_fields
        # 快捷回复应该是游戏相关（优先级最高的缺失字段）
        assert len(response.quick_replies) > 0

    def test_feature_only_profile(self, service):
        """只有功能需求的画像"""
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        response = service.generate_full_response(profile)

        assert response.question != ""
        assert "预算" in response.missing_fields
        # 快捷回复应该是预算相关
        assert "1000-2000元" in response.quick_replies or "元" in response.quick_replies[0]

    def test_response_has_consistent_fields(self, service):
        """响应字段一致性"""
        profile = UserProfile()
        response = service.generate_full_response(profile)

        # missing_fields 应该与问题对应
        assert len(response.missing_fields) > 0
        # quick_replies 应该与问题字段对应
        assert len(response.quick_replies) > 0


class TestQuestionServiceGetMissingFieldNames:
    """测试 _get_missing_field_names() 方法

    新逻辑（2026-05-04）：
    - 必须有预算
    - 只需要至少一个功能需求（游戏/拍照/续航），而不是全部
    - 品牌偏好是可选的，不算缺失
    """

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_empty_profile_missing_budget_and_feature(self, service):
        """空画像缺失预算和功能需求（只返回预算和游戏需求作为优先）"""
        profile = UserProfile()
        missing = service._get_missing_field_names(profile)

        assert "budget" in missing
        # 只需要至少一个功能需求，优先返回游戏需求
        assert "gaming_need" in missing
        # 品牌偏好是可选的，不应该在缺失列表中
        assert "brand_preference" not in missing

    def test_complete_profile_no_missing(self, service):
        """完整画像无缺失"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM,
            battery_need=NeedLevel.LOW,
            brand_preference=["小米"]
        )
        missing = service._get_missing_field_names(profile)

        assert len(missing) == 0

    def test_single_budget_boundary(self, service):
        """单边预算不算缺失"""
        profile = UserProfile(budget_max=5000)
        missing = service._get_missing_field_names(profile)

        assert "budget" not in missing

    def test_partial_features_sufficient(self, service):
        """部分功能需求已足够，不报告缺失"""
        profile = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.HIGH
        )
        missing = service._get_missing_field_names(profile)

        assert "budget" not in missing
        assert "gaming_need" not in missing
        # 只需要一个功能需求，其他不算缺失
        assert "camera_need" not in missing
        assert "battery_need" not in missing

    def test_empty_brand_preference_not_missing(self, service):
        """空品牌偏好不算缺失（品牌是可选的）"""
        profile = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.HIGH,
            brand_preference=[]
        )
        missing = service._get_missing_field_names(profile)

        # 品牌是可选的，不应该在缺失列表中
        assert "brand_preference" not in missing

    def test_returns_field_names_not_chinese(self, service):
        """返回字段名而非中文描述"""
        profile = UserProfile()
        missing = service._get_missing_field_names(profile)

        # 应该是英文字段名
        assert "budget" in missing
        assert "预算" not in missing


class TestQuestionServiceGetFieldPriority:
    """测试 get_field_priority() 方法"""

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_budget_highest_priority(self, service):
        """预算优先级最高"""
        assert service.get_field_priority("budget") == 0

    def test_gaming_second_priority(self, service):
        """游戏需求优先级第二"""
        assert service.get_field_priority("gaming_need") == 1

    def test_camera_third_priority(self, service):
        """拍照需求优先级第三"""
        assert service.get_field_priority("camera_need") == 2

    def test_battery_fourth_priority(self, service):
        """续航需求优先级第四"""
        assert service.get_field_priority("battery_need") == 3

    def test_brand_lowest_priority(self, service):
        """品牌偏好优先级最低"""
        assert service.get_field_priority("brand_preference") == 4

    def test_unknown_field_low_priority(self, service):
        """未知字段低优先级"""
        assert service.get_field_priority("unknown") > 4


class TestQuestionServiceIntegration:
    """集成测试：模拟多轮对话追问"""

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_multi_turn_questioning(self, service):
        """模拟多轮追问流程"""
        # 第一轮：空画像
        profile = UserProfile()
        response = service.generate_full_response(profile)

        assert "预算" in response.missing_fields
        assert "预算" in response.question or "钱" in response.question

        # 第二轮：用户提供了预算
        profile = UserProfile(budget_min=2000, budget_max=4000)
        response = service.generate_full_response(profile)

        assert "预算" not in response.missing_fields
        assert "游戏" in response.question

        # 第三轮：用户提供了游戏需求（完整）
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_full_response(profile)

        # 画像已完整（预算+一个功能需求），不再追问
        assert response.question == ""
        assert len(response.missing_fields) == 0

    def test_quick_replies_match_question(self, service):
        """快捷回复与问题匹配"""
        # 预算问题的快捷回复
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        response = service.generate_full_response(profile)

        # 问题问预算，快捷回复应该是价格范围
        assert "元" in response.quick_replies[0] or "以上" in response.quick_replies[-1]

        # 游戏问题的快捷回复
        profile = UserProfile(budget_min=2000)
        response = service.generate_full_response(profile)

        # 问题问游戏，快捷回复应该是游戏相关
        assert any("游戏" in r or "玩" in r for r in response.quick_replies)

    def test_all_field_questions_valid(self, service):
        """所有字段的问题都有效"""
        fields = ["budget", "gaming_need", "camera_need", "battery_need", "brand_preference"]

        for field in fields:
            question = service.generate_question([field])

            assert question != "", f"{field} should generate a question"
            assert len(question) > 5, f"{field} question too short"
            assert "？" in question or "。" in question, f"{field} question missing punctuation"

    def test_all_quick_replies_valid(self, service):
        """所有字段的快捷回复都有效"""
        fields = ["budget", "gaming_need", "camera_need", "battery_need", "brand_preference"]

        for field in fields:
            replies = service.generate_quick_replies(field)

            assert len(replies) > 0, f"{field} should have quick replies"
            for reply in replies:
                assert len(reply) > 0, f"{field} has empty quick reply"

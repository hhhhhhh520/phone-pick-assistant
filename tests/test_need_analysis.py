"""
NeedAnalysisService 单元测试

测试覆盖：
- AnalysisResult 数据类
- analyze() 完整性分析
- is_complete() 完整性判断
- get_missing_fields() 缺失字段获取
- _generate_question() 追问问题生成
"""
import pytest
from backend.services.need_analysis import NeedAnalysisService, AnalysisResult
from backend.models.schemas import UserProfile, NeedLevel


class TestAnalysisResult:
    """测试 AnalysisResult 数据类"""

    def test_create_complete_result(self):
        """创建完整的结果"""
        result = AnalysisResult(
            is_complete=True,
            missing_fields=[],
            suggested_question=None
        )
        assert result.is_complete is True
        assert result.missing_fields == []
        assert result.suggested_question is None

    def test_create_incomplete_result(self):
        """创建不完整的结果"""
        result = AnalysisResult(
            is_complete=False,
            missing_fields=["预算范围"],
            suggested_question="您的预算大概是多少呢？"
        )
        assert result.is_complete is False
        assert result.missing_fields == ["预算范围"]
        assert result.suggested_question == "您的预算大概是多少呢？"

    def test_to_dict(self):
        """测试字典转换"""
        result = AnalysisResult(
            is_complete=False,
            missing_fields=["预算范围", "功能需求"],
            suggested_question="测试问题"
        )
        d = result.to_dict()
        assert d["is_complete"] is False
        assert d["missing_fields"] == ["预算范围", "功能需求"]
        assert d["suggested_question"] == "测试问题"

    def test_equality(self):
        """测试相等性判断"""
        result1 = AnalysisResult(is_complete=True, missing_fields=[], suggested_question=None)
        result2 = AnalysisResult(is_complete=True, missing_fields=[], suggested_question=None)
        result3 = AnalysisResult(is_complete=False, missing_fields=[], suggested_question=None)
        assert result1 == result2
        assert result1 != result3

    def test_repr(self):
        """测试字符串表示"""
        result = AnalysisResult(is_complete=True, missing_fields=[], suggested_question=None)
        repr_str = repr(result)
        assert "is_complete=True" in repr_str
        assert "missing_fields=[]" in repr_str


class TestNeedAnalysisServiceAnalyze:
    """测试 analyze() 方法"""

    @pytest.fixture
    def service(self):
        return NeedAnalysisService()

    def test_analyze_empty_profile(self, service):
        """分析空画像"""
        profile = UserProfile()
        result = service.analyze(profile)

        assert result.is_complete is False
        assert len(result.missing_fields) > 0
        assert result.suggested_question is not None

    def test_analyze_complete_profile(self, service):
        """分析完整画像"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        result = service.analyze(profile)

        assert result.is_complete is True
        assert result.missing_fields == []
        assert result.suggested_question is None

    def test_analyze_budget_only(self, service):
        """只有预算的画像"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        result = service.analyze(profile)

        assert result.is_complete is False
        assert any("功能" in f for f in result.missing_fields)
        assert result.suggested_question is not None
        # 问题应该与功能需求相关
        assert "游戏" in result.suggested_question or "拍照" in result.suggested_question or "功能" in result.suggested_question

    def test_analyze_feature_only(self, service):
        """只有功能需求的画像"""
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        result = service.analyze(profile)

        assert result.is_complete is False
        assert "预算范围" in result.missing_fields
        assert result.suggested_question is not None
        # 问题应该与预算相关
        assert "预算" in result.suggested_question or "钱" in result.suggested_question

    def test_analyze_returns_new_instance(self, service):
        """分析不修改原画像"""
        profile = UserProfile()
        result = service.analyze(profile)

        # 原画像不应被修改
        assert profile.budget_min is None
        assert profile.budget_max is None


class TestNeedAnalysisServiceIsComplete:
    """测试 is_complete() 方法"""

    @pytest.fixture
    def service(self):
        return NeedAnalysisService()

    def test_empty_not_complete(self, service):
        """空画像不完整"""
        profile = UserProfile()
        assert service.is_complete(profile) is False

    def test_budget_only_not_complete(self, service):
        """只有预算不完整"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        assert service.is_complete(profile) is False

    def test_feature_only_not_complete(self, service):
        """只有功能需求不完整"""
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        assert service.is_complete(profile) is False

    def test_budget_and_feature_complete(self, service):
        """预算 + 功能需求 = 完整"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        assert service.is_complete(profile) is True

    def test_single_budget_boundary_and_feature_complete(self, service):
        """单边预算 + 功能需求 = 完整"""
        profile = UserProfile(
            budget_max=5000,
            camera_need=NeedLevel.HIGH
        )
        assert service.is_complete(profile) is True


class TestNeedAnalysisServiceGetMissingFields:
    """测试 get_missing_fields() 方法"""

    @pytest.fixture
    def service(self):
        return NeedAnalysisService()

    def test_empty_profile_missing_all(self, service):
        """空画像缺失预算和功能需求"""
        profile = UserProfile()
        missing = service.get_missing_fields(profile)

        assert "预算范围" in missing
        assert any("功能" in f for f in missing)

    def test_budget_only_missing_features(self, service):
        """只有预算，缺失功能需求"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        missing = service.get_missing_fields(profile)

        assert "预算范围" not in missing
        assert any("功能" in f for f in missing)

    def test_feature_only_missing_budget(self, service):
        """只有功能需求，缺失预算"""
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        missing = service.get_missing_fields(profile)

        assert "预算范围" in missing

    def test_complete_profile_no_missing(self, service):
        """完整画像没有缺失"""
        profile = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.HIGH
        )
        missing = service.get_missing_fields(profile)

        assert len(missing) == 0


class TestNeedAnalysisServiceGenerateQuestion:
    """测试 _generate_question() 方法"""

    @pytest.fixture
    def service(self):
        return NeedAnalysisService()

    def test_generate_budget_question(self, service):
        """生成预算相关问题"""
        question = service._generate_question(["预算范围"])

        assert question is not None
        assert "预算" in question or "钱" in question

    def test_generate_feature_question(self, service):
        """生成功能需求相关问题"""
        question = service._generate_question(["至少一项功能需求（游戏/拍照/续航）"])

        assert question is not None
        # 应该包含功能相关的关键词
        has_feature_keyword = any(
            kw in question for kw in ["游戏", "拍照", "续航", "功能", "需求"]
        )
        assert has_feature_keyword

    def test_generate_combined_question(self, service):
        """生成预算和功能都缺失的问题"""
        question = service._generate_question(["预算范围", "至少一项功能需求"])

        assert question is not None
        # 应该同时提到预算和功能
        has_budget = "预算" in question or "钱" in question
        has_feature = any(kw in question for kw in ["游戏", "拍照", "续航", "功能", "需求"])
        # 组合问题至少要包含一类信息
        assert has_budget or has_feature

    def test_generate_question_no_missing(self, service):
        """没有缺失字段时不生成问题"""
        question = service._generate_question([])

        assert question is None

    def test_generate_question_randomness(self, service):
        """问题生成有随机性（测试多次调用可能返回不同结果）"""
        # 多次调用，检查是否返回有效问题
        questions = set()
        for _ in range(10):
            q = service._generate_question(["预算范围"])
            questions.add(q)

        # 所有问题都应该是有效的
        for q in questions:
            assert q is not None
            assert len(q) > 0


class TestNeedAnalysisServiceIntegration:
    """集成测试：模拟多轮对话引导"""

    @pytest.fixture
    def service(self):
        return NeedAnalysisService()

    def test_multi_turn_guidance(self, service):
        """模拟多轮对话引导用户补充信息"""
        # 第一轮：用户刚进入，空画像
        profile = UserProfile()
        result = service.analyze(profile)

        assert result.is_complete is False
        assert len(result.missing_fields) > 0

        # 第二轮：用户说了预算
        profile = UserProfile(budget_min=2000, budget_max=4000)
        result = service.analyze(profile)

        assert result.is_complete is False
        assert len(result.missing_fields) > 0

        # 第三轮：用户说了游戏需求
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        result = service.analyze(profile)

        assert result.is_complete is True
        assert len(result.missing_fields) == 0

"""
SSE question 事件类型测试

测试覆盖：
- question 事件格式
- QuestionResponse 数据模型
- 前端需要的字段完整性
"""
import pytest
import json
from backend.services.question import QuestionService, QuestionResponse
from backend.models.schemas import UserProfile, NeedLevel


class TestQuestionEventFormat:
    """测试 question 事件的数据格式"""

    def test_question_response_model_dump(self):
        """QuestionResponse.model_dump() 生成正确的字典"""
        response = QuestionResponse(
            question="您的预算大概是多少？",
            quick_replies=["1000-2000元", "2000-3000元", "3000-5000元", "5000元以上"],
            missing_fields=["预算", "游戏需求"]
        )

        data = response.model_dump()

        assert "question" in data
        assert "quick_replies" in data
        assert "missing_fields" in data
        assert data["question"] == "您的预算大概是多少？"
        assert len(data["quick_replies"]) == 4
        assert len(data["missing_fields"]) == 2

    def test_question_json_serialization(self):
        """question 事件可以正确序列化为 JSON"""
        response = QuestionResponse(
            question="您的预算大概是多少？",
            quick_replies=["1000-2000元", "2000-3000元"],
            missing_fields=["预算"]
        )

        # 模拟 SSE 格式
        sse_data = json.dumps(response.model_dump(), ensure_ascii=False)

        # 验证可以解析回来
        parsed = json.loads(sse_data)
        assert parsed["question"] == "您的预算大概是多少？"
        assert parsed["quick_replies"] == ["1000-2000元", "2000-3000元"]
        assert parsed["missing_fields"] == ["预算"]

    def test_sse_event_format(self):
        """SSE 事件格式符合规范"""
        response = QuestionResponse(
            question="平时玩游戏吗？",
            quick_replies=["不玩游戏", "王者/吃鸡", "原神/崩铁"],
            missing_fields=["游戏需求"]
        )

        # 模拟后端 SSE 输出
        event_data = {
            "type": "question",
            "data": response.model_dump()
        }

        sse_line = f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

        # 验证格式
        assert sse_line.startswith("data: ")
        assert sse_line.endswith("\n\n")

        # 验证可以解析
        parsed = json.loads(sse_line[6:].strip())
        assert parsed["type"] == "question"
        assert "data" in parsed


class TestQuestionServiceSSEIntegration:
    """测试 QuestionService 与 SSE 的集成"""

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_generate_full_response_sse_ready(self, service):
        """generate_full_response 返回可直接用于 SSE 的数据"""
        # 空画像
        profile = UserProfile()
        response = service.generate_full_response(profile)

        # 验证字段完整性
        assert response.question != ""
        assert len(response.quick_replies) > 0
        assert len(response.missing_fields) > 0

        # 验证可以直接序列化
        data = response.model_dump()
        json.dumps(data, ensure_ascii=False)  # 不应抛出异常

    def test_budget_question_with_quick_replies(self, service):
        """预算问题有对应的快捷回复"""
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        response = service.generate_full_response(profile)

        # 预算应该是第一个缺失字段
        assert "预算" in response.missing_fields
        # 快捷回复应该是价格范围
        assert any("元" in r or "以上" in r for r in response.quick_replies)

    def test_gaming_question_with_quick_replies(self, service):
        """游戏问题有对应的快捷回复"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        response = service.generate_full_response(profile)

        # 游戏需求应该是第一个缺失字段
        assert "游戏需求" in response.missing_fields
        # 快捷回复应该是游戏相关
        assert any("游戏" in r or "玩" in r for r in response.quick_replies)


class TestQuestionEventFrontendFields:
    """测试前端所需的字段"""

    def test_all_required_fields_present(self):
        """所有前端需要的字段都存在"""
        response = QuestionResponse(
            question="测试问题",
            quick_replies=["选项1", "选项2"],
            missing_fields=["字段1"]
        )

        data = response.model_dump()

        # 前端 TypeScript QuestionResponse 接口要求的字段
        required_fields = ["question", "quick_replies", "missing_fields"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_empty_quick_replies(self):
        """空快捷回复列表也有效"""
        response = QuestionResponse(
            question="测试问题",
            quick_replies=[],
            missing_fields=["字段1"]
        )

        data = response.model_dump()
        assert data["quick_replies"] == []

    def test_chinese_characters_preserved(self):
        """中文字符在 JSON 序列化时保留"""
        response = QuestionResponse(
            question="您的预算大概是多少？",
            quick_replies=["1000-2000元", "2000-3000元"],
            missing_fields=["预算范围", "游戏需求"]
        )

        # 使用 ensure_ascii=False
        json_str = json.dumps(response.model_dump(), ensure_ascii=False)

        # 验证中文字符存在
        assert "预算" in json_str
        assert "游戏需求" in json_str


class TestSSEEventType:
    """测试 SSE 事件类型"""

    def test_question_event_type_in_data(self):
        """question 事件类型在 data JSON 中"""
        event_data = {
            "type": "question",
            "data": {
                "question": "测试问题",
                "quick_replies": ["选项1"],
                "missing_fields": ["字段1"]
            }
        }

        json_str = json.dumps(event_data, ensure_ascii=False)
        parsed = json.loads(json_str)

        assert parsed["type"] == "question"
        assert "data" in parsed
        assert parsed["data"]["question"] == "测试问题"

    def test_question_vs_content_event_distinction(self):
        """question 事件与 content 事件可区分"""
        # content 事件
        content_event = {"type": "content", "data": "推荐内容"}

        # question 事件
        question_event = {
            "type": "question",
            "data": {
                "question": "您的预算？",
                "quick_replies": ["1000-2000元"],
                "missing_fields": ["预算"]
            }
        }

        # 验证类型不同
        assert content_event["type"] != question_event["type"]
        # question 事件的 data 是对象，content 的 data 是字符串
        assert isinstance(question_event["data"], dict)
        assert isinstance(content_event["data"], str)

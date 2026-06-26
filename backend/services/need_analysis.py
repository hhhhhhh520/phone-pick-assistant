"""
需求完整性分析服务

分析用户需求是否足够明确，返回缺失的关键信息字段，
并生成建议的追问问题来引导用户补充信息。
"""
from typing import List, Optional
from backend.models.schemas import UserProfile
import random


class AnalysisResult:
    """
    需求分析结果

    Attributes:
        is_complete: 需求是否完整
        missing_fields: 缺失字段列表（中文描述）
        suggested_question: 建议的追问问题
    """

    def __init__(
        self,
        is_complete: bool,
        missing_fields: List[str],
        suggested_question: Optional[str] = None
    ):
        self.is_complete = is_complete
        self.missing_fields = missing_fields
        self.suggested_question = suggested_question

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "is_complete": self.is_complete,
            "missing_fields": self.missing_fields,
            "suggested_question": self.suggested_question
        }

    def __eq__(self, other):
        if not isinstance(other, AnalysisResult):
            return False
        return (
            self.is_complete == other.is_complete
            and self.missing_fields == other.missing_fields
            and self.suggested_question == other.suggested_question
        )

    def __repr__(self):
        return (
            f"AnalysisResult(is_complete={self.is_complete}, "
            f"missing_fields={self.missing_fields}, "
            f"suggested_question={self.suggested_question!r})"
        )


class NeedAnalysisService:
    """
    需求完整性分析服务

    分析用户画像的完整性，判断是否有足够的信息进行手机推荐，
    并生成引导性的追问问题帮助用户补充缺失信息。
    """

    # 追问问题模板
    QUESTION_TEMPLATES = {
        "budget": [
            "您的预算大概是多少呢？比如2000-3000元，还是4000-5000元？",
            "您想买多少钱的手机？可以告诉我一个大概的价格范围。",
            "预算方面有什么要求吗？比如3000元左右或者5000元以内？"
        ],
        "feature": [
            "您对手机有什么特别的需求吗？比如打游戏、拍照、还是续航？",
            "您平时主要用手机做什么呢？玩游戏、拍照、还是看视频？",
            "有没有什么功能是您比较看重的？比如游戏性能、拍照效果、或者电池续航？"
        ],
        "budget_and_feature": [
            "请告诉我您的预算范围，以及您对手机的主要需求（比如游戏、拍照、续航等）。",
            "为了给您更好的推荐，需要了解您的预算和主要使用需求。"
        ]
    }

    def analyze(self, user_profile: UserProfile) -> AnalysisResult:
        """
        分析用户需求的完整性

        Args:
            user_profile: 用户画像

        Returns:
            AnalysisResult: 分析结果，包含完整性、缺失字段和建议问题
        """
        is_complete = user_profile.is_complete()
        missing_fields = user_profile.get_missing_fields()
        suggested_question = None

        if not is_complete:
            suggested_question = self._generate_question(missing_fields)

        return AnalysisResult(
            is_complete=is_complete,
            missing_fields=missing_fields,
            suggested_question=suggested_question
        )

    def is_complete(self, user_profile: UserProfile) -> bool:
        """
        判断用户需求是否完整

        Args:
            user_profile: 用户画像

        Returns:
            bool: 需求是否完整
        """
        return user_profile.is_complete()

    def get_missing_fields(self, user_profile: UserProfile) -> List[str]:
        """
        获取缺失的关键字段

        Args:
            user_profile: 用户画像

        Returns:
            List[str]: 缺失字段的中文描述列表
        """
        return user_profile.get_missing_fields()

    def _generate_question(self, missing_fields: List[str]) -> str:
        """
        根据缺失字段生成追问问题

        Args:
            missing_fields: 缺失字段列表

        Returns:
            str: 建议的追问问题
        """
        if not missing_fields:
            return None

        # 判断缺失类型
        has_budget_missing = any("预算" in field for field in missing_fields)
        has_feature_missing = any("功能" in field for field in missing_fields)

        if has_budget_missing and has_feature_missing:
            # 预算和功能都缺失
            templates = self.QUESTION_TEMPLATES["budget_and_feature"]
        elif has_budget_missing:
            # 只缺预算
            templates = self.QUESTION_TEMPLATES["budget"]
        elif has_feature_missing:
            # 只缺功能需求
            templates = self.QUESTION_TEMPLATES["feature"]
        else:
            # 其他情况，使用功能问题作为默认
            templates = self.QUESTION_TEMPLATES["feature"]

        return random.choice(templates)

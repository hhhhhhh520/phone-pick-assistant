from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class IntentType(str, Enum):
    RECOMMEND = "recommend"
    COMPARE = "compare"
    FILTER = "filter"


class ChatRequest(BaseModel):
    message: str = Field(
        max_length=2000,
        description="用户输入消息",
        examples=["推荐一款3000元左右的手机"]
    )
    session_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """验证消息长度和非空"""
        if not v or not v.strip():
            raise ValueError("消息不能为空")
        # 注意：Pydantic max_length 已处理长度限制
        # 这里可以添加额外的内容验证
        return v.strip()


class PhoneBrief(BaseModel):
    """列表接口精简字段，含 imageUrl 供前端卡片展示 (ISSUE-041)"""
    id: int
    brand: str
    model: str
    price: int
    imageUrl: Optional[str] = None


class PhoneListResponse(BaseModel):
    phones: List[PhoneBrief]
    total: int


class IntentResult(BaseModel):
    """意图识别结果模型"""

    intent: IntentType
    budget_min: Optional[int] = 0
    budget_max: Optional[int] = 100000
    brands: Optional[List[str]] = []
    features: Optional[List[str]] = []
    phones_mentioned: Optional[List[str]] = []

    # 用户明确表示不需要的功能
    no_need_features: Optional[List[str]] = Field(
        default=[],
        description="用户明确表示不需要的功能列表，如['游戏']表示用户说'不玩游戏'"
    )

    # 重置状态标志
    reset_profile: bool = Field(
        default=False,
        description="是否需要重置用户需求状态（用户想重新开始）"
    )

    # 追问相关字段
    need_clarification: bool = Field(
        default=False,
        description="是否需要追问用户补充信息"
    )
    missing_fields: Optional[List[str]] = Field(
        default=[],
        description="缺失的关键字段列表，如预算、品牌等"
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="追问问题，用于引导用户补充缺失信息"
    )

    # 痛点检测相关字段
    pain_point_detected: bool = Field(
        default=False,
        description="是否检测到痛点（预算与需求冲突等）"
    )
    pain_point_type: Optional[str] = Field(
        default=None,
        description="痛点类型，如 budget_too_low_for_features"
    )
    pain_point_severity: Optional[str] = Field(
        default=None,
        description="痛点严重程度：high/medium/low"
    )


class NeedLevel(str, Enum):
    """需求程度枚举"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class UserProfile(BaseModel):
    """
    用户需求状态模型，用于多轮对话引导。

    五个维度：
    - 预算：budget_min, budget_max
    - 游戏需求：gaming_need
    - 拍照需求：camera_need
    - 续航需求：battery_need
    - 品牌偏好：brand_preference
    """

    budget_min: Optional[int] = Field(default=None, description="预算下限（元）")
    budget_max: Optional[int] = Field(default=None, description="预算上限（元）")
    gaming_need: Optional[NeedLevel] = Field(default=None, description="游戏需求程度")
    camera_need: Optional[NeedLevel] = Field(default=None, description="拍照需求程度")
    battery_need: Optional[NeedLevel] = Field(default=None, description="续航需求程度")
    brand_preference: Optional[List[str]] = Field(default=None, description="品牌偏好列表")

    def is_complete(self) -> bool:
        """
        判断需求是否足够完整进行推荐。

        完整性标准：
        - 必须有预算范围（至少一个边界）
        - 至少有一个功能需求（游戏/拍照/续航）
        - 品牌偏好可选（为空视为无偏好）

        Returns:
            bool: 需求是否完整
        """
        # 预算：至少有一个边界
        has_budget = self.budget_min is not None or self.budget_max is not None

        # 功能需求：至少有一个
        has_feature = any([
            self.gaming_need is not None,
            self.camera_need is not None,
            self.battery_need is not None
        ])

        return has_budget and has_feature

    def get_missing_fields(self) -> List[str]:
        """
        返回缺失的关键字段列表。

        Returns:
            List[str]: 缺失字段的中文描述列表
        """
        missing = []

        # 检查预算
        if self.budget_min is None and self.budget_max is None:
            missing.append("预算范围")

        # 检查功能需求
        feature_missing = []
        if self.gaming_need is None:
            feature_missing.append("游戏需求")
        if self.camera_need is None:
            feature_missing.append("拍照需求")
        if self.battery_need is None:
            feature_missing.append("续航需求")

        # 功能需求至少需要一个，否则提示
        if len(feature_missing) == 3:
            missing.append("至少一项功能需求（游戏/拍照/续航）")
        elif len(feature_missing) > 0:
            # 如果已有部分功能需求，不报告缺失（因为至少有一个就够了）
            pass

        return missing

    def update_from_intent(self, intent_result: IntentResult) -> "UserProfile":
        """
        从意图识别结果更新用户状态。

        Args:
            intent_result: 意图识别结果

        Returns:
            UserProfile: 更新后的用户状态（新实例）
        """
        updates = {}

        # 更新预算
        if intent_result.budget_min and intent_result.budget_min > 0:
            updates["budget_min"] = intent_result.budget_min
        if intent_result.budget_max and intent_result.budget_max < 100000:
            updates["budget_max"] = intent_result.budget_max

        # 更新品牌偏好
        if intent_result.brands:
            # 合并现有偏好和新增偏好
            existing_brands = self.brand_preference or []
            new_brands = list(set(existing_brands + intent_result.brands))
            updates["brand_preference"] = new_brands

        # 从 features 推断功能需求
        features = intent_result.features or []
        for feature in features:
            feature_lower = feature.lower()
            if "游戏" in feature_lower or "电竞" in feature_lower or "性能" in feature_lower:
                updates["gaming_need"] = NeedLevel.HIGH
            elif "拍照" in feature_lower or "影像" in feature_lower or "相机" in feature_lower:
                updates["camera_need"] = NeedLevel.HIGH
            elif "续航" in feature_lower or "电池" in feature_lower:
                updates["battery_need"] = NeedLevel.HIGH
            elif "快充" in feature_lower:
                # 快充关联续航需求
                updates["battery_need"] = NeedLevel.MEDIUM

        # 处理用户明确表示不需要的功能
        no_need_features = intent_result.no_need_features or []
        for feature in no_need_features:
            feature_lower = feature.lower()
            if "游戏" in feature_lower:
                updates["gaming_need"] = NeedLevel.LOW  # 明确不需要游戏
            elif "拍照" in feature_lower:
                updates["camera_need"] = NeedLevel.LOW  # 明确不需要拍照
            elif "续航" in feature_lower:
                updates["battery_need"] = NeedLevel.LOW  # 明确不需要续航

        # 创建新实例，保留未更新的字段
        return UserProfile(
            budget_min=updates.get("budget_min", self.budget_min),
            budget_max=updates.get("budget_max", self.budget_max),
            gaming_need=updates.get("gaming_need", self.gaming_need),
            camera_need=updates.get("camera_need", self.camera_need),
            battery_need=updates.get("battery_need", self.battery_need),
            brand_preference=updates.get("brand_preference", self.brand_preference)
        )

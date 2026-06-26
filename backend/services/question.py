"""
追问生成服务

根据缺失字段生成自然语言的追问问题，
支持单次追问和多维度追问，并提供快捷回复选项。

包含痛点追问服务，检测用户预算与需求的冲突。
"""
from typing import List, Optional
from pydantic import BaseModel
import random
from backend.models.schemas import UserProfile, NeedLevel
from backend.models.domain import Phone


class QuestionResponse(BaseModel):
    """
    追问响应模型

    Attributes:
        question: 追问问题
        quick_replies: 快捷回复选项
        missing_fields: 缺失字段列表
    """

    question: str
    quick_replies: List[str]
    missing_fields: List[str]


class QuestionService:
    """
    追问生成服务

    根据用户画像缺失的字段生成追问问题，
    提供快捷回复选项帮助用户快速回答。
    """

    # 字段到中文的映射
    FIELD_NAMES = {
        "budget": "预算",
        "gaming_need": "游戏需求",
        "camera_need": "拍照需求",
        "battery_need": "续航需求",
        "brand_preference": "品牌偏好"
    }

    # 追问问题模板（每个字段多个备选）
    QUESTION_TEMPLATES = {
        "budget": [
            "您的预算大概是多少？",
            "您打算花多少钱买手机？",
            "预算方面有什么要求吗？"
        ],
        "gaming_need": [
            "平时玩游戏吗？玩什么游戏？",
            "对游戏性能有要求吗？",
            "您会用手机打游戏吗？"
        ],
        "camera_need": [
            "对拍照有要求吗？",
            "平时拍照多吗？",
            "对相机功能有什么期待？"
        ],
        "battery_need": [
            "对续航有要求吗？",
            "平时一天大概用多久手机？",
            "电池续航方面有什么需求？"
        ],
        "brand_preference": [
            "有品牌偏好吗？",
            "比较喜欢哪个品牌的手机？",
            "有没有特别想买或不想买的品牌？"
        ]
    }

    # 快捷回复选项
    QUICK_REPLIES = {
        "budget": ["1000-2000元", "2000-3000元", "3000-5000元", "5000元以上"],
        "gaming_need": ["不玩游戏", "王者/吃鸡", "原神/崩铁", "重度游戏"],
        "camera_need": ["不太拍照", "日常记录", "人像/风景", "专业摄影"],
        "battery_need": ["一天一充就行", "希望两天一充", "重度使用"],
        "brand_preference": ["小米", "华为", "苹果", "OPPO/vivo", "都可以"]
    }

    # 多字段组合问题模板
    COMBINED_QUESTIONS = {
        ("budget", "gaming_need"): [
            "请告诉我您的预算范围，以及平时玩游戏的情况。",
            "您想花多少钱买手机？会用来玩游戏吗？"
        ],
        ("budget", "camera_need"): [
            "您的预算是多少？对拍照有要求吗？",
            "想花多少钱？拍照方面有什么需求？"
        ],
        ("budget", "battery_need"): [
            "预算大概多少？对续航有要求吗？",
            "您想花多少钱买手机？电池续航重要吗？"
        ],
        ("gaming_need", "camera_need"): [
            "平时玩游戏和拍照多吗？",
            "您对游戏性能和拍照效果有什么需求？"
        ],
        ("gaming_need", "battery_need"): [
            "玩游戏多吗？对续航有什么要求？",
            "游戏和续航方面有什么需求？"
        ],
        ("camera_need", "battery_need"): [
            "拍照和续航方面有什么要求？",
            "您对相机和电池有什么需求？"
        ],
        ("budget", "gaming_need", "camera_need"): [
            "请告诉我您的预算，以及游戏和拍照方面的需求。",
            "预算多少？玩游戏和拍照的情况是怎样的？"
        ],
        ("budget", "gaming_need", "battery_need"): [
            "您的预算是多少？游戏和续航有什么需求？",
            "想花多少钱买手机？会玩游戏吗？续航重要吗？"
        ],
        ("budget", "camera_need", "battery_need"): [
            "预算多少？拍照和续航有什么要求？",
            "您想花多少钱？对相机和电池有需求吗？"
        ],
        ("gaming_need", "camera_need", "battery_need"): [
            "游戏、拍照和续航方面有什么需求？",
            "您对手机的游戏性能、相机效果和电池续航有什么要求？"
        ],
        ("budget", "gaming_need", "camera_need", "battery_need"): [
            "请告诉我您的预算，以及游戏、拍照、续航方面的需求。",
            "预算多少？平时主要用手机做什么（游戏/拍照）？续航重要吗？"
        ]
    }

    def generate_question(self, missing_fields: List[str]) -> str:
        """
        根据缺失字段生成追问问题

        Args:
            missing_fields: 缺失字段列表，元素为字段名（如 "budget", "gaming_need"）

        Returns:
            str: 生成的追问问题
        """
        if not missing_fields:
            return ""

        # 标准化字段名（去除中文描述，转为字段名）
        normalized_fields = []
        for field in missing_fields:
            # 如果已经是字段名，直接使用
            if field in self.FIELD_NAMES:
                normalized_fields.append(field)
            # 如果是中文描述，转换为字段名
            elif "预算" in field:
                normalized_fields.append("budget")
            elif "游戏" in field:
                normalized_fields.append("gaming_need")
            elif "拍照" in field:
                normalized_fields.append("camera_need")
            elif "续航" in field:
                normalized_fields.append("battery_need")
            elif "品牌" in field:
                normalized_fields.append("brand_preference")

        # 去重并排序（保持优先级：预算 > 功能需求 > 品牌）
        priority_order = ["budget", "gaming_need", "camera_need", "battery_need", "brand_preference"]
        sorted_fields = sorted(
            set(normalized_fields),
            key=lambda x: priority_order.index(x) if x in priority_order else len(priority_order)
        )

        # 单字段问题
        if len(sorted_fields) == 1:
            templates = self.QUESTION_TEMPLATES.get(sorted_fields[0], [])
            if templates:
                return random.choice(templates)
            return f"请告诉我您的{self.FIELD_NAMES.get(sorted_fields[0], sorted_fields[0])}。"

        # 多字段组合问题
        field_tuple = tuple(sorted_fields)
        templates = self.COMBINED_QUESTIONS.get(field_tuple)

        if templates:
            return random.choice(templates)

        # 没有预定义模板，生成组合问题
        field_names = [self.FIELD_NAMES.get(f, f) for f in sorted_fields]
        return f"请告诉我您的{', '.join(field_names[:-1])}和{field_names[-1]}。"

    def generate_quick_replies(self, field: str) -> List[str]:
        """
        根据字段生成快捷回复选项

        Args:
            field: 字段名（如 "budget", "gaming_need"）

        Returns:
            List[str]: 快捷回复选项列表
        """
        # 标准化字段名
        normalized_field = field
        if field not in self.FIELD_NAMES:
            for key, name in self.FIELD_NAMES.items():
                if name in field:
                    normalized_field = key
                    break

        return self.QUICK_REPLIES.get(normalized_field, [])

    def generate_full_response(self, user_profile: UserProfile) -> QuestionResponse:
        """
        根据用户画像生成完整的追问响应

        Args:
            user_profile: 用户画像

        Returns:
            QuestionResponse: 包含问题、快捷回复、缺失字段的响应
        """
        # 获取缺失字段（字段名格式）
        missing_fields = self._get_missing_field_names(user_profile)

        if not missing_fields:
            # 没有缺失字段，返回空响应（实际场景应直接推荐）
            return QuestionResponse(
                question="",
                quick_replies=[],
                missing_fields=[]
            )

        # 获取优先级最高的缺失字段作为主要问题
        priority_order = ["budget", "gaming_need", "camera_need", "battery_need", "brand_preference"]
        primary_field = min(
            missing_fields,
            key=lambda x: priority_order.index(x) if x in priority_order else len(priority_order)
        )

        # 生成问题
        question = self.generate_question([primary_field])

        # 生成快捷回复（基于主要问题字段）
        quick_replies = self.generate_quick_replies(primary_field)

        # 转换缺失字段为中文描述
        missing_fields_cn = [self.FIELD_NAMES.get(f, f) for f in missing_fields]

        return QuestionResponse(
            question=question,
            quick_replies=quick_replies,
            missing_fields=missing_fields_cn
        )

    def _get_missing_field_names(self, user_profile: UserProfile) -> List[str]:
        """
        获取缺失字段的字段名列表（而非中文描述）

        根据完整性标准：
        - 必须有预算
        - 至少有一个功能需求（游戏/拍照/续航），LOW 也算已明确
        - 品牌偏好可选

        Args:
            user_profile: 用户画像

        Returns:
            List[str]: 缺失字段名列表
        """
        missing = []

        # 检查预算（必须有）
        if user_profile.budget_min is None and user_profile.budget_max is None:
            missing.append("budget")

        # 检查功能需求：只需要至少有一个（LOW 也算已明确）
        # 注意：LOW 表示用户明确表示不需要，也算已明确
        has_feature = any([
            user_profile.gaming_need is not None,  # 包括 LOW
            user_profile.camera_need is not None,
            user_profile.battery_need is not None
        ])

        if not has_feature:
            # 没有任何功能需求，优先询问游戏需求
            missing.append("gaming_need")

        # 注意：品牌偏好是可选的，不加入 missing

        return missing

    def get_field_priority(self, field: str) -> int:
        """
        获取字段的优先级

        Args:
            field: 字段名

        Returns:
            int: 优先级（数字越小优先级越高）
        """
        priority_order = ["budget", "gaming_need", "camera_need", "battery_need", "brand_preference"]
        return priority_order.index(field) if field in priority_order else len(priority_order)


class PainPointResponse(BaseModel):
    """
    痛点追问响应模型

    Attributes:
        question: 追问问题
        quick_replies: 快捷回复选项
        pain_point_type: 痛点类型
        severity: 痛点严重程度 (high/medium/low)
        suggestion: 解决建议
    """

    question: str
    quick_replies: List[str]
    pain_point_type: str
    severity: str = "medium"
    suggestion: Optional[str] = None


# 痛点场景模板
PAIN_POINT_TEMPLATES = {
    "budget_too_low_for_features": {
        "description": "预算不足：高需求但预算低",
        "question_templates": [
            "您的预算可能难以满足游戏+拍照的高需求，建议调整预算或降低某项需求，您更看重哪个？",
            "这个预算要同时满足高游戏和高拍照需求比较困难，您愿意在哪方面妥协？",
            "高端游戏手机通常要4000元以上，您的预算可能只能满足中等需求，可以接受吗？"
        ],
        "quick_replies": ["提高预算", "降低游戏需求", "降低拍照需求", "先看看再说"],
        "suggestion": "建议预算提高到4000元以上，或降低游戏/拍照需求中的一项"
    },
    "brand_budget_conflict": {
        "description": "品牌冲突：想要特定品牌但预算不够",
        "question_templates": [
            "您想要的{brand}手机价格通常较高，当前预算可能买不到新款，可以考虑其他品牌吗？",
            "{brand}的旗舰机型都在{min_price}元以上，您的预算只能买到入门款，可以接受吗？",
            "在这个价位，{brand}的选择较少，要不要看看其他品牌？"
        ],
        "quick_replies": ["提高预算", "换个品牌", "看看入门款", "都可以"],
        "suggestion": "建议提高预算或放宽品牌限制"
    },
    "gaming_camera_budget_conflict": {
        "description": "功能冲突：想要游戏+拍照但预算有限",
        "question_templates": [
            "游戏性能和拍照都是旗舰配置的手机通常5000+，您的预算可能不够，更看重哪个？",
            "同时满足游戏和拍照的高需求需要旗舰机，您愿意在哪方面妥协？",
            "游戏手机拍照一般，拍照手机游戏一般，您更偏向哪个方向？"
        ],
        "quick_replies": ["优先游戏", "优先拍照", "提高预算", "平衡一下"],
        "suggestion": "建议选择游戏手机或拍照手机中的一个方向，或提高预算到5000元以上"
    },
    "battery_vs_gaming": {
        "description": "续航与游戏冲突：重度游戏但也要长续航",
        "question_templates": [
            "重度游戏会快速消耗电量，即使大电池也难撑一天，您对续航有特别要求吗？",
            "游戏手机通常续航一般，您需要特别关注续航吗？",
            "高强度游戏耗电快，建议选择带快充的手机，可以吗？"
        ],
        "quick_replies": ["续航很重要", "游戏优先", "有快充就行", "不太在意"],
        "suggestion": "建议选择支持高功率快充(67W+)的游戏手机"
    },
    "high_demand_low_budget_general": {
        "description": "综合高需求低预算：多项高需求但预算不足",
        "question_templates": [
            "您对多个方面都有高要求，但预算有限，建议选择核心需求，您最看重什么？",
            "全能旗舰机通常5000元以上，您的预算只能满足部分需求，优先哪个？",
            "高性能+好拍照+长续航的手机较贵，您愿意在哪方面妥协？"
        ],
        "quick_replies": ["性能优先", "拍照优先", "续航优先", "提高预算"],
        "suggestion": "建议确定最核心的1-2个需求，或提高预算到5000元以上"
    },
    "brand_not_match_features": {
        "description": "品牌与功能不匹配：想要的品牌不擅长该功能",
        "question_templates": [
            "{brand}手机在{feature}方面不是强项，您可以接受吗？",
            "想要顶级的{feature}，可能需要考虑其他品牌，要不要看看？",
            "{brand}的{feature}表现中等，对您来说够用吗？"
        ],
        "quick_replies": ["够用就行", "换个品牌", "降低需求", "先看看再说"],
        "suggestion": "建议根据核心需求选择擅长该功能的品牌"
    }
}


class PainPointQuestionService:
    """
    痛点追问服务

    检测用户预算与需求的冲突，生成针对性的追问。
    """

    # 品牌价格参考（旗舰机最低价格）
    BRAND_PRICE_REFERENCE = {
        "华为": 4000,
        "苹果": 5000,
        "小米": 3000,
        "OPPO": 3000,
        "vivo": 3000,
        "三星": 4000,
        "荣耀": 2500,
        "realme": 2000,
        "红魔": 3000,
        "一加": 3000
    }

    # 品牌特色
    BRAND_SPECIALTY = {
        "华为": ["拍照", "续航"],
        "苹果": ["拍照", "性能"],
        "小米": ["性能", "性价比"],
        "OPPO": ["拍照", "快充"],
        "vivo": ["拍照", "音乐"],
        "三星": ["拍照", "屏幕"],
        "荣耀": ["性能", "续航"],
        "红魔": ["游戏"],
        "一加": ["性能"]
    }

    def generate_pain_point_question(
        self,
        user_profile: UserProfile,
        phones: Optional[List[Phone]] = None
    ) -> Optional[PainPointResponse]:
        """
        根据用户画像检测痛点并生成追问

        检测策略（按优先级）：
        1. 预算与高需求的冲突
        2. 品牌偏好与预算的冲突
        3. 功能需求的冲突
        4. 品牌与功能的不匹配

        Args:
            user_profile: 用户画像
            phones: 可选的手机列表，用于更精确的冲突检测

        Returns:
            PainPointResponse: 痛点追问响应，无冲突返回 None
        """
        # 检测预算与需求的冲突
        budget_conflict = self._detect_budget_feature_conflict(user_profile)
        if budget_conflict:
            template = PAIN_POINT_TEMPLATES["budget_too_low_for_features"]
            question = random.choice(template["question_templates"])
            return PainPointResponse(
                question=question,
                quick_replies=template["quick_replies"],
                pain_point_type="budget_too_low_for_features",
                severity="high",
                suggestion=template["suggestion"]
            )

        # 检测品牌与预算的冲突
        brand_conflict = self._detect_brand_budget_conflict(user_profile)
        if brand_conflict:
            template = PAIN_POINT_TEMPLATES["brand_budget_conflict"]
            brand = brand_conflict["brand"]
            min_price = brand_conflict["min_price"]
            # 填充模板变量
            question = random.choice(template["question_templates"]).format(
                brand=brand,
                min_price=min_price
            )
            return PainPointResponse(
                question=question,
                quick_replies=template["quick_replies"],
                pain_point_type="brand_budget_conflict",
                severity="high",
                suggestion=template["suggestion"]
            )

        # 检测功能冲突（游戏+拍照但预算有限）
        feature_conflict = self._detect_feature_conflict(user_profile)
        if feature_conflict:
            template = PAIN_POINT_TEMPLATES["gaming_camera_budget_conflict"]
            question = random.choice(template["question_templates"])
            return PainPointResponse(
                question=question,
                quick_replies=template["quick_replies"],
                pain_point_type="gaming_camera_budget_conflict",
                severity="medium",
                suggestion=template["suggestion"]
            )

        # 检测续航与游戏的冲突
        battery_conflict = self._detect_battery_gaming_conflict(user_profile)
        if battery_conflict:
            template = PAIN_POINT_TEMPLATES["battery_vs_gaming"]
            question = random.choice(template["question_templates"])
            return PainPointResponse(
                question=question,
                quick_replies=template["quick_replies"],
                pain_point_type="battery_vs_gaming",
                severity="low",
                suggestion=template["suggestion"]
            )

        # 检测综合高需求低预算
        general_conflict = self._detect_general_high_demand_low_budget(user_profile)
        if general_conflict:
            template = PAIN_POINT_TEMPLATES["high_demand_low_budget_general"]
            question = random.choice(template["question_templates"])
            return PainPointResponse(
                question=question,
                quick_replies=template["quick_replies"],
                pain_point_type="high_demand_low_budget_general",
                severity="medium",
                suggestion=template["suggestion"]
            )

        # 检测品牌与功能不匹配
        brand_feature_conflict = self._detect_brand_feature_mismatch(user_profile)
        if brand_feature_conflict:
            template = PAIN_POINT_TEMPLATES["brand_not_match_features"]
            brand = brand_feature_conflict["brand"]
            feature = brand_feature_conflict["feature"]
            question = random.choice(template["question_templates"]).format(
                brand=brand,
                feature=feature
            )
            return PainPointResponse(
                question=question,
                quick_replies=template["quick_replies"],
                pain_point_type="brand_not_match_features",
                severity="low",
                suggestion=template["suggestion"]
            )

        # 无冲突
        return None

    def _detect_budget_feature_conflict(self, profile: UserProfile) -> bool:
        """检测预算与高需求的冲突"""
        # 预算上限低于3000，但有高游戏或高拍照需求
        budget_max = profile.budget_max or 100000

        if budget_max < 3000:
            high_gaming = profile.gaming_need == NeedLevel.HIGH
            high_camera = profile.camera_need == NeedLevel.HIGH
            if high_gaming or high_camera:
                return True

        return False

    def _detect_brand_budget_conflict(self, profile: UserProfile) -> Optional[dict]:
        """检测品牌与预算的冲突"""
        if not profile.brand_preference:
            return None

        budget_max = profile.budget_max or 100000

        for brand in profile.brand_preference:
            # 标准化品牌名
            normalized_brand = self._normalize_brand(brand)
            if normalized_brand in self.BRAND_PRICE_REFERENCE:
                min_price = self.BRAND_PRICE_REFERENCE[normalized_brand]
                # 预算上限低于品牌旗舰机最低价格
                if budget_max < min_price and budget_max > 0:
                    return {"brand": normalized_brand, "min_price": min_price}

        return None

    def _detect_feature_conflict(self, profile: UserProfile) -> bool:
        """检测游戏+拍照高需求但预算有限"""
        budget_max = profile.budget_max or 100000

        high_gaming = profile.gaming_need == NeedLevel.HIGH
        high_camera = profile.camera_need == NeedLevel.HIGH

        # 高游戏+高拍照，但预算低于5000
        if high_gaming and high_camera and budget_max < 5000:
            return True

        return False

    def _detect_battery_gaming_conflict(self, profile: UserProfile) -> bool:
        """检测续航与游戏的冲突"""
        high_gaming = profile.gaming_need == NeedLevel.HIGH
        high_battery = profile.battery_need == NeedLevel.HIGH

        # 高游戏+高续航需求，通常难以同时满足
        return high_gaming and high_battery

    def _detect_general_high_demand_low_budget(self, profile: UserProfile) -> bool:
        """检测综合高需求低预算"""
        budget_max = profile.budget_max or 100000

        # 计算高需求数量
        high_count = 0
        if profile.gaming_need == NeedLevel.HIGH:
            high_count += 1
        if profile.camera_need == NeedLevel.HIGH:
            high_count += 1
        if profile.battery_need == NeedLevel.HIGH:
            high_count += 1

        # 3个都是高需求，但预算低于5000
        if high_count >= 3 and budget_max < 5000:
            return True

        return False

    def _detect_brand_feature_mismatch(self, profile: UserProfile) -> Optional[dict]:
        """检测品牌与功能不匹配"""
        if not profile.brand_preference:
            return None

        # 确定用户的最高需求
        high_feature = None
        if profile.gaming_need == NeedLevel.HIGH:
            high_feature = "游戏"
        elif profile.camera_need == NeedLevel.HIGH:
            high_feature = "拍照"
        elif profile.battery_need == NeedLevel.HIGH:
            high_feature = "续航"

        if not high_feature:
            return None

        for brand in profile.brand_preference:
            normalized_brand = self._normalize_brand(brand)
            if normalized_brand in self.BRAND_SPECIALTY:
                specialties = self.BRAND_SPECIALTY[normalized_brand]
                # 品牌不擅长用户的高需求功能
                if high_feature not in specialties:
                    return {"brand": normalized_brand, "feature": high_feature}

        return None

    def _normalize_brand(self, brand: str) -> str:
        """标准化品牌名称"""
        brand_lower = brand.lower()
        brand_map = {
            "华为": "华为",
            "huawei": "华为",
            "苹果": "苹果",
            "apple": "苹果",
            "iphone": "苹果",
            "小米": "小米",
            "xiaomi": "小米",
            "oppo": "OPPO",
            "vivo": "vivo",
            "三星": "三星",
            "samsung": "三星",
            "荣耀": "荣耀",
            "honor": "荣耀",
            "realme": "realme",
            "红魔": "红魔",
            "redmagic": "红魔",
            "一加": "一加",
            "oneplus": "一加"
        }
        return brand_map.get(brand, brand_map.get(brand_lower, brand))
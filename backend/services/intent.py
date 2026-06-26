from backend.services.llm import LLMService, truncate_messages
from backend.services.need_analysis import NeedAnalysisService
from backend.services.question import QuestionService, PainPointQuestionService
from backend.models.schemas import IntentResult, IntentType, UserProfile
from backend.models.domain import Phone
import json
import logging
import re

logger = logging.getLogger(__name__)

INTENT_PROMPT = """你是一个手机选购助手。分析用户意图并提取关键信息。

{history_context}{profile_context}
用户输入: "{user_message}"

返回JSON格式(不要有其他内容):
{{
  "intent": "recommend或compare或filter",
  "budget_min": 0,
  "budget_max": 10000,
  "brands": ["品牌列表"],
  "features": ["功能需求列表"],
  "no_need_features": ["明确不需要的功能"],
  "phones_mentioned": ["提到的手机型号"],
  "reset_profile": false
}}

intent说明:
- recommend: 用户想要推荐手机
- compare: 用户想对比两款手机
- filter: 用户想按条件筛选

reset_profile说明（重要）:
- 如果用户说"选个新手机"、"重新推荐"、"换个手机"、"我想选个新手机"、"我要选一台新的"、"不要之前的推荐"、"重新来"、"换一个手机"、"重新选一个"、"从头开始"等表示重新开始的意图，设置为 true
- 如果用户说"便宜点的"、"贵点的"、"还有别的吗"等追问补充，设置为 false
- 关键判断：用户是否想完全重新开始（清空之前的所有需求）

预算提取规则（重要）:
- "三千价位" → budget_min=2500, budget_max=3500
- "五千价位" → budget_min=4500, budget_max=5500
- "一万以内" → budget_min=0, budget_max=10000
- 如果用户说具体价格如"3000元左右"，设置 ±500 的范围
- 如果没有明确预算，保持 budget_min=0, budget_max=100000

功能需求(features)提取规则（重要）:
- "玩游戏" → features: ["游戏"]
- "打游戏最好" → features: ["游戏"]
- "拍照好" → features: ["拍照"]
- "拍照清晰" → features: ["拍照"]
- "续航长" → features: ["续航"]
- "电池耐用" → features: ["续航"]
- "充电快" → features: ["快充"]
- "屏幕好" → features: ["屏幕"]
- "性能强" → features: ["性能"]
- 提取用户明确提到的功能需求关键词，不要添加用户未提及的功能

明确不需要的功能(no_need_features)提取规则（非常重要）:
- "不玩游戏" → no_need_features: ["游戏"]
- "不需要游戏" → no_need_features: ["游戏"]
- "不打游戏" → no_need_features: ["游戏"]
- "不拍照" → no_need_features: ["拍照"]
- "不需要拍照" → no_need_features: ["拍照"]
- 当用户明确表示不需要某个功能时，添加到 no_need_features，不要添加到 features

多轮对话规则（重要）:
- 如果用户追问"便宜点的/贵点的"，需要参考历史上下文调整预算
- "便宜点的" → 在原预算基础上降低1000-2000元
- "贵点的" → 在原预算基础上提高1000-2000元
- 如果历史上下文提到过手机型号，用户追问时可能想对比或了解同系列
"""


class IntentService:
    def __init__(self):
        self.llm = LLMService()
        self.need_analysis = NeedAnalysisService()
        self.question = QuestionService()
        self.pain_point = PainPointQuestionService()

    def _fallback_intent_recognition(
        self,
        user_message: str,
        user_profile: UserProfile = None
    ) -> IntentResult:
        """基于规则的降级意图识别（不依赖 LLM）"""
        message_lower = user_message.lower()
        result = {
            "intent": IntentType.RECOMMEND,
            "budget_min": 0,
            "budget_max": 100000,
            "brands": [],
            "features": [],
            "no_need_features": [],
            "phones_mentioned": [],
            "reset_profile": False
        }

        # 检测重置状态意图
        reset_keywords = [
            "新手机", "重新推荐", "换个手机", "重新选", "重新开始", "从头选",
            "选一台新", "选台新", "重选", "不要之前", "换一个手机", "重新来",
            "从头开始", "选个新的", "选一款新", "重新选一个", "重新给我",
            "不想用", "不想要之前", "不要之前的",
        ]
        if any(kw in message_lower for kw in reset_keywords):
            result["reset_profile"] = True

        # 检测对比意图
        if "对比" in message_lower or "比较" in message_lower or "哪个好" in message_lower:
            result["intent"] = IntentType.COMPARE

        # 检测筛选意图
        if "筛选" in message_lower or "过滤" in message_lower or "只看" in message_lower:
            result["intent"] = IntentType.FILTER

        # 提取预算（规则匹配）
        result["budget_min"], result["budget_max"] = self._extract_budget(message_lower)

        # 提取品牌偏好
        result["brands"] = self._extract_brands(message_lower)

        # 提取功能需求（返回元组）
        result["features"], result["no_need_features"] = self._extract_features(message_lower)

        # 构建基础 IntentResult
        intent_result = IntentResult(
            intent=result["intent"],
            budget_min=result["budget_min"],
            budget_max=result["budget_max"],
            brands=result["brands"],
            features=result["features"],
            no_need_features=result["no_need_features"],
            phones_mentioned=result["phones_mentioned"],
            reset_profile=result["reset_profile"]
        )

        # 如果提供了 user_profile，判断需求完整性并生成追问
        if user_profile is not None:
            intent_result = self._enrich_with_clarification(intent_result, user_profile)

        return intent_result

    def _extract_budget(self, message: str) -> tuple:
        """从消息中提取预算范围"""
        budget_min, budget_max = 0, 100000

        # 中文数字映射
        chinese_to_digit = {
            "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
            "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10
        }

        # 匹配中文数字 + 千价位："三千价位"、"两千元"
        chinese_thousand = re.search(r'([一二两三四五六七八九十])千[元价位]*', message)
        if chinese_thousand:
            chinese_num = chinese_thousand.group(1)
            base = chinese_to_digit.get(chinese_num, 0) * 1000
            budget_min = base - 500
            budget_max = base + 500
            return budget_min, budget_max

        # 匹配 "X千价位"、"X千元" 等（阿拉伯数字）
        thousand_match = re.search(r'(\d)千[元价位]*', message)
        if thousand_match:
            base = int(thousand_match.group(1)) * 1000
            budget_min = base - 500
            budget_max = base + 500
            return budget_min, budget_max

        # 匹配中文数字 + 万："一万以内"、"两万以下"
        chinese_wan = re.search(r'([一二两三四五六七八九十])万(?:以内|以下)', message)
        if chinese_wan and chinese_wan.group(1):
            chinese_num = chinese_wan.group(1)
            budget_max = chinese_to_digit.get(chinese_num, 0) * 10000
            return budget_min, budget_max

        # 匹配阿拉伯数字 + 万："1万以内"、"2万以下"
        wan_match = re.search(r'(\d)万(?:以内|以下)', message)
        if wan_match and wan_match.group(1):
            budget_max = int(wan_match.group(1)) * 10000
            return budget_min, budget_max

        # 匹配具体数字 "3000左右"、"3000元左右"
        price_around = re.search(r'(\d{3,5})\s*[元块]?左右', message)
        if price_around:
            base = int(price_around.group(1))
            budget_min = max(0, base - 500)
            budget_max = base + 500
            return budget_min, budget_max

        # 匹配 "X元以内"、"不超过X元"、"X元以下"
        under_price = re.search(r'(\d{3,5})\s*[元块]?(?:以内|以下)|不超过\s*(\d{3,5})\s*[元块]?', message)
        if under_price:
            # group(1) 匹配 "X元以内"，group(2) 匹配 "不超过X"
            if under_price.group(2):
                budget_max = int(under_price.group(2))
            else:
                budget_max = int(under_price.group(1))
            return budget_min, budget_max

        # 匹配范围 "X-Y元"、"X到Y元"
        range_price = re.search(r'(\d{3,5})\s*[到\-]\s*(\d{3,5})\s*[元块]?', message)
        if range_price:
            budget_min = int(range_price.group(1))
            budget_max = int(range_price.group(2))
            return budget_min, budget_max

        return budget_min, budget_max

    def _extract_brands(self, message: str) -> list:
        """从消息中提取品牌偏好"""
        brands = []
        brand_keywords = [
            ("苹果", ["苹果", "iphone", "iPhone"]),
            ("华为", ["华为", "huawei", "Huawei"]),
            ("小米", ["小米", "红米", "xiaomi", "Xiaomi", "redmi", "Redmi"]),
            ("OPPO", ["oppo", "OPPO", "欧珀"]),
            ("vivo", ["vivo", "VIVO", "维沃"]),
            ("荣耀", ["荣耀", "honor", "Honor"]),
            ("三星", ["三星", "samsung", "Samsung"]),
            ("一加", ["一加", "oneplus", "OnePlus"]),
            ("realme", ["realme", "Realme", "真我"]),
            ("魅族", ["魅族", "meizu", "Meizu"])
        ]

        for brand, keywords in brand_keywords:
            for keyword in keywords:
                if keyword in message:
                    brands.append(brand)
                    break

        return list(set(brands))  # 去重

    def _extract_features(self, message: str) -> tuple:
        """从消息中提取功能需求

        Returns:
            tuple: (features, no_need_features)
            - features: 用户需要的功能列表
            - no_need_features: 用户明确表示不需要的功能列表
        """
        features = []
        no_need_features = []

        # 首先检查否定词，如果用户说"不玩游戏"、"不需要游戏"等
        negative_patterns = {
            "游戏": ["不玩游戏", "不需要游戏", "没游戏需求", "不打游戏", "不玩", "没游戏"],
            "拍照": ["不拍照", "不需要拍照", "没拍照需求"],
            "续航": ["不关心续航", "不需要续航"],
        }

        # 检查否定词
        for feature, neg_patterns in negative_patterns.items():
            for pattern in neg_patterns:
                if pattern in message:
                    no_need_features.append(feature)
                    break

        # 功能关键词映射
        feature_keywords = {
            "游戏": ["玩游戏", "打游戏", "电竞", "王者", "原神", "吃鸡", "重度游戏"],
            "拍照": ["拍照", "照相", "摄影", "相机", "自拍", "影像", "夜景"],
            "续航": ["续航", "电池", "电量", "耐用"],
            "快充": ["快充", "充电快", "闪充", "充电要快"],
            "性能": ["性能", "流畅", "不卡", "处理器", "芯片"],
            "屏幕": ["屏幕", "显示", "护眼", "高刷", "刷新率"],
            "存储": ["存储", "内存", "容量", "空间"]
        }

        for feature, keywords in feature_keywords.items():
            # 如果用户明确表示不需要这个功能，跳过
            if feature in no_need_features:
                continue
            for keyword in keywords:
                if keyword in message:
                    features.append(feature)
                    break

        return list(set(features)), list(set(no_need_features))  # 去重

    def _extract_json_from_response(self, response: str) -> dict:
        """从LLM响应中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON块
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None

    async def recognize(
        self,
        user_message: str,
        history: list = None,
        user_profile: UserProfile = None
    ) -> IntentResult:
        """识别用户意图

        Args:
            user_message: 用户当前输入
            history: 历史消息列表，格式 [{"role": "user/assistant", "content": "..."}]
            user_profile: 当前用户画像，用于需求完整性判断和追问生成
        """
        # 构建历史上下文
        history_context = ""
        if history and len(history) > 0:
            # 使用统一的截断方法处理历史消息
            truncated_history = truncate_messages(history, max_messages=6)
            history_lines = []
            for msg in truncated_history:
                role = "用户" if msg["role"] == "user" else "助手"
                history_lines.append(f"{role}: {msg['content']}")
            history_context = "历史对话:\n" + "\n".join(history_lines) + "\n\n"

        # 构建用户画像上下文
        profile_context = ""
        if user_profile is not None:
            profile_context = self._build_profile_context(user_profile)

        # 转义用户输入中的花括号，防止 str.format() KeyError DoS
        safe_user_message = user_message.replace("{", "{{").replace("}", "}}")
        safe_history = history_context.replace("{", "{{").replace("}", "}}")

        prompt = INTENT_PROMPT.format(
            user_message=safe_user_message,
            history_context=safe_history,
            profile_context=profile_context
        )
        response = await self.llm.chat([{"role": "user", "content": prompt}])

        try:
            data = self._extract_json_from_response(response)
            if data is None:
                logger.warning(f"Intent JSON parse failed, raw response: {response[:200]}")
                return self._fallback_intent_recognition(user_message, user_profile)

            # 记录 LLM 返回的数据
            logger.info(f"Intent LLM response: {data}")

            # 构建基础 IntentResult
            intent_result = IntentResult(
                intent=IntentType(data.get("intent", "recommend")),
                budget_min=data.get("budget_min", 0),
                budget_max=data.get("budget_max", 100000),
                brands=data.get("brands", []),
                features=data.get("features", []),
                no_need_features=data.get("no_need_features", []),
                phones_mentioned=data.get("phones_mentioned", []),
                reset_profile=data.get("reset_profile", False)
            )

            # 补充规则提取的 no_need_features（LLM 可能遗漏，导致"不玩游戏"无法结束追问）
            rule_features, rule_no_need = self._extract_features(user_message)
            if rule_no_need:
                merged_no_need = list(set(
                    (intent_result.no_need_features or []) + rule_no_need
                ))
                intent_result.no_need_features = merged_no_need
                logger.info(
                    "Merged no_need_features from rules: %s -> %s",
                    rule_no_need, merged_no_need,
                )

            # 记录 no_need_features
            logger.info(f"no_need_features: {intent_result.no_need_features}")

            # 如果提供了 user_profile，判断需求完整性并生成追问
            if user_profile is not None:
                intent_result = self._enrich_with_clarification(
                    intent_result, user_profile
                )

            return intent_result
        except ValueError as e:
            logger.warning(f"Intent recognition error: {e}, raw response: {response[:200]}")
            return self._fallback_intent_recognition(user_message, user_profile)

    def _build_profile_context(self, user_profile: UserProfile) -> str:
        """
        构建用户画像上下文，用于 prompt

        Args:
            user_profile: 用户画像

        Returns:
            str: 格式化的用户画像上下文
        """
        parts = []

        # 预算信息
        if user_profile.budget_min is not None or user_profile.budget_max is not None:
            budget_parts = []
            if user_profile.budget_min is not None:
                budget_parts.append(f"{user_profile.budget_min}元")
            if user_profile.budget_max is not None:
                budget_parts.append(f"{user_profile.budget_max}元")
            if len(budget_parts) == 2:
                parts.append(f"预算范围: {budget_parts[0]}-{budget_parts[1]}")
            else:
                parts.append(f"预算: {'以内'.join(budget_parts)}")

        # 功能需求
        feature_parts = []
        if user_profile.gaming_need is not None:
            feature_parts.append(f"游戏需求({user_profile.gaming_need.value})")
        if user_profile.camera_need is not None:
            feature_parts.append(f"拍照需求({user_profile.camera_need.value})")
        if user_profile.battery_need is not None:
            feature_parts.append(f"续航需求({user_profile.battery_need.value})")

        if feature_parts:
            parts.append("功能需求: " + ", ".join(feature_parts))

        # 品牌偏好
        if user_profile.brand_preference:
            parts.append(f"品牌偏好: {', '.join(user_profile.brand_preference)}")

        if parts:
            return "当前已收集的用户需求:\n" + "\n".join(parts) + "\n\n"
        return ""

    def _enrich_with_clarification(
        self,
        intent_result: IntentResult,
        user_profile: UserProfile,
        phones: list[Phone] = None
    ) -> IntentResult:
        """
        使用需求分析和追问服务丰富 IntentResult

        优先检测痛点（预算与需求冲突），若存在痛点则返回痛点追问，
        否则检查需求完整性并返回普通追问。

        Args:
            intent_result: 基础意图识别结果
            user_profile: 用户画像
            phones: 可选的手机列表，用于更精确的痛点检测

        Returns:
            IntentResult: 包含追问信息的意图结果
        """
        # 1. 优先检测痛点（预算与需求冲突）
        pain_point_response = self.pain_point.generate_pain_point_question(
            user_profile, phones
        )

        if pain_point_response:
            # 存在痛点，返回痛点追问
            logger.info(
                f"Pain point detected: {pain_point_response.pain_point_type}, "
                f"severity: {pain_point_response.severity}"
            )
            return IntentResult(
                intent=intent_result.intent,
                budget_min=intent_result.budget_min,
                budget_max=intent_result.budget_max,
                brands=intent_result.brands,
                features=intent_result.features,
                no_need_features=intent_result.no_need_features,
                phones_mentioned=intent_result.phones_mentioned,
                reset_profile=intent_result.reset_profile,
                need_clarification=True,
                missing_fields=[],
                clarification_question=pain_point_response.question,
                pain_point_detected=True,
                pain_point_type=pain_point_response.pain_point_type,
                pain_point_severity=pain_point_response.severity
            )

        # 2. 无痛点，检查需求完整性
        analysis = self.need_analysis.analyze(user_profile)

        if not analysis.is_complete:
            # 生成追问响应
            question_response = self.question.generate_full_response(user_profile)

            return IntentResult(
                intent=intent_result.intent,
                budget_min=intent_result.budget_min,
                budget_max=intent_result.budget_max,
                brands=intent_result.brands,
                features=intent_result.features,
                no_need_features=intent_result.no_need_features,
                phones_mentioned=intent_result.phones_mentioned,
                reset_profile=intent_result.reset_profile,
                need_clarification=True,
                missing_fields=question_response.missing_fields,
                clarification_question=question_response.question,
                pain_point_detected=False
            )

        return intent_result
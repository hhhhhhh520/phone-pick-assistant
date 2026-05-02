from sqlalchemy.orm import Session
from backend.models.domain import Phone, get_antutu_score
from typing import List
from sqlalchemy import case


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db

    def get_phones_by_budget(self, min_price: int, max_price: int, limit: int = 10) -> List[Phone]:
        """按预算筛选，优先返回有图片的"""
        return self.db.query(Phone).filter(
            Phone.price > 0,  # 过滤无效价格
            Phone.price >= min_price,
            Phone.price <= max_price
        ).order_by(
            # 有图片的排前面
            case(
                (Phone.image_url.isnot(None), 0),
                else_=1
            ),
            Phone.price
        ).limit(limit).all()

    def get_phones_by_brand(self, brands: List[str], limit: int = 10) -> List[Phone]:
        """按品牌筛选，优先返回有图片的"""
        return self.db.query(Phone).filter(
            Phone.brand.in_(brands)
        ).order_by(
            case(
                (Phone.image_url.isnot(None), 0),
                else_=1
            )
        ).limit(limit).all()

    def get_phones_by_model(self, models: List[str]) -> List[Phone]:
        """按型号查找，优先返回有图片且价格有效的"""
        phones = []
        for model in models:
            # 优先级1: 精确匹配完整型号（如"小米14"）
            phone = self.db.query(Phone).filter(
                Phone.price > 0,
                Phone.model == model
            ).first()

            # 优先级2: 完整型号作为子串匹配（如"小米14"匹配"小米14 Ultra"）
            if not phone:
                phone = self.db.query(Phone).filter(
                    Phone.price > 0,
                    Phone.model.contains(model)
                ).order_by(
                    # 优先匹配最短的型号（避免"小米14"匹配到"小米14 Ultra"）
                    case(
                        (Phone.image_url.isnot(None), 0),
                        else_=1
                    ),
                    Phone.price
                ).first()

            # 优先级3: 提取核心型号匹配（如"小米14" -> "14"，但必须同品牌）
            if not phone:
                # 提取品牌和核心型号
                brand_prefix = None
                model_core = model
                for brand in ["小米", "华为", "苹果", "OPPO", "vivo", "荣耀", "Redmi", "realme"]:
                    if model.startswith(brand):
                        brand_prefix = brand
                        model_core = model[len(brand):].strip()
                        break

                if brand_prefix and model_core:
                    # 必须同时匹配品牌和核心型号
                    phone = self.db.query(Phone).filter(
                        Phone.price > 0,
                        Phone.brand == brand_prefix,
                        Phone.model.contains(model_core)
                    ).order_by(
                        case(
                            (Phone.image_url.isnot(None), 0),
                            else_=1
                        ),
                        Phone.price
                    ).first()

            if phone:
                phones.append(phone)
        return phones

    def _build_feature_filters(self, features: List[str]) -> tuple:
        """构建场景筛选条件

        Args:
            features: 场景需求列表，如 ["游戏", "拍照", "续航"]

        Returns:
            (or_conditions, battery_threshold) 元组
            - or_conditions: suitable_for 或 features 字段的匹配条件列表
            - battery_threshold: 电池容量阈值（用于续航场景）
        """
        or_conditions = []
        battery_threshold = None

        for feature in features:
            feature_lower = feature.lower()

            if feature_lower == "游戏":
                # 游戏：suitable_for 包含 "游戏玩家" 或 features 包含 "游戏"/"电竞"
                or_conditions.append(
                    (Phone.suitable_for.contains("游戏玩家")) |
                    (Phone.features.contains("游戏")) |
                    (Phone.features.contains("电竞"))
                )
            elif feature_lower == "拍照":
                # 拍照：suitable_for 包含 "摄影" 或 features 包含影像相关关键词
                or_conditions.append(
                    (Phone.suitable_for.contains("摄影")) |
                    (Phone.features.contains("影像")) |
                    (Phone.features.contains("徕卡")) |
                    (Phone.features.contains("哈苏")) |
                    (Phone.features.contains("蔡司"))
                )
            elif feature_lower == "续航":
                # 续航：suitable_for 包含 "续航" 或 battery >= 5000
                or_conditions.append(Phone.suitable_for.contains("续航"))
                battery_threshold = 5000

        return or_conditions, battery_threshold

    def _sort_by_scenario(self, phones: List[Phone], features_lower: List[str]) -> List[Phone]:
        """根据场景需求对手机进行智能排序

        Args:
            phones: 手机列表
            features_lower: 小写化的场景需求列表

        Returns:
            排序后的手机列表
        """
        # 判断主要场景（优先级：游戏 > 拍照 > 续航）
        if "游戏" in features_lower:
            # 游戏场景：安兔兔跑分 > 内存 > 电池 > 价格
            def game_sort_key(phone):
                antutu_score = get_antutu_score(phone.processor) if phone.processor else 0
                ram = phone.ram or 0
                battery = phone.battery or 0
                # 降序排列，取负值
                return (-antutu_score, -ram, -battery, phone.price)
            return sorted(phones, key=game_sort_key)

        elif "拍照" in features_lower:
            # 拍照场景：主摄像素降序
            return sorted(phones, key=lambda p: -(p.camera_main or 0))

        elif "续航" in features_lower:
            # 续航场景：电池容量降序
            return sorted(phones, key=lambda p: -(p.battery or 0))

        else:
            # 默认：价格升序
            return sorted(phones, key=lambda p: p.price)

    def search(self, intent_result, limit: int = 10) -> List[Phone]:
        """综合搜索，优先返回有图片的"""
        query = self.db.query(Phone)

        # 过滤掉无效价格（price=0或null）
        query = query.filter(Phone.price > 0)

        # 预算筛选
        if intent_result.budget_min > 0 or intent_result.budget_max < 100000:
            query = query.filter(
                Phone.price >= intent_result.budget_min,
                Phone.price <= intent_result.budget_max
            )

        # 品牌筛选
        if intent_result.brands:
            query = query.filter(Phone.brand.in_(intent_result.brands))

        # 场景筛选
        if intent_result.features:
            or_conditions, battery_threshold = self._build_feature_filters(intent_result.features)

            # 应用 OR 条件（任一场景匹配即可）
            if or_conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*or_conditions))

            # 续航场景额外筛选电池容量
            if battery_threshold is not None:
                query = query.filter(Phone.battery >= battery_threshold)

        # 场景感知排序
        phones = query.order_by(
            # 有图片的排前面
            case(
                (Phone.image_url.isnot(None), 0),
                else_=1
            )
        ).limit(limit * 2).all()  # 多取一些用于重排序

        # 根据场景进行智能排序
        if intent_result.features:
            features_lower = [f.lower() for f in intent_result.features]
            phones = self._sort_by_scenario(phones, features_lower)
        else:
            # 默认按价格升序
            phones = sorted(phones, key=lambda p: p.price)

        return phones[:limit]

    def get_all_phones(self, limit: int = 20) -> List[Phone]:
        """获取所有手机，优先返回有图片的"""
        return self.db.query(Phone).filter(
            Phone.price > 0  # 过滤无效价格
        ).order_by(
            case(
                (Phone.image_url.isnot(None), 0),
                else_=1
            )
        ).limit(limit).all()

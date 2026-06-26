from sqlalchemy.orm import Session
from backend.models.domain import Phone, get_antutu_score
from typing import List, Optional
from sqlalchemy import case, or_
import re


def _safe_battery_value(battery) -> int:
    """
    安全地提取电池容量数值。

    数据库中 battery 字段可能是:
    - int: 5000
    - str: "5000mAh"
    - None

    Args:
        battery: 电池字段原始值

    Returns:
        int: 电池容量(mAh)，解析失败返回0
    """
    if battery is None:
        return 0

    if isinstance(battery, int):
        return battery

    if isinstance(battery, str):
        # 提取字符串中的数字
        match = re.search(r'(\d+)', battery)
        if match:
            return int(match.group(1))

    return 0


def _safe_ram_value(ram) -> int:
    """
    安全地提取内存大小数值。

    数据库中 ram 字段可能是:
    - int: 8
    - str: "8GB"
    - str: "6GB游戏..." (带额外描述)
    - None

    Args:
        ram: 内存字段原始值

    Returns:
        int: 内存大小(GB)，解析失败返回0
    """
    if ram is None:
        return 0

    if isinstance(ram, int):
        return ram

    if isinstance(ram, str):
        # 提取字符串中的数字
        match = re.search(r'(\d+)', ram)
        if match:
            return int(match.group(1))

    return 0


def _parse_camera_mp(value) -> Optional[int]:
    """Parse camera_main text to 万pixel integer.

    '5000万' -> 5000, '2亿' -> 20000, '1.08亿' -> 10800

    Args:
        value: 原始camera_main值（TEXT如"5000万"、"2亿"、INTEGER、或None）

    Returns:
        int: 像素值(万)，解析失败返回None
    """
    if value is None:
        return None
    s = str(value).strip()
    # Handle 亿 (hundred million)
    yi_match = re.search(r'([\d.]+)\s*亿', s)
    if yi_match:
        return int(float(yi_match.group(1)) * 10000)
    # Handle 万
    wan_match = re.search(r'([\d.]+)\s*万', s)
    if wan_match:
        return int(float(wan_match.group(1)))
    # Fallback: pure number
    num_match = re.search(r'(\d+)', s)
    if num_match:
        return int(num_match.group(1))
    return None


def _safe_camera_value(camera_main) -> int:
    """
    安全地提取主摄像素数值（万像素）。

    数据库中 camera_main 字段可能是:
    - int: 5000 (万像素)
    - str: "5000万" / "2亿" / "1.08亿"
    - None

    Args:
        camera_main: 主摄字段原始值

    Returns:
        int: 主摄像素(万像素)，解析失败返回0
    """
    result = _parse_camera_mp(camera_main)
    return result if result is not None else 0


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
                # 游戏场景：筛选 features 包含 '游戏' 或 '电竞' 的手机
                # 同时筛选 suitable_for 包含 '游戏玩家'
                or_conditions.append(
                    or_(
                        Phone.features.contains("游戏"),
                        Phone.features.contains("电竞"),
                        Phone.suitable_for.contains("游戏玩家")
                    )
                )
            elif feature_lower == "拍照":
                # 拍照场景：筛选 features 包含 '徕卡'/'哈苏'/'蔡司'
                # 或 suitable_for 包含 '摄影爱好者'
                or_conditions.append(
                    or_(
                        Phone.features.contains("徕卡"),
                        Phone.features.contains("哈苏"),
                        Phone.features.contains("蔡司"),
                        Phone.suitable_for.contains("摄影爱好者")
                    )
                )
            elif feature_lower == "续航":
                # 续航：筛选 features 包含 '大电池' 或 '快充'
                # 或 suitable_for 包含 '续航'，或 battery >= 5000
                or_conditions.append(
                    or_(
                        Phone.features.contains("大电池"),
                        Phone.features.contains("快充"),
                        Phone.suitable_for.contains("续航")
                    )
                )
                battery_threshold = 5000
            elif feature_lower == "性能":
                # 性能场景：不添加DB筛选，所有手机都是候选，依赖 _sort_by_scenario 按跑分排序
                pass
            elif "无线" in feature_lower or "wireless" in feature_lower:
                # 无线充电：charging_wireless > 0 表示支持无线充电
                or_conditions.append(Phone.charging_wireless > 0)

        return or_conditions, battery_threshold

    def _sort_by_scenario(self, phones: List[Phone], features_lower: List[str], no_need_features: List[str] = None) -> List[Phone]:
        """根据场景需求对手机进行智能排序

        Args:
            phones: 手机列表
            features_lower: 小写化的场景需求列表
            no_need_features: 用户明确不需要的功能列表

        Returns:
            排序后的手机列表
        """
        no_need_features = no_need_features or []

        # 判断主要场景（优先级：游戏 > 拍照 > 续航）
        if "游戏" in features_lower:
            # 游戏场景：安兔兔跑分 > 内存 > 电池 > 价格
            def game_sort_key(phone):
                antutu_score = get_antutu_score(phone.processor) if phone.processor else 0
                ram = _safe_ram_value(phone.ram)
                battery = _safe_battery_value(phone.battery)
                # 降序排列，取负值
                return (-antutu_score, -ram, -battery, phone.price)
            return sorted(phones, key=game_sort_key)

        elif "拍照" in features_lower:
            # 拍照场景：按主摄像素降序，同像素时影像标签优先
            def camera_sort_key(phone):
                """拍照排序键：像素降序，同像素时影像标签优先"""
                camera_pixels = _safe_camera_value(phone.camera_main)
                # 判断是否有影像标签（徕卡、哈苏、蔡司、潜望长焦等）
                features_str = phone.features or ""
                has_photo_tag = any(tag in features_str for tag in ["徕卡", "哈苏", "蔡司", "影像", "潜望长焦"])
                # 像素降序(取负)，影像标签优先(0在前)，价格升序
                return (-camera_pixels, 0 if has_photo_tag else 1, phone.price)

            return sorted(phones, key=camera_sort_key)

        elif "性能" in features_lower:
            # 性能场景：安兔兔跑分 > 内存 > 价格
            def perf_sort_key(phone):
                antutu_score = get_antutu_score(phone.processor) if phone.processor else 0
                ram = _safe_ram_value(phone.ram)
                return (-antutu_score, -ram, phone.price)
            return sorted(phones, key=perf_sort_key)

        elif "续航" in features_lower:
            # 续航场景：电池容量降序
            return sorted(phones, key=lambda p: -_safe_battery_value(p.battery))

        # 处理 no_need_features：用户明确不需要的功能
        elif any(f.lower() in ["游戏", "拍照", "性能"] for f in no_need_features):
            # 用户不需要游戏/拍照/性能 → 推荐"日常使用流畅"的手机
            # 排序标准：处理器性能足够日常（安兔兔40万分以上）+ 大电池 + 价格低
            def daily_use_sort_key(phone):
                antutu_score = get_antutu_score(phone.processor) if phone.processor else 0
                battery = _safe_battery_value(phone.battery)
                # 日常使用：处理器够用就行（40万分阈值），电池大优先，价格低优先
                # 安兔兔分数：40万分以上得0分（足够），以下得负分（不够）
                antutu_penalty = 0 if antutu_score >= 400000 else -(400000 - antutu_score)
                return (antutu_penalty, -battery, phone.price)
            return sorted(phones, key=daily_use_sort_key)

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
                query = query.filter(or_(*or_conditions))

            # 续航场景额外筛选电池容量
            if battery_threshold is not None:
                query = query.filter(Phone.battery >= battery_threshold)

        # 场景感知排序
        if intent_result.features or intent_result.no_need_features:
            # 有场景需求或明确不需要的功能时：取全部候选(无ORDER BY)，用场景排序重排
            phones = query.all()
            features_lower = [f.lower() for f in intent_result.features]
            no_need_lower = [f.lower() for f in (intent_result.no_need_features or [])]
            phones = self._sort_by_scenario(phones, features_lower, no_need_lower)
            # 场景排序后，同分优先有图片（稳定排序：先排图片，再排场景，场景为主键）
        else:
            # 无场景需求：优先有图片，按价格排序
            phones = query.order_by(
                case(
                    (Phone.image_url.isnot(None), 0),
                    else_=1
                ),
                Phone.price
            ).limit(limit * 2).all()
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

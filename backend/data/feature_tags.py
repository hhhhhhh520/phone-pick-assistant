"""
手机特性标签库

定义系统化的 features 和 suitable_for 标签，用于智能匹配和推荐。
"""

from typing import Dict, List, Any


# 特性标签定义
# 每个标签包含：
# - name: 标签名称
# - keywords: 关键词列表（用于文本匹配）
# - param_rules: 参数匹配规则

FEATURE_TAGS: Dict[str, Dict[str, Any]] = {
    # 游戏相关
    "游戏手机": {
        "name": "游戏手机",
        "keywords": ["游戏", "电竞", "游戏手机", "gaming"],
        "param_rules": [
            {"field": "processor", "op": "contains", "value": ["骁龙8", "骁龙7+", "天玑9000", "天玑9200"]},
        ]
    },
    "高刷屏": {
        "name": "高刷屏",
        "keywords": ["高刷", "高刷新率", "120Hz", "144Hz", "电竞屏"],
        "param_rules": [
            {"field": "screen", "op": "contains", "value": ["120Hz", "144Hz", "165Hz"]},
        ]
    },
    "电竞散热": {
        "name": "电竞散热",
        "keywords": ["散热", "电竞散热", "液冷", "VC散热", "石墨烯"],
        "param_rules": []
    },

    # 拍照相关
    "徕卡影像": {
        "name": "徕卡影像",
        "keywords": ["徕卡", "Leica", "徕卡影像"],
        "param_rules": []
    },
    "哈苏影像": {
        "name": "哈苏影像",
        "keywords": ["哈苏", "Hasselblad", "哈苏影像"],
        "param_rules": []
    },
    "蔡司影像": {
        "name": "蔡司影像",
        "keywords": ["蔡司", "Zeiss", "蔡司影像"],
        "param_rules": []
    },
    "潜望长焦": {
        "name": "潜望长焦",
        "keywords": ["潜望", "长焦", "潜望长焦", "100x", "120x"],
        "param_rules": []
    },
    "人像大师": {
        "name": "人像大师",
        "keywords": ["人像", "人像大师", "人像模式"],
        "param_rules": []
    },
    "夜景拍摄": {
        "name": "夜景拍摄",
        "keywords": ["夜景", "夜拍", "暗光拍摄"],
        "param_rules": []
    },

    # 续航相关
    "快充": {
        "name": "快充",
        "keywords": ["快充", "闪充", "超级快充", "67W", "120W", "150W"],
        "param_rules": [
            {"field": "charging_wired", "op": ">=", "value": 67},
        ]
    },
    "大电池": {
        "name": "大电池",
        "keywords": ["大电池", "长续航", "5000mAh", "5500mAh", "6000mAh"],
        "param_rules": [
            {"field": "battery", "op": ">=", "value": 5000},
        ]
    },
    "无线充电": {
        "name": "无线充电",
        "keywords": ["无线充电", "Qi", "无线快充"],
        "param_rules": [
            {"field": "charging_wireless", "op": ">", "value": 0},
        ]
    },

    # 商务相关
    "卫星通信": {
        "name": "卫星通信",
        "keywords": ["卫星", "卫星通信", "北斗", "天通"],
        "param_rules": []
    },
    "IP68防水": {
        "name": "IP68防水",
        "keywords": ["IP68", "防水", "防尘", "IP68防水"],
        "param_rules": []
    },

    # 屏幕相关
    "AMOLED屏": {
        "name": "AMOLED屏",
        "keywords": ["AMOLED", "OLED", "Super AMOLED"],
        "param_rules": []
    },
    "折叠屏": {
        "name": "折叠屏",
        "keywords": ["折叠", "折叠屏", "Fold", "Flip"],
        "param_rules": []
    },
    "曲面屏": {
        "name": "曲面屏",
        "keywords": ["曲面", "曲面屏", "微曲"],
        "param_rules": []
    },

    # 性能相关
    "旗舰芯片": {
        "name": "旗舰芯片",
        "keywords": ["旗舰", "骁龙8", "天玑9000"],
        "param_rules": [
            {"field": "processor", "op": "contains", "value": ["骁龙8 Gen", "天玑9"]},
        ]
    },

    # 外观相关
    "轻薄机身": {
        "name": "轻薄机身",
        "keywords": ["轻薄", "轻薄机身", "超薄"],
        "param_rules": []
    },

    # 存储相关
    "大存储": {
        "name": "大存储",
        "keywords": ["大存储", "大内存", "512GB", "1TB"],
        "param_rules": [
            {"field": "storage", "op": ">=", "value": 512},
        ]
    },
}


# 适用人群标签定义
SUITABLE_FOR_TAGS: Dict[str, Dict[str, Any]] = {
    "游戏玩家": {
        "name": "游戏玩家",
        "keywords": ["游戏", "电竞", "玩家"],
        "required_features": ["游戏手机", "高刷屏"],
        "param_rules": []
    },
    "摄影爱好者": {
        "name": "摄影爱好者",
        "keywords": ["摄影", "拍照", "影像"],
        "required_features": ["潜望长焦"],
        "param_rules": []
    },
    "商务人士": {
        "name": "商务人士",
        "keywords": ["商务", "办公", "出差"],
        "required_features": ["IP68防水"],
        "param_rules": []
    },
    "学生党": {
        "name": "学生党",
        "keywords": ["学生", "性价比", "预算有限"],
        "required_features": [],
        "param_rules": [
            {"field": "price", "op": "<=", "value": 2500},
        ]
    },
    "长辈机": {
        "name": "长辈机",
        "keywords": ["长辈", "老人", "父母", "简单"],
        "required_features": ["大电池"],
        "param_rules": []
    },
    "性价比党": {
        "name": "性价比党",
        "keywords": ["性价比", "便宜", "实惠"],
        "required_features": [],
        "param_rules": []
    },
    "内容创作者": {
        "name": "内容创作者",
        "keywords": ["创作", "视频", "Vlog", "剪辑"],
        "required_features": ["大存储"],
        "param_rules": []
    },
    "户外爱好者": {
        "name": "户外爱好者",
        "keywords": ["户外", "旅行", "露营"],
        "required_features": ["大电池", "IP68防水"],
        "param_rules": []
    },
    "科技发烧友": {
        "name": "科技发烧友",
        "keywords": ["发烧", "科技", "极客", "旗舰"],
        "required_features": ["旗舰芯片"],
        "param_rules": []
    },
    "社交达人": {
        "name": "社交达人",
        "keywords": ["社交", "自拍", "人像"],
        "required_features": ["人像大师"],
        "param_rules": []
    },
    "重度用户": {
        "name": "重度用户",
        "keywords": ["重度", "高强度", "长时间"],
        "required_features": ["大电池", "快充"],
        "param_rules": []
    },
    "轻商务": {
        "name": "轻商务",
        "keywords": ["轻商务", "简约", "质感"],
        "required_features": [],
        "param_rules": []
    },
}


def get_feature_tag_names() -> List[str]:
    """获取所有特性标签名称"""
    return list(FEATURE_TAGS.keys())


def get_suitable_for_tag_names() -> List[str]:
    """获取所有适用人群标签名称"""
    return list(SUITABLE_FOR_TAGS.keys())


def find_matching_feature_tags(phone_data: Dict[str, Any]) -> List[str]:
    """
    根据手机参数匹配特性标签

    Args:
        phone_data: 手机参数字典

    Returns:
        匹配的标签名称列表
    """
    matched_tags = []

    for tag_name, tag_info in FEATURE_TAGS.items():
        # 检查关键词匹配
        keywords = tag_info.get("keywords", [])
        for keyword in keywords:
            # 在型号、处理器、屏幕等字段中搜索关键词
            for field in ["model", "processor", "screen", "features"]:
                value = str(phone_data.get(field, ""))
                if keyword.lower() in value.lower():
                    matched_tags.append(tag_name)
                    break
            if tag_name in matched_tags:
                break

        # 检查参数规则匹配
        if tag_name not in matched_tags:
            param_rules = tag_info.get("param_rules", [])
            for rule in param_rules:
                if check_param_rule(phone_data, rule):
                    matched_tags.append(tag_name)
                    break

    return list(set(matched_tags))  # 去重


def find_matching_suitable_for_tags(phone_data: Dict[str, Any]) -> List[str]:
    """
    根据手机参数匹配适用人群标签

    Args:
        phone_data: 手机参数字典

    Returns:
        匹配的标签名称列表
    """
    matched_tags = []

    for tag_name, tag_info in SUITABLE_FOR_TAGS.items():
        # 检查参数规则匹配
        param_rules = tag_info.get("param_rules", [])
        for rule in param_rules:
            if check_param_rule(phone_data, rule):
                matched_tags.append(tag_name)
                break

    return list(set(matched_tags))


def check_param_rule(phone_data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """
    检查单个参数规则是否匹配

    Args:
        phone_data: 手机参数字典
        rule: 规则字典，包含 field, op, value

    Returns:
        是否匹配
    """
    field = rule.get("field")
    op = rule.get("op")
    value = rule.get("value")

    if not field or not op:
        return False

    phone_value = phone_data.get(field)
    if phone_value is None:
        return False

    # 处理字符串类型的字段
    if isinstance(phone_value, str):
        phone_value_str = phone_value.lower()
        if op == "contains":
            if isinstance(value, list):
                return any(v.lower() in phone_value_str for v in value)
            return str(value).lower() in phone_value_str

    # 处理数值类型的字段
    try:
        phone_num = float(phone_value) if not isinstance(phone_value, (int, float)) else phone_value
        if op == ">=":
            return phone_num >= value
        elif op == ">":
            return phone_num > value
        elif op == "<=":
            return phone_num <= value
        elif op == "<":
            return phone_num < value
        elif op == "==":
            return phone_num == value
    except (ValueError, TypeError):
        pass

    return False


def suggest_tags_from_text(text: str) -> List[str]:
    """
    从用户输入文本中提取标签建议

    Args:
        text: 用户输入文本

    Returns:
        建议的标签名称列表
    """
    suggested = []
    text_lower = text.lower()

    # 检查特性标签关键词
    for tag_name, tag_info in FEATURE_TAGS.items():
        keywords = tag_info.get("keywords", [])
        if any(kw.lower() in text_lower for kw in keywords):
            suggested.append(tag_name)

    # 检查适用人群标签关键词
    for tag_name, tag_info in SUITABLE_FOR_TAGS.items():
        keywords = tag_info.get("keywords", [])
        if any(kw.lower() in text_lower for kw in keywords):
            suggested.append(tag_name)

    return list(set(suggested))


def get_tag_statistics() -> Dict[str, Any]:
    """获取标签库统计信息"""
    return {
        "feature_tags_count": len(FEATURE_TAGS),
        "suitable_for_tags_count": len(SUITABLE_FOR_TAGS),
        "feature_tags": list(FEATURE_TAGS.keys()),
        "suitable_for_tags": list(SUITABLE_FOR_TAGS.keys())
    }


def validate_tags() -> Dict[str, Any]:
    """验证标签定义的完整性"""
    errors = []

    # 检查特性标签
    for tag_name, tag_info in FEATURE_TAGS.items():
        if "name" not in tag_info:
            errors.append(f"FEATURE_TAGS['{tag_name}'] 缺少 'name' 字段")
        if "keywords" not in tag_info:
            errors.append(f"FEATURE_TAGS['{tag_name}'] 缺少 'keywords' 字段")
        if "param_rules" not in tag_info:
            errors.append(f"FEATURE_TAGS['{tag_name}'] 缺少 'param_rules' 字段")

    # 检查适用人群标签
    for tag_name, tag_info in SUITABLE_FOR_TAGS.items():
        if "name" not in tag_info:
            errors.append(f"SUITABLE_FOR_TAGS['{tag_name}'] 缺少 'name' 字段")
        if "keywords" not in tag_info:
            errors.append(f"SUITABLE_FOR_TAGS['{tag_name}'] 缺少 'keywords' 字段")
        if "param_rules" not in tag_info:
            errors.append(f"SUITABLE_FOR_TAGS['{tag_name}'] 缺少 'param_rules' 字段")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "feature_tags_count": len(FEATURE_TAGS),
        "suitable_for_tags_count": len(SUITABLE_FOR_TAGS)
    }

"""
影像评分配置数据
================

基于知乎文章《2025年手机影像能力排行榜》的评分体系
来源：知乎影像评测团队

评分维度：
1. 芯片算力评分（权重30%）- 基于安兔兔跑分
2. 影像硬件评分（权重40%）- 主摄+长焦+OIS
3. 影像算法评分（权重30%）- 影像品牌/联名

综合评分 = 芯片算力分 + 影像硬件分 + 影像算法分
满分 = 30 + 40 + 30 = 100分
"""

from typing import Optional


# =============================================================================
# 芯片算力评分配置（权重30%）
# 基于安兔兔跑分分级
# =============================================================================

CHIP_SCORE_CONFIG = {
    # 芯片名称 -> (安兔兔跑分范围, 基础分数)
    # 顶级旗舰：200万+ 跑分
    "骁龙8至尊版Gen5": (2_000_000, 30),
    "骁龙8 Elite": (2_000_000, 30),  # 别名
    "天玑9500": (2_000_000, 30),
    "骁龙8 Gen4": (2_000_000, 30),  # 部分文献命名

    # 旗舰级：130-200万跑分
    "骁龙8 Gen3": (1_300_000, 25),
    "天玑9300": (1_300_000, 25),
    "天玑9300+": (1_300_000, 25),
    "骁龙8 Gen2": (900_000, 22),  # 归类为高端
    "天玑9200": (900_000, 22),
    "天玑9200+": (900_000, 22),
    "骁龙8+": (900_000, 22),

    # 中端级：60-90万跑分
    "骁龙7+ Gen3": (600_000, 18),
    "骁龙7+ Gen2": (600_000, 18),
    "天玑8300": (600_000, 18),
    "骁龙7 Gen3": (600_000, 16),

    # 入门级：<60万跑分
    "天玑6020": (0, 10),
    "骁龙6 Gen1": (0, 10),
    "天玑700": (0, 10),
    "骁龙480": (0, 8),
}

# 影像芯片加成分数
IMAGE_CHIP_BONUS = {
    "V3+": 3,   # vivo 自研影像芯片
    "V3": 3,    # vivo V系列
    "V2": 3,
    "MariSilicon": 3,  # OPPO 马里亚纳
    "MariSilicon X": 3,
    "彭拜": 2,   # 小米彭拜（加分略低）
    "彭拜C1": 2,
    "彭拜G1": 2,
}

# 芯片档次基础分数（当芯片名称不在配置中时使用）
CHIP_TIER_BASE_SCORES = {
    "顶级旗舰": 30,
    "旗舰级": 25,
    "高端级": 22,
    "中端级": 16,
    "入门级": 10,
}


# =============================================================================
# 影像硬件评分配置（权重40%）
# 主摄传感器（15分）+ 长焦配置（15分）+ OIS（5分）+ 影像芯片加成（5分）
# =============================================================================

# 主摄传感器评分（满分15分）
# 基于传感器尺寸和型号
SENSOR_SCORE_CONFIG = {
    # 1英寸大底（顶级）
    "LYT-900": 15,
    "IMX989": 15,

    # 1/1.28"-1/1.4"（旗舰级）
    "LYT-818": 12,
    "LYT-808": 12,
    "OV50H": 12,
    "GN1": 12,

    # 1/1.5"-1/1.56"（高端）
    "IMX921": 10,
    "IMX906": 10,
    "IMX888": 10,
    "IMX890": 10,
    "IMX766": 10,
    "IMX866": 10,
    "IMX866V": 10,
    "OV50E": 10,

    # 1/1.7"-1/2"（中端）
    "IMX689": 7,
    "IMX686": 7,
    "IMX586": 7,
    "OV64B": 7,
    "GW3": 7,
    "HM6": 7,

    # 其他5000万像素（基础）
    "default_50mp": 5,
}

# 传感器尺寸等级（用于未知传感器推断）
SENSOR_SIZE_TIERS = {
    "1英寸": 15,
    "1/1.28": 12,
    "1/1.3": 12,
    "1/1.4": 12,
    "1/1.5": 10,
    "1/1.56": 10,
    "1/1.7": 7,
    "1/1.8": 7,
    "1/2": 5,
    "1/2.4": 4,
    "1/2.6": 3,
}

# 长焦配置评分（满分15分）
TELEPHOTO_SCORE_CONFIG = {
    # 配置类型 -> 分数
    "双潜望长焦": 15,          # 如 vivo X100 Ultra
    "直立+潜望双长焦": 12,     # 如 小米14 Ultra
    "高像素大底潜望": 10,      # 如 OPPO Find X7 Ultra
    "单潜望长焦": 7,           # 如 vivo X100s
    "直立长焦": 7,             # 3x/5x 固定焦距
    "无长焦": 0,
}

# 长焦具体配置关键词识别
TELEPHOTO_KEYWORDS = {
    # 关键词 -> (配置类型, 分数)
    "双潜望": ("双潜望长焦", 15),
    "潜望+潜望": ("双潜望长焦", 15),
    "潜望长焦": ("单潜望长焦", 7),
    "潜望式": ("单潜望长焦", 7),
    "直立长焦": ("直立长焦", 7),
    "长焦镜头": ("直立长焦", 7),
    "3x长焦": ("直立长焦", 7),
    "5x长焦": ("直立长焦", 7),
    "10x光学": ("单潜望长焦", 8),  # 高倍潜望加分
}

# OIS 配置
OIS_SCORE = {
    True: 5,   # 有OIS光学防抖
    False: 0,  # 无OIS
}


# =============================================================================
# 影像算法评分配置（权重30%）
# 基于影像品牌/相机联名
# =============================================================================

ALGORITHM_SCORE_CONFIG = {
    # 影像品牌 -> (分数, 说明)
    "XMAGE": (30, "华为自研影像品牌"),
    "Blueimage": (30, "vivo自研影像品牌"),
    "徕卡": (25, "小米徕卡联名"),
    "Leica": (25, "小米徕卡联名"),
    "哈苏": (25, "OPPO/一加哈苏联名"),
    "Hasselblad": (25, "OPPO/一加哈苏联名"),
    "蔡司": (25, "vivo蔡司联名"),
    "Zeiss": (25, "vivo蔡司联名"),
    "苹果原色": (22, "苹果原厂算法"),
    "Apple": (22, "苹果原厂算法"),
    "三星影像": (22, "三星原厂算法"),
    "Samsung": (22, "三星原厂算法"),
    "鹰眼": (18, "荣耀鹰眼算法"),
    "荣耀影像": (18, "荣耀原厂算法"),
    "原色": (15, "默认原色算法"),
    "default": (15, "其他/未知"),
}

# 品牌默认影像算法（当手机品牌无明确影像合作时）
BRAND_DEFAULT_ALGORITHM = {
    "华为": "XMAGE",
    "vivo": "蔡司",
    "OPPO": "哈苏",
    "一加": "哈苏",
    "小米": "徕卡",
    "苹果": "苹果原色",
    "三星": "三星影像",
    "荣耀": "鹰眼",
    "realme": "原色",
    "iQOO": "原色",
    "Redmi": "原色",
    "摩托罗拉": "原色",
    "中兴": "原色",
    "努比亚": "原色",
}


# =============================================================================
# 查询函数
# =============================================================================

def get_chip_score(chip_name: str, has_image_chip: bool = False, image_chip_name: Optional[str] = None) -> int:
    """
    获取芯片算力评分

    Args:
        chip_name: 芯片名称，如 "骁龙8 Gen3"
        has_image_chip: 是否有独立影像芯片
        image_chip_name: 影像芯片名称，如 "V3+"

    Returns:
        芯片算力评分（满分30分）
    """
    # 基础分数（CHIP_SCORE_CONFIG值是tuple: (跑分, 分数)）
    chip_data = CHIP_SCORE_CONFIG.get(chip_name)
    if chip_data:
        base_score = chip_data[1]  # 取分数部分
    else:
        base_score = CHIP_TIER_BASE_SCORES["入门级"]

    # 影像芯片加成
    bonus = 0
    if has_image_chip and image_chip_name:
        bonus = IMAGE_CHIP_BONUS.get(image_chip_name, 2)
    elif has_image_chip:
        bonus = 2  # 默认加2分

    total = base_score + bonus
    return min(total, 30)  # 不超过满分


def get_sensor_score(sensor_name: str) -> int:
    """
    获取主摄传感器评分

    Args:
        sensor_name: 传感器名称，如 "LYT-900", "IMX989"

    Returns:
        传感器评分（满分15分）
    """
    if not sensor_name:
        return SENSOR_SCORE_CONFIG["default_50mp"]

    # 直接匹配
    if sensor_name in SENSOR_SCORE_CONFIG:
        return SENSOR_SCORE_CONFIG[sensor_name]

    # 模糊匹配（如 "IMX989 1英寸"）
    sensor_upper = sensor_name.upper()
    for key, score in SENSOR_SCORE_CONFIG.items():
        if key.upper() in sensor_upper:
            return score

    # 尺寸匹配
    for size_key, score in SENSOR_SIZE_TIERS.items():
        if size_key in sensor_name:
            return score

    # 默认返回
    return SENSOR_SCORE_CONFIG["default_50mp"]


def get_telephoto_score(telephoto_config: str) -> int:
    """
    获取长焦配置评分

    Args:
        telephoto_config: 长焦配置描述，如 "双潜望长焦", "单潜望"

    Returns:
        长焦评分（满分15分）
    """
    if not telephoto_config:
        return TELEPHOTO_SCORE_CONFIG["无长焦"]

    # 直接匹配配置类型
    if telephoto_config in TELEPHOTO_SCORE_CONFIG:
        return TELEPHOTO_SCORE_CONFIG[telephoto_config]

    # 关键词匹配
    for keyword, (_, score) in TELEPHOTO_KEYWORDS.items():
        if keyword in telephoto_config:
            return score

    # 检查是否提到长焦
    if "长焦" in telephoto_config or "telephoto" in telephoto_config.lower():
        return 7  # 默认按直立长焦计

    return TELEPHOTO_SCORE_CONFIG["无长焦"]


def get_ois_score(has_ois: bool) -> int:
    """
    获取OIS评分

    Args:
        has_ois: 是否有OIS光学防抖

    Returns:
        OIS评分（满分5分）
    """
    return OIS_SCORE.get(has_ois, 0)


def get_algorithm_score(brand: Optional[str] = None, algorithm_name: Optional[str] = None) -> int:
    """
    获取影像算法评分

    Args:
        brand: 手机品牌，用于获取默认算法
        algorithm_name: 影像算法/品牌名称，如 "徕卡", "XMAGE"

    Returns:
        影像算法评分（满分30分）
    """
    # 优先使用明确的算法名称
    if algorithm_name:
        for key, (score, _) in ALGORITHM_SCORE_CONFIG.items():
            if key.lower() in algorithm_name.lower():
                return score

    # 使用品牌默认算法
    if brand:
        default_algo = BRAND_DEFAULT_ALGORITHM.get(brand, "default")
        if default_algo in ALGORITHM_SCORE_CONFIG:
            return ALGORITHM_SCORE_CONFIG[default_algo][0]

    return ALGORITHM_SCORE_CONFIG["default"][0]


def calculate_camera_score(
    chip_name: str,
    sensor_name: str,
    telephoto_config: str,
    has_ois: bool,
    algorithm_name: str,
    brand: Optional[str] = None,
    has_image_chip: bool = False,
    image_chip_name: Optional[str] = None,
) -> dict:
    """
    计算手机影像综合评分

    Args:
        chip_name: 芯片名称
        sensor_name: 主摄传感器名称
        telephoto_config: 长焦配置描述
        has_ois: 是否有OIS
        algorithm_name: 影像算法/品牌名称
        brand: 手机品牌
        has_image_chip: 是否有独立影像芯片
        image_chip_name: 影像芯片名称

    Returns:
        {
            "total_score": 综合评分,
            "chip_score": 芯片算力分,
            "hardware_score": 影像硬件分,
            "algorithm_score": 影像算法分,
            "details": 各项明细
        }
    """
    # 计算各维度分数
    chip_score = get_chip_score(chip_name, has_image_chip, image_chip_name)
    sensor_score = get_sensor_score(sensor_name)
    telephoto_score = get_telephoto_score(telephoto_config)
    ois_score = get_ois_score(has_ois)
    algorithm_score = get_algorithm_score(brand, algorithm_name)

    # 影像硬件总分
    hardware_score = sensor_score + telephoto_score + ois_score

    # 综合评分
    total_score = chip_score + hardware_score + algorithm_score

    return {
        "total_score": total_score,
        "chip_score": chip_score,
        "hardware_score": hardware_score,
        "algorithm_score": algorithm_score,
        "details": {
            "chip_base": chip_score - (IMAGE_CHIP_BONUS.get(image_chip_name, 0) if image_chip_name and has_image_chip else 0),
            "chip_bonus": IMAGE_CHIP_BONUS.get(image_chip_name, 0) if image_chip_name and has_image_chip else 0,
            "sensor": sensor_score,
            "telephoto": telephoto_score,
            "ois": ois_score,
        }
    }


# =============================================================================
# 评分等级说明
# =============================================================================

SCORE_LEVELS = {
    (90, 100): "顶级影像旗舰",
    (80, 90): "旗舰影像手机",
    (70, 80): "高端影像手机",
    (60, 70): "中端影像手机",
    (50, 60): "入门影像手机",
    (0, 50): "基础影像能力",
}


def get_score_level(score: int) -> str:
    """
    根据评分获取等级描述

    Args:
        score: 综合评分

    Returns:
        等级描述
    """
    for (min_score, max_score), level in SCORE_LEVELS.items():
        if min_score <= score < max_score:
            return level
    return "基础影像能力"


# =============================================================================
# 示例用法
# =============================================================================

if __name__ == "__main__":
    # 示例：vivo X100 Ultra
    result = calculate_camera_score(
        chip_name="天玑9300",
        sensor_name="LYT-900",
        telephoto_config="双潜望长焦",
        has_ois=True,
        algorithm_name="蔡司",
        brand="vivo",
        has_image_chip=True,
        image_chip_name="V3+"
    )
    print(f"vivo X100 Ultra 影像评分: {result['total_score']}分")
    print(f"  - 芯片算力: {result['chip_score']}分")
    print(f"  - 影像硬件: {result['hardware_score']}分")
    print(f"  - 影像算法: {result['algorithm_score']}分")
    print(f"  - 等级: {get_score_level(result['total_score'])}")

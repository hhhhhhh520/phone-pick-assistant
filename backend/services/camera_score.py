"""
影像评分服务
============

提供手机影像综合评分计算功能，封装 camera_score_config 的查询函数。

评分维度：
1. 芯片算力分（满分30分）- 基于处理器安兔兔跑分 + 影像芯片加成
2. 影像硬件分（满分35分）- 主摄传感器(15) + 长焦配置(15) + OIS(5)
3. 影像算法分（满分30分）- 基于影像品牌/联名

综合满分 = 30 + 35 + 30 = 95分（不含影像芯片额外加成可达100分）
"""

from typing import TYPE_CHECKING

from backend.models.domain import get_antutu_score
from backend.services.camera_score_config import (
    get_score_level,
    get_sensor_score,
    get_telephoto_score,
    get_ois_score,
    get_algorithm_score,
)

if TYPE_CHECKING:
    from backend.models.domain import Phone


# 芯片算力分档：按安兔兔实际跑分划分（而非芯片名精确匹配配置表）。
# 名字匹配对新款/别名芯片会整体失效并冤枉为入门档（如"骁龙8 至尊版 Gen5"
# 不在配置表中实得 10/30，实际跑分 244 万全场最高）；跑分匹配在
# domain.get_antutu_score 已有 7 层模糊策略且覆盖全库，按跑分分档还
# 自带"年代惩罚"——老芯片跑分低，拍照排序自然靠后。
CHIP_SCORE_BY_ANTUTU = [
    (2_000_000, 30),  # 顶级旗舰：200万+
    (1_300_000, 25),  # 旗舰级：130-200万
    (900_000, 22),    # 高端级：90-130万
    (600_000, 18),    # 中高端：60-90万
    (400_000, 14),    # 中端：40-60万
    (0, 10),          # 入门：<40万
]


def _chip_score_from_antutu(score: int) -> int:
    for threshold, points in CHIP_SCORE_BY_ANTUTU:
        if score >= threshold:
            return points
    return 10


class CameraScoringService:
    """影像评分服务"""

    def calc_chip_score(self, phone: "Phone") -> int:
        """
        计算芯片算力分（满分30分）

        基于处理器安兔兔跑分分档评分（未匹配跑分按入门档），如有独立影像芯片
        可获得额外加成。

        Args:
            phone: Phone 模型实例

        Returns:
            芯片算力评分（满分30分）
        """
        processor = phone.processor or ""
        base_score = _chip_score_from_antutu(get_antutu_score(processor) if processor else 0)
        # Phone 模型暂无影像芯片字段，使用默认值
        has_image_chip = False

        return min(base_score, 30)

    def calc_hardware_score(self, phone: "Phone") -> int:
        """
        计算影像硬件分（满分35分）

        = 传感器分(15) + 长焦分(15) + OIS分(5)

        Args:
            phone: Phone 模型实例

        Returns:
            影像硬件评分（满分35分）
        """
        # 主摄传感器评分
        sensor_name = phone.sensor_main or ""
        sensor_score = get_sensor_score(sensor_name)

        # 长焦配置评分
        telephoto_config = phone.telephoto_type or ""
        telephoto_score = get_telephoto_score(telephoto_config)

        # OIS评分
        has_ois = phone.has_ois if phone.has_ois is not None else False
        ois_score = get_ois_score(has_ois)

        return sensor_score + telephoto_score + ois_score

    def calc_algorithm_score(self, phone: "Phone") -> int:
        """
        计算影像算法分（满分30分）

        基于影像品牌评分，优先使用 image_brand 字段，否则使用手机品牌默认算法。

        Args:
            phone: Phone 模型实例

        Returns:
            影像算法评分（满分30分）
        """
        brand = phone.brand or ""
        algorithm_name = phone.image_brand or ""

        return get_algorithm_score(
            brand=brand,
            algorithm_name=algorithm_name
        )

    def calc_total_score(self, phone: "Phone") -> dict:
        """
        计算综合影像评分

        Args:
            phone: Phone 模型实例

        Returns:
            {
                "total": int,           # 总分
                "chip_score": int,      # 芯片算力分
                "hardware_score": int,  # 影像硬件分
                "algorithm_score": int, # 影像算法分
                "grade": str            # 等级描述
            }
        """
        chip_score = self.calc_chip_score(phone)
        hardware_score = self.calc_hardware_score(phone)
        algorithm_score = self.calc_algorithm_score(phone)

        total = chip_score + hardware_score + algorithm_score
        grade = get_score_level(total)

        return {
            "total": total,
            "chip_score": chip_score,
            "hardware_score": hardware_score,
            "algorithm_score": algorithm_score,
            "grade": grade
        }


# 单例实例
camera_scoring_service = CameraScoringService()
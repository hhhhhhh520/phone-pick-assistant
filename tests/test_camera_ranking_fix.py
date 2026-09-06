"""
拍照推荐排序修复测试（2026-09-06）

背景：此前拍照场景按裸像素降序，1.08亿像素的 2021 年代老机型（骁龙870）
会压过 5000万大底新机。修复后：
1. 芯片算力分按安兔兔实际跑分分档（不再按名字精确匹配配置表，
   新芯片/别名不再被冤枉为入门档）
2. 拍照排序键 = 影像评分 → 像素 → 影像标签 → 价格
3. 数据补全：影像评分缓存入库 + 影像标签下放（enrich_camera_data.py）
"""
from unittest.mock import patch

from backend.models.domain import Phone
from backend.services.camera_score import (
    CameraScoringService,
    _chip_score_from_antutu,
    camera_scoring_service,
)
from backend.services.retrieval import RetrievalService, _safe_camera_value
from backend.models.schemas import IntentResult, IntentType


def _phone(**kwargs):
    base = dict(
        brand="小米", model="测试机", price=3000,
        processor="骁龙8 Gen3", ram=8, storage=256,
        camera_main=5000, battery=5000,
        features='[]', suitable_for='[]',
    )
    base.update(kwargs)
    return Phone(**base)


class TestChipScoreByAntutu:
    """芯片算力分按跑分分档"""

    def test_thresholds(self):
        assert _chip_score_from_antutu(2_500_000) == 30
        assert _chip_score_from_antutu(2_000_000) == 30
        assert _chip_score_from_antutu(1_400_000) == 25
        assert _chip_score_from_antutu(1_000_000) == 22
        assert _chip_score_from_antutu(700_000) == 18
        assert _chip_score_from_antutu(500_000) == 14
        assert _chip_score_from_antutu(100_000) == 10

    def test_new_chip_not_punished(self):
        """新款芯片名不在旧配置表也应按实际跑得分档（此前冤枉为10分）"""
        svc = CameraScoringService()
        phone = _phone(processor="骁龙8 至尊版 Gen5")
        assert svc.calc_chip_score(phone) == 30  # 跑分 244万

    def test_old_chip_ranked_lower(self):
        """老旗舰（骁龙870，约70-80万跑分）落在中端档，低于新旗舰"""
        svc = CameraScoringService()
        old = _phone(processor="骁龙870")
        new = _phone(processor="骁龙8 Gen3")
        assert svc.calc_chip_score(old) < svc.calc_chip_score(new)

    def test_unknown_processor_gets_floor(self):
        svc = CameraScoringService()
        assert svc.calc_chip_score(_phone(processor="完全不存在的芯片")) == 10
        assert svc.calc_chip_score(_phone(processor=None)) == 10


class TestCameraRankingFix:
    """拍照排序：老高像素机型必须排在新生底机型之后"""

    def _make_pair(self):
        # 老机型：1.08亿像素 + 骁龙870（2021 年代），无传感器数据
        old = _phone(
            brand="联想", model="老高像素机", price=2699,
            processor="骁龙870", camera_main=10800,
            features='["高刷屏", "旗舰芯片", "游戏手机"]',
        )
        # 新机型：5000万大底 + 新旗舰 + 明确传感器 + OIS
        new = _phone(
            brand="小米", model="新大底机", price=2999,
            processor="骁龙8 Gen3", camera_main=5000,
            sensor_main="IMX989", has_ois=True,
            features='["影像"]',
        )
        return old, new

    def test_new_sensor_beats_old_high_pixels(self):
        """5000万大底新机必须排在 1.08亿像素老机之前（核心回归用例）"""
        old, new = self._make_pair()
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0, budget_max=100000,
            brands=[], features=["拍照"], no_need_features=[],
            phones_mentioned=[], reset_profile=False,
        )
        service = RetrievalService.__new__(RetrievalService)  # 只用纯排序方法，不触库
        ranked = service._sort_by_scenario([old, new], ["拍照"], [])
        assert ranked[0].model == "新大底机"
        assert ranked[1].model == "老高像素机"

    def test_score_detail_justification(self):
        """新大底机的影像评分构成应全面领先老机"""
        old, new = self._make_pair()
        old_score = camera_scoring_service.calc_total_score(old)
        new_score = camera_scoring_service.calc_total_score(new)
        assert new_score["total"] > old_score["total"]
        assert new_score["chip_score"] > old_score["chip_score"]  # 跑分分档
        assert new_score["hardware_score"] > old_score["hardware_score"]  # 传感器+OIS


class TestEnrichCameraData:
    """数据补全脚本的纯逻辑"""

    def test_append_feature_idempotent(self):
        from backend.data.enrich_camera_data import _append_feature
        raw = '["快充", "旗舰芯片"]'
        new, changed = _append_feature(raw, "影像")
        assert changed and "影像" in new
        # 再来一次不重复加
        again, changed2 = _append_feature(new, "影像")
        assert not changed2 and again == new

    def test_append_feature_handles_dirty_json(self):
        from backend.data.enrich_camera_data import _append_feature
        new, changed = _append_feature("不是JSON", "影像")
        assert changed and "影像" in new

    def test_threshold_is_1e8_pixels(self):
        from backend.data.enrich_camera_data import STRONG_PIXEL_THRESHOLD
        assert STRONG_PIXEL_THRESHOLD == 10000  # 万 = 1亿

    def test_safe_camera_value_parsing(self):
        assert _safe_camera_value("2亿") == 20000
        assert _safe_camera_value("1.08亿") == 10800
        assert _safe_camera_value("5000万") == 5000
        assert _safe_camera_value(None) == 0

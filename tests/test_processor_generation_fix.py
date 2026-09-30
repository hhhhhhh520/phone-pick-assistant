"""
W1 处理器污染修复守卫测试 (2026-09-30, ISSUE-047)

背景：影像/跑分补全批次（276b0f4/41998c3）把芯片映射表键 '骁龙8 至尊版 Gen5'
写入了 9 款发布代际早于该芯片的机型（代际不可能，如小米12 Pro 2021=骁龙8 Gen 1、
Xperia PRO-I 2021=骁龙888）。污染值得分 2449060 为全库最高档，直接扭曲游戏/性能
场景排序（实测小米12 Pro ¥1859 顶进"预算3000打原神"推荐前三）。

本文件逐款锁定 A 桶修复行，断言真实库与导出副本中的 processor 为核实后的正确值。
期望值依据：
- 同家族标准版机型在库内的完好值（小米12=骁龙8 Gen 1、小米13=Gen 2、
  小米14=Gen 3、小米15=骁龙8 至尊版）
- 机型发布代际公开事实（Xperia PRO-I 2021=骁龙888、ROG 5s Pro 2021=骁龙888+）

范围说明：B 桶（小米17/17 Pro Max/17 Ultra、Redmi K90 Pro、荣耀500 Pro——Gen5
即其真实芯片）与 C 桶（泛化名/无法核实代际机型）不在断言范围，见 ISSUE-047。
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.domain import Phone

CONTAMINATED = "骁龙8 至尊版 Gen5"

# (id, model, 核实后的正确值) —— 修复清单见 issues/ISSUE-047
A_BUCKET = [
    (1114, "ROG 5s Pro", "骁龙888+"),
    (1209, "小米12 Pro", "骁龙8 Gen 1"),
    (1210, "小米13 Pro", "骁龙8 Gen 2"),
    (1211, "小米13 Ultra", "骁龙8 Gen 2"),
    (1212, "小米14 Pro", "骁龙8 Gen 3"),
    (1213, "小米14 Ultra", "骁龙8 Gen 3"),
    (1214, "小米15 Pro", "骁龙8 至尊版"),
    (1215, "小米15 Ultra", "骁龙8 至尊版"),
    (1233, "Xperia PRO-I", "骁龙888"),
]

EXPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "backend", "data", "phones_export.json",
)


@pytest.fixture
def real_db_session():
    """连接真实数据库（与 test_data_completeness.real_db_session 同惯例）"""
    import backend.config
    settings = backend.config.get_settings()
    db_url = settings.database_url
    if db_url.startswith("sqlite:///./"):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rel_path = db_url.replace("sqlite:///./", "")
        abs_path = os.path.join(project_root, rel_path)
        db_url = f"sqlite:///{abs_path}"

    engine = create_engine(db_url)
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        assert "phones" in inspector.get_table_names(), (
            f"phones表不存在，数据库路径: {db_url}"
        )

        Session = sessionmaker(bind=engine)
        db = Session()
        yield db
        db.close()
    finally:
        engine.dispose()


@pytest.mark.parametrize("phone_id,model,expected", A_BUCKET)
def test_processor_generation_real_db(real_db_session, phone_id, model, expected):
    """A 桶 9 款：真实库 processor 必须为核实的正确值，不得为污染值"""
    phone = real_db_session.query(Phone).filter(Phone.id == phone_id).one_or_none()
    assert phone is not None, f"id={phone_id} {model} 不存在于真实库"
    assert phone.processor != CONTAMINATED, (
        f"{model}(id={phone_id}) 仍被污染值覆盖: {phone.processor!r}"
    )
    assert phone.processor == expected, (
        f"{model}(id={phone_id}): 期望 {expected!r}, 实际 {phone.processor!r}"
    )


def test_export_json_a_bucket_clean():
    """导出副本与库同窗口同步：A 桶 9 款在 phones_export.json 中同样干净"""
    assert os.path.exists(EXPORT_PATH), f"导出副本不存在: {EXPORT_PATH}"
    with open(EXPORT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    by_id = {p.get("id"): p for p in data}
    for phone_id, model, expected in A_BUCKET:
        p = by_id.get(phone_id)
        assert p is not None, f"{model}(id={phone_id}) 不在导出副本中"
        assert p.get("processor") != CONTAMINATED, (
            f"导出副本中 {model} 仍为污染值"
        )
        assert p.get("processor") == expected, (
            f"导出副本 {model}: 期望 {expected!r}, 实际 {p.get('processor')!r}"
        )

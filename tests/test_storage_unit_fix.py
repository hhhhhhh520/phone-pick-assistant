"""
W2 存储字段单位截断守卫测试 (2026-09-30, ISSUE-048)

背景：历史清洗把 "1TB" 截断为整数 1（GB 口径），小米13/14/15 Ultra 三款
storage=1，前端按 `${storage}GB` 渲染成"存储: 1GB"。数据侧修复为 1024（GB
口径），展示侧（PhoneCard/CompareTable/recommend LLM prompt）对 ≥1024 整数倍
转 TB 显示。

范围声明：storage 列另有若干疑似 RAM 误植值（8/12/16/18/24），本次不动，见
ISSUE-048 遗留事项。
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.domain import Phone

EXPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "backend", "data", "phones_export.json",
)

# (id, model) —— 1TB 截断修复清单
TB_PHONES = [
    (1211, "小米13 Ultra"),
    (1213, "小米14 Ultra"),
    (1215, "小米15 Ultra"),
]


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


@pytest.mark.parametrize("phone_id,model", TB_PHONES)
def test_storage_tb_real_db(real_db_session, phone_id, model):
    """三款 1TB 机型：真实库 storage 必须为 1024（GB 口径），不得为截断值 1"""
    phone = real_db_session.query(Phone).filter(Phone.id == phone_id).one_or_none()
    assert phone is not None, f"id={phone_id} {model} 不存在于真实库"
    assert phone.storage == 1024, (
        f"{model}(id={phone_id}): 期望 storage=1024(1TB), 实际 {phone.storage!r}"
    )


def test_storage_export_sync():
    """导出副本与库同窗口同步：三款机型 storage 同为 1024"""
    assert os.path.exists(EXPORT_PATH), f"导出副本不存在: {EXPORT_PATH}"
    with open(EXPORT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    by_id = {p.get("id"): p for p in data}
    for phone_id, model in TB_PHONES:
        assert by_id[phone_id]["storage"] == 1024, (
            f"导出副本 {model}(id={phone_id}) storage 未同步为 1024"
        )


class TestFormatStorage:
    """recommend._format_storage：LLM prompt 侧的存储展示格式化（与前端 formatStorage 镜像）"""

    def test_tb_and_gb_formatting(self):
        """1024/2048 转 TB；128 与非整 TB（1536）保持 GB"""
        from backend.services.recommend import _format_storage
        assert _format_storage(1024) == "1TB"
        assert _format_storage(2048) == "2TB"
        assert _format_storage(128) == "128GB"
        assert _format_storage(1536) == "1536GB"

    def test_falsy_returns_none(self):
        from backend.services.recommend import _format_storage
        assert _format_storage(0) is None
        assert _format_storage(None) is None

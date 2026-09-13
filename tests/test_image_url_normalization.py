r"""图片路径归一化守卫（ISSUE-046）。

数据库里混进过 Windows 反斜杠写法（如 images + 反斜杠 + 文件名，曾占 38%）。
前端拼 URL 时 `encodeURI` 不会把反斜杠规范成 `/`（而是编成 `%5C`），
于是拼出 `http://localhost:8002images%5C...` —— **主机名被吃**，
浏览器拒绝解析、请求根本不发。

这里守卫两层：
1. `Phone` 模型的 `@validates("image_url")`——覆盖**所有**写入路径，
   包括 `scripts/import_phones_json.py` 这条灾难恢复链（只 patch 活库治不了它）
2. 被 git 跟踪的数据源 `backend/data/phones_export.json`——恢复时会全量灌回 DB
"""

import json
from pathlib import Path

import pytest

from backend.models.domain import Phone

BACKSLASH = chr(92)
REPO_ROOT = Path(__file__).resolve().parents[1]  # tests/ 的上一级即项目根
EXPORT_JSON = REPO_ROOT / "backend" / "data" / "phones_export.json"


class TestPhoneModelNormalizesImageUrl:
    """模型层必须保证：写进去的 image_url 永远是 `http(s)://...` 或 `/...`。"""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            # 反斜杠 → 正斜杠，并补前导斜杠
            (f"images{BACKSLASH}OPPO A32(8GB128GB)_1.jpg", "/images/OPPO A32(8GB128GB)_1.jpg"),
            ("images/OPPO A32(8GB128GB)_1.jpg", "/images/OPPO A32(8GB128GB)_1.jpg"),
            ("/images/OPPO A32(8GB128GB)_1.jpg", "/images/OPPO A32(8GB128GB)_1.jpg"),
            # 中文与全角括号要原样保留（真实数据长这样）
            (f"images{BACKSLASH}华为畅享 80（128GB）_1.jpg", "/images/华为畅享 80（128GB）_1.jpg"),
            # 外链原样
            ("https://2e.zol-img.com.cn/product/253_320x240/254/x.jpg",
             "https://2e.zol-img.com.cn/product/253_320x240/254/x.jpg"),
            ("http://img.example.com/a.jpg", "http://img.example.com/a.jpg"),
            # 空值原样
            (None, None),
            ("", ""),
        ],
    )
    def test_image_url_is_normalized_on_set(self, raw, expected):
        phone = Phone(id=1, brand="测试", model="型号", price=999, image_url=raw)

        assert phone.image_url == expected

    def test_no_backslash_survives_in_model(self):
        phone = Phone(
            id=1, brand="小米", model="14", price=3999,
            image_url=f"images{BACKSLASH}小米14（12GB+256GB）_1.jpg",
        )

        assert BACKSLASH not in (phone.image_url or "")
        assert "%5C" not in (phone.image_url or "")
        assert phone.image_url.startswith("/images/")


class TestExportJsonIsClean:
    """`phones_export.json` 是灾难恢复的数据源，恢复会把它的值全量灌回 DB。

    只修活库、不修这份源文件 = 下次恢复 bug 复发（ISSUE-046 审查发现）。
    """

    def test_export_json_exists_and_parses(self):
        assert EXPORT_JSON.exists(), f"数据源不存在：{EXPORT_JSON}"
        json.loads(EXPORT_JSON.read_text(encoding="utf-8"))

    def test_no_backslash_image_url_in_export(self):
        items = json.loads(EXPORT_JSON.read_text(encoding="utf-8"))
        if isinstance(items, dict):
            items = items.get("items", [])

        offenders = [
            it.get("imageUrl")
            for it in items
            if isinstance(it.get("imageUrl"), str) and BACKSLASH in it["imageUrl"]
        ]

        assert offenders == [], (
            f"数据源里仍有 {len(offenders)} 条反斜杠 imageUrl，"
            f"按 import_phones_json.py 恢复后会全部复发。样例：{offenders[:3]}"
        )

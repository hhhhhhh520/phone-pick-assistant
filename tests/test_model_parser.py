"""Tests for ModelParserService - phone model extraction from LLM responses.

Covers all four parsing strategies plus fuzzy matching, brand mappings,
edge cases (empty input, no match, multiple phones), and integration tests.
"""

import pytest
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.model_parser import ModelParserService


# ---------------------------------------------------------------------------
# Mock / Fixtures
# ---------------------------------------------------------------------------


@dataclass
class MockPhone:
    """Lightweight Phone mock -- brand/model are read by the service via display_name (ISSUE-050)."""
    brand: str
    model: str

    @property
    def display_name(self) -> str:
        """与 domain.Phone.display_name 同语义：model 含品牌前缀则不重复拼接"""
        if self.brand and self.model.startswith(self.brand):
            return self.model
        return f"{self.brand} {self.model}".strip()


@pytest.fixture
def parser() -> ModelParserService:
    return ModelParserService()


@pytest.fixture
def sample_phones() -> list[MockPhone]:
    return [
        MockPhone(brand="小米", model="小米14"),
        MockPhone(brand="小米", model="小米14 Ultra"),
        MockPhone(brand="小米", model="Redmi Note 14"),
        MockPhone(brand="华为", model="P60"),
        MockPhone(brand="华为", model="P60 Pro"),
        MockPhone(brand="苹果", model="iPhone 15"),
        MockPhone(brand="苹果", model="iPhone 15 Pro"),
        MockPhone(brand="OPPO", model="Find X9"),
        MockPhone(brand="vivo", model="X200"),
        MockPhone(brand="三星", model="Galaxy S24"),
        MockPhone(brand="一加", model="一加 13"),
        MockPhone(brand="realme", model="GT 5 Pro"),
        MockPhone(brand="荣耀", model="Magic6 Pro"),
        MockPhone(brand="红米", model="Redmi K70"),
        MockPhone(brand="联想", model="moto X50 Ultra"),
    ]


# ===========================================================================
# (a) JSON mode parsing -- ```json code block
# ===========================================================================


def test_parse_json_pattern_with_code_block(parser):
    """Strategy 1: extract models from a ```json fenced code block."""
    text = '''
Here are my recommendations:

```json
{"recommended": ["OPPO Find X9", "vivo X200"]}
```

Hope this helps!
'''
    result = parser._parse_json_pattern(text)
    assert result == ["OPPO Find X9", "vivo X200"]


def test_parse_json_pattern_multiple_models(parser):
    """JSON code block with three recommended models."""
    text = '```json\n{"recommended": ["小米14", "华为P60", "iPhone 15"]}\n```'
    result = parser._parse_json_pattern(text)
    assert result == ["小米14", "华为P60", "iPhone 15"]


def test_parse_json_pattern_single_model(parser):
    """JSON code block with a single model in the list."""
    text = '```json\n{"recommended": ["iPhone 15 Pro"]}\n```'
    result = parser._parse_json_pattern(text)
    assert result == ["iPhone 15 Pro"]


def test_parse_json_pattern_no_json_block(parser):
    """Returns empty list when no ```json fence is present."""
    text = "I recommend the OPPO Find X9. It has a great camera."
    result = parser._parse_json_pattern(text)
    assert result == []


def test_parse_json_pattern_invalid_json(parser):
    """Gracefully handles malformed JSON inside the code fence."""
    text = '```json\n{broken json!!!}\n```'
    result = parser._parse_json_pattern(text)
    assert result == []


# ===========================================================================
# (b) Bare JSON parsing -- no markdown code fence
# ===========================================================================


def test_parse_bare_json_basic(parser):
    """Strategy 2: bare JSON object inline in the response."""
    text = 'Based on your needs, {"recommended": ["Galaxy S24", "iPhone 15"]} is my pick.'
    result = parser._parse_bare_json_pattern(text)
    assert result == ["Galaxy S24", "iPhone 15"]


def test_parse_bare_json_no_match(parser):
    """Returns empty list when no JSON-like structure is present."""
    text = "I suggest you buy the latest flagship phone."
    result = parser._parse_bare_json_pattern(text)
    assert result == []


# ===========================================================================
# (c) Text pattern parsing -- various Markdown formats
# ===========================================================================


def test_parse_text_numbered_bold_dash(parser):
    """Pattern: `1. **Brand Model** -` numbered bold list."""
    text = """
1. **OPPO Find X9** - 极致的拍照体验
2. **vivo X200** - 出色的续航
3. **小米14** - 性价比高
"""
    result = parser._parse_text_patterns(text)
    assert result == ["OPPO Find X9", "vivo X200", "小米14"]


def test_parse_text_chinese_recommend(parser):
    """Pattern: `推荐一：Brand Model` Chinese recommendation format."""
    text = "推荐一：OPPO Find X9\n推荐二：vivo X200"
    result = parser._parse_text_patterns(text)
    assert len(result) >= 2
    assert "OPPO Find X9" in result
    assert "vivo X200" in result


def test_parse_text_heading_bold(parser):
    """Pattern: `### 1. **Brand Model**` heading+bold format."""
    text = """
### 1. **OPPO Find X9**
### 2. **vivo X200**
"""
    result = parser._parse_text_patterns(text)
    assert result == ["OPPO Find X9", "vivo X200"]


def test_parse_text_bold_colon(parser):
    """Pattern: `**Brand Model**：` bold+colon format."""
    text = "**OPPO Find X9**：这款手机..."
    result = parser._parse_text_patterns(text)
    assert result == ["OPPO Find X9"]


def test_parse_text_no_match(parser):
    """Returns empty list when no known text pattern matches."""
    text = "Just buy whatever phone you like."
    result = parser._parse_text_patterns(text)
    assert result == []


# ===========================================================================
# (d) Candidate phone direct matching
# ===========================================================================


def test_match_from_candidates_exact(parser, sample_phones):
    """Exact model substring appears in the response text."""
    text = "I recommend the 小米14 for its great value."
    result = parser._match_from_candidates(text, sample_phones)
    # ISSUE-050：展示名去重——model 已含品牌前缀时不再输出"小米 小米14"
    assert "小米14" in result
    assert "小米 小米14" not in result


def test_match_from_candidates_case_insensitive(parser, sample_phones):
    """Case-insensitive matching of model names."""
    text = "the iphone 15 is a good choice"
    result = parser._match_from_candidates(text, sample_phones)
    assert any("iPhone 15" in m for m in result)


def test_match_from_candidates_multiple_phones(parser, sample_phones):
    """Multiple phone models matched from a single response."""
    text = "I suggest 小米14 or P60. Both are great."
    result = parser._match_from_candidates(text, sample_phones)
    assert len(result) >= 2
    assert any("小米14" in m for m in result)
    assert any("P60" in m for m in result)


def test_match_from_candidates_limits_to_three(parser, sample_phones):
    """At most 3 models returned from candidate matching."""
    text = "小米14 P60 iPhone 15 Find X9 X200"  # 5 models
    result = parser._match_from_candidates(text, sample_phones)
    assert len(result) <= 3


def test_match_from_candidates_no_match(parser, sample_phones):
    """Returns empty list when no phone models appear in the response."""
    text = "I cannot find any suitable phones for your requirements."
    result = parser._match_from_candidates(text, sample_phones)
    assert result == []


# ===========================================================================
# (e) Chinese-English brand bidirectional mapping
# ===========================================================================


def test_brand_mapping_cn_to_en(parser):
    """Chinese brand names map to English equivalents."""
    assert parser._brand_cn_to_en["红米"] == "redmi"
    assert parser._brand_cn_to_en["一加"] == "oneplus"
    assert parser._brand_cn_to_en["华为"] == "huawei"
    assert parser._brand_cn_to_en["小米"] == "xiaomi"
    assert parser._brand_cn_to_en["荣耀"] == "honor"
    assert parser._brand_cn_to_en["苹果"] == "apple"
    assert parser._brand_cn_to_en["三星"] == "samsung"
    assert parser._brand_cn_to_en["联想"] == "lenovo"


def test_brand_mapping_en_to_cn(parser):
    """English brand names map to Chinese equivalents."""
    assert parser._brand_en_to_cn["redmi"] == "红米"
    assert parser._brand_en_to_cn["oneplus"] == "一加"
    assert parser._brand_en_to_cn["huawei"] == "华为"
    assert parser._brand_en_to_cn["honor"] == "荣耀"
    assert parser._brand_en_to_cn["samsung"] == "三星"
    assert parser._brand_en_to_cn["apple"] == "苹果"
    assert parser._brand_en_to_cn["xiaomi"] == "小米"


def test_brand_mapping_completeness(parser):
    """Combined brand mapping covers all primary phone brands."""
    expected_keys = [
        # Chinese brands
        "红米", "一加", "华为", "小米", "荣耀", "苹果", "三星", "联想",
        "摩托罗拉",
        # English brands
        "oppo", "vivo", "realme", "iqoo",
        "redmi", "oneplus", "huawei", "honor",
        "samsung", "apple", "lenovo", "moto", "iphone",
    ]
    for key in expected_keys:
        assert key in parser._brand_mapping, f"Missing brand key: {key}"


# ===========================================================================
# (f) Fuzzy matching tolerance
# ===========================================================================


def test_fuzzy_match_chinese_brand_to_english_model(parser):
    """'红米' in model_name matches phone with English 'Redmi' in model field."""
    phone = MockPhone(brand="小米", model="Redmi Note 14")
    assert parser._fuzzy_match_model("红米 Note 14", phone) is True


def test_fuzzy_match_english_brand_to_chinese_model(parser):
    """'oneplus' in model_name matches phone with Chinese '一加' in brand."""
    phone = MockPhone(brand="一加", model="一加 13")
    assert parser._fuzzy_match_model("OnePlus 13", phone) is True


def test_fuzzy_match_star_rating_stripped(parser):
    """Star-rating decorations are stripped before matching."""
    phone = MockPhone(brand="OPPO", model="Find X9")
    assert parser._fuzzy_match_model("OPPO Find X9（推荐指数：⭐⭐⭐⭐⭐）", phone) is True
    assert parser._fuzzy_match_model("OPPO Find X9（推荐指数：⭐⭐⭐⭐）", phone) is True


def test_fuzzy_match_core_model_substring(parser):
    """After stripping brand, core model substring must appear in phone.model."""
    # "华为 P60 Pro" -> strip "华为" -> "p60 pro" -> "p60 pro" in "p60 pro" -> True
    phone = MockPhone(brand="华为", model="P60 Pro")
    assert parser._fuzzy_match_model("华为 P60 Pro", phone) is True

    # "Huawei P60" -> strip "huawei" -> "p60" -> "p60" in "p60 pro" -> True
    # (Fuzzy matching correctly identifies P60 as a subset of P60 Pro)
    assert parser._fuzzy_match_model("Huawei P60", phone) is True

    # "Huawei P70" -> strip "huawei" -> "p70" -> "p70" not in "p60 pro" -> False
    assert parser._fuzzy_match_model("Huawei P70", phone) is False


def test_fuzzy_match_no_match(parser):
    """Completely unrelated model name returns False."""
    phone = MockPhone(brand="小米", model="小米14")
    assert parser._fuzzy_match_model("iPhone 99 Pro Max Ultra", phone) is False


# ===========================================================================
# (g) Empty input handling
# ===========================================================================


def test_extract_empty_string(parser, sample_phones):
    """Empty response returns empty list."""
    result = parser.extract_recommended_models("", sample_phones)
    assert result == []


def test_extract_empty_phones(parser):
    """No candidate phones returns empty list even with valid response text."""
    text = '```json\n{"recommended": ["OPPO Find X9"]}\n```'
    # JSON strategy should still find the model even without phone candidates
    result = parser.extract_recommended_models(text, [])
    assert result == ["OPPO Find X9"]


def test_extract_whitespace_only(parser, sample_phones):
    """Whitespace-only response returns empty list."""
    result = parser.extract_recommended_models("   \n\t  ", sample_phones)
    assert result == []


# ===========================================================================
# (h) No-match boundary condition
# ===========================================================================


def test_extract_no_known_models(parser, sample_phones):
    """Response with no phone references returns empty list."""
    text = "This is a general discussion about mobile technology trends."
    result = parser.extract_recommended_models(text, sample_phones)
    assert result == []


# ===========================================================================
# (i) Multiple phones matched simultaneously
# ===========================================================================


def test_extract_multiple_phones_json(parser):
    """Multiple phone models extracted from JSON format."""
    text = '```json\n{"recommended": ["小米14", "华为P60", "iPhone 15", "OPPO Find X9"]}\n```'
    result = parser.extract_recommended_models(text, [])
    assert len(result) == 4
    assert "小米14" in result
    assert "华为P60" in result
    assert "iPhone 15" in result
    assert "OPPO Find X9" in result


# ===========================================================================
# Integration: extract_recommended_models strategy fallback chain
# ===========================================================================


def test_extract_json_strategy_wins(parser, sample_phones):
    """JSON code block is tried first and its result is returned immediately."""
    text = '''
```json
{"recommended": ["Galaxy S24"]}
```

1. **OPPO Find X9** - also mentioned
'''
    result = parser.extract_recommended_models(text, sample_phones)
    assert result == ["Galaxy S24"]


def test_extract_fallback_to_text(parser, sample_phones):
    """When no JSON is present, fall back to text pattern parsing."""
    text = "1. **OPPO Find X9** - 推荐理由..."
    result = parser.extract_recommended_models(text, sample_phones)
    assert result == ["OPPO Find X9"]


def test_extract_fallback_to_candidates(parser, sample_phones):
    """When no JSON or text patterns match, fall back to candidate matching."""
    text = "I think the 小米14 is your best option here."
    result = parser.extract_recommended_models(text, sample_phones)
    assert any("小米14" in m for m in result)

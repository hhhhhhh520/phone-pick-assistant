"""
安兔兔配置加载测试

测试范围:
- antutu_scores.json 格式验证 (文件存在、有效JSON、必需字段、UTF-8编码、值类型、别名有效性)
- load_antutu_scores() 加载/缓存/降级行为
- get_antutu_score() 行为一致性和正确性

任务: SUB-008 #11
"""
import json
import logging
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from backend.config import load_antutu_scores, get_project_root
from backend.models.domain import get_antutu_score


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _get_antutu_json_path() -> Path:
    """返回 antutu_scores.json 的绝对路径。"""
    return get_project_root() / "backend" / "data" / "antutu_scores.json"


def _load_raw_json() -> dict:
    """读取并解析真实的 antutu_scores.json（不使用缓存层）。"""
    json_path = _get_antutu_json_path()
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Task a, f, g, h: antutu_scores.json 格式验证
# ---------------------------------------------------------------------------

class TestAntutuScoresJsonFormat:
    """antutu_scores.json 文件格式与内容验证。"""

    def test_file_exists(self):
        """a1 -- JSON 文件存在于配置路径。"""
        json_path = _get_antutu_json_path()
        assert json_path.exists(), f"Expected {json_path} to exist"
        assert json_path.is_file(), f"Expected {json_path} to be a regular file"

    def test_valid_json(self):
        """a2 -- 文件内容为有效 JSON，可被 json.load 成功解析。"""
        # 不会抛出 JSONDecodeError 即为通过
        data = _load_raw_json()
        assert isinstance(data, dict), "Top-level JSON value must be a dict"

    def test_has_required_fields(self):
        """a3 -- 顶层必须包含 scores、aliases、version 三个字段。"""
        data = _load_raw_json()
        for field in ("scores", "aliases", "version"):
            assert field in data, f"Missing required field: {field}"

    def test_version_is_string(self):
        """version 字段的类型应为字符串。"""
        data = _load_raw_json()
        assert isinstance(data["version"], str), "version must be a string"

    def test_scores_is_dict(self):
        """scores 字段的类型应为 dict[str, int]。"""
        data = _load_raw_json()
        scores = data["scores"]
        assert isinstance(scores, dict), "scores must be a dict"
        assert len(scores) > 0, "scores must be non-empty"

    def test_all_scores_are_positive_integers(self):
        """g -- 所有 scores 值必须为正整数。"""
        data = _load_raw_json()
        for key, value in data["scores"].items():
            assert isinstance(value, int), (
                f"Score for '{key}' must be int, got {type(value).__name__}"
            )
            assert value > 0, f"Score for '{key}' must be positive, got {value}"

    def test_aliases_is_dict_of_strings(self):
        """aliases 字段应为 dict[str, str]。"""
        data = _load_raw_json()
        aliases = data["aliases"]
        assert isinstance(aliases, dict), "aliases must be a dict"
        for k, v in aliases.items():
            assert isinstance(k, str), f"Alias key '{k}' must be str"
            assert isinstance(v, str), f"Alias value for '{k}' must be str"

    def test_all_aliases_point_to_valid_scores_keys(self):
        """h -- 所有 aliases 的值必须指向 scores 中存在的键。"""
        data = _load_raw_json()
        scores_keys = set(data["scores"].keys())
        for alias_key, target in data["aliases"].items():
            assert target in scores_keys, (
                f"Alias '{alias_key}' -> '{target}' but '{target}' "
                f"is not a key in scores"
            )

    def test_utf8_encoding_chinese_processor_names(self):
        """f -- 中文处理器名称正确 UTF-8 编码/解码，且可被 json.load 往返。"""
        data = _load_raw_json()

        # 确认 JSON 中存在中文键
        chinese_keys = [
            k for k in data["scores"]
            if any('一' <= c <= '鿿' for c in k)
        ]
        assert len(chinese_keys) > 0, "No Chinese processor names in scores"

        # 抽取几个代表性中文键，确认值正确
        checks = {
            "骁龙8 至尊版": 1990417,
            "天玑9400": 1788839,
            "麒麟9020": 680418,
        }
        for name, expected_score in checks.items():
            assert name in data["scores"], f"Missing Chinese key: {name}"
            assert data["scores"][name] == expected_score, (
                f"Score mismatch for '{name}': "
                f"expected {expected_score}, got {data['scores'][name]}"
            )

        # 别名中的中文键也应正确编码
        chinese_alias_keys = [
            k for k in data["aliases"]
            if any('一' <= c <= '鿿' for c in k)
        ]
        assert len(chinese_alias_keys) > 0, "No Chinese keys in aliases"


# ---------------------------------------------------------------------------
# Task b, c, d: load_antutu_scores() 行为
# ---------------------------------------------------------------------------

class TestLoadAntutuScores:
    """load_antutu_scores() 正常加载、缓存、降级行为。"""

    def _clear_cache(self):
        """清除 load_antutu_scores 的 lru_cache。"""
        load_antutu_scores.cache_clear()

    def test_normal_load_returns_dicts(self):
        """b1 -- 正常加载返回 (scores_dict, aliases_dict) 元组。"""
        self._clear_cache()
        try:
            scores, aliases = load_antutu_scores()
            assert isinstance(scores, dict), "scores must be dict"
            assert isinstance(aliases, dict), "aliases must be dict"
            assert len(scores) > 0, "scores must be non-empty"
        finally:
            self._clear_cache()

    def test_normal_load_known_values(self):
        """b2 -- 加载的数据包含预期值。"""
        self._clear_cache()
        try:
            scores, aliases = load_antutu_scores()
            # 抽样验证已知处理器跑分
            assert scores.get("A19 Pro") == 2200000
            assert scores.get("骁龙8 至尊版") == 1990417
            # 抽样验证已知别名
            assert aliases.get("骁龙8 Elite") == "骁龙8 至尊版"
        finally:
            self._clear_cache()

    def test_caching_identity(self):
        """b3 -- lru_cache 生效：两次调用返回同一对象（is 判等）。"""
        self._clear_cache()
        try:
            result1 = load_antutu_scores()
            result2 = load_antutu_scores()
            # 顶层元组是同一对象
            assert result1 is result2, "Cached result should be same object"
            # 内部 dict 也应是同一对象
            assert result1[0] is result2[0], "Cached scores dict should be same object"
            assert result1[1] is result2[1], "Cached aliases dict should be same object"
        finally:
            self._clear_cache()

    def test_caching_value_stability(self):
        """b4 -- 缓存后值不变，即使不同时间调用。"""
        self._clear_cache()
        try:
            scores1, aliases1 = load_antutu_scores()
            # 等一会再调用（模拟时间流逝）
            import time
            time.sleep(0.01)
            scores2, aliases2 = load_antutu_scores()
            assert scores1 == scores2
            assert aliases1 == aliases2
        finally:
            self._clear_cache()

    def test_file_missing_degradation(self, caplog):
        """c -- JSON 文件不存在时降级：返回空字典 + 日志警告。"""
        self._clear_cache()
        try:
            with patch.object(Path, 'exists', return_value=False):
                with caplog.at_level(logging.WARNING):
                    scores, aliases = load_antutu_scores()

            assert scores == {}, f"Expected empty scores dict, got {scores}"
            assert aliases == {}, f"Expected empty aliases dict, got {aliases}"

            # 日志应包含 "not found" 提示
            log_text = caplog.text.lower()
            assert "not found" in log_text, (
                f"Expected 'not found' in log, got: {caplog.text}"
            )
        finally:
            self._clear_cache()

    def test_json_parse_failure_degradation(self, caplog):
        """d -- JSON 解析失败时优雅降级：返回空字典 + 日志警告。"""
        self._clear_cache()
        try:
            corrupted = 'this is not valid json {{{[[[]'
            with patch('builtins.open', mock_open(read_data=corrupted)):
                with caplog.at_level(logging.WARNING):
                    scores, aliases = load_antutu_scores()

            assert scores == {}, f"Expected empty scores dict, got {scores}"
            assert aliases == {}, f"Expected empty aliases dict, got {aliases}"

            # 日志应包含 "corrupted" 或 "parse" 提示
            log_text = caplog.text.lower()
            assert "corrupted" in log_text or "parse" in log_text, (
                f"Expected degradation log, got: {caplog.text}"
            )
        finally:
            self._clear_cache()


# ---------------------------------------------------------------------------
# Task e: get_antutu_score() 行为一致性
# ---------------------------------------------------------------------------

class TestGetAntutuScore:
    """get_antutu_score() 在新架构下的行为正确性和一致性。"""

    def test_deterministic(self):
        """e1 -- 相同输入始终返回相同输出（确定性）。"""
        processors = [
            "A19 Pro",
            "骁龙8 至尊版",
            "天玑9400",
            "麒麟9020",
            "Exynos 2500",
            "骁龙8 Elite",          # 需要通过别名解析
            "unknown_processor_xyz", # 未知处理器
        ]
        for p in processors:
            r1 = get_antutu_score(p)
            r2 = get_antutu_score(p)
            assert r1 == r2, (
                f"Non-deterministic: '{p}' -> {r1} vs {r2}"
            )

    def test_known_processors_exact(self):
        """e2 -- 精确匹配已知处理器跑分。"""
        test_cases = [
            ("A19 Pro", 2200000),
            ("A18 Pro", 1720000),
            ("骁龙8 至尊版", 1990417),
            ("天玑9400", 1788839),
            ("麒麟9020", 680418),
        ]
        for proc, expected in test_cases:
            result = get_antutu_score(proc)
            assert result == expected, (
                f"'{proc}' expected {expected}, got {result}"
            )

    def test_alias_resolution(self):
        """e3 -- 别名能正确解析到规范键并返回对应跑分。"""
        test_cases = [
            ("骁龙8 Elite", "骁龙8 至尊版"),       # 别名
            ("骁龙8Elite", "骁龙8至尊版"),          # 无空格别名
            ("第三代骁龙7+", "骁龙7+ Gen 3"),       # 中文别名
            ("骁龙8+", "骁龙8+ Gen 1"),            # 简写别名
        ]
        load_antutu_scores()  # prime the cache so aliases are loaded
        for alias, canonical in test_cases:
            alias_score = get_antutu_score(alias)
            canonical_score = get_antutu_score(canonical)
            assert alias_score == canonical_score, (
                f"Alias '{alias}' ({alias_score}) should match "
                f"canonical '{canonical}' ({canonical_score})"
            )
            assert alias_score > 0, (
                f"Alias '{alias}' resolved to score 0 (should be > 0)"
            )

    def test_unknown_processor_returns_zero(self):
        """未知处理器（无可匹配项）应返回 0。"""
        unknown = [
            "完全不存在的处理器XYZZY",
            "",
            "FakeCPU-9999",
        ]
        for proc in unknown:
            result = get_antutu_score(proc)
            assert result == 0, (
                f"Unknown processor '{proc}' should return 0, got {result}"
            )

    def test_empty_or_none_default_returns_zero(self):
        """空字符串或 None 输入应安全返回 0。"""
        assert get_antutu_score("") == 0
        assert get_antutu_score(None) == 0  # type: ignore[arg-type]

    def test_whitespace_only_returns_zero(self):
        """纯空白输入应返回 0。"""
        assert get_antutu_score("   ") == 0
        assert get_antutu_score("\t\n") == 0

    def test_spacing_variants_resolve(self):
        """不同空格变体（如 '骁龙8Gen3' vs '骁龙8 Gen 3'）应返回相同结果。"""
        variants = [
            ("骁龙8 Gen 3", "骁龙8Gen3"),
            ("骁龙8+ Gen 1", "骁龙8+Gen1"),
            ("天玑 9300+", "天玑9300+"),
        ]
        for spaced, nospaced in variants:
            s1 = get_antutu_score(spaced)
            s2 = get_antutu_score(nospaced)
            assert s1 == s2, (
                f"Spacing variant mismatch: '{spaced}' ({s1}) vs '{nospaced}' ({s2})"
            )
            assert s1 > 0, f"Expected positive score for '{spaced}', got {s1}"

    def test_result_is_always_integer(self):
        """所有返回结果必须是 int 类型。"""
        test_inputs = [
            "A19 Pro",
            "骁龙8 至尊版",
            "unknown_xyz",
            "",
            "骁龙8 Elite",
        ]
        for inp in test_inputs:
            result = get_antutu_score(inp)
            assert isinstance(result, int), (
                f"Result for '{inp}' must be int, got {type(result).__name__}: {result}"
            )

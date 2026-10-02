"""Model parser service - extracts recommended phone models from LLM responses.

Extracted from backend/api/routes/chat.py (SUB-009 task #13).
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ModelParserService:
    """Extracts recommended phone model names from LLM response text.

    Multiple parsing strategies are tried in fallback order:
    1. JSON code block with "recommended" key
    2. Bare JSON (no code fence) with "recommended" key
    3. Markdown text patterns (numbered lists, headings, bold markers)
    4. Direct candidate matching from the provided phone list

    Brand name mappings (Chinese/English bidirectional) are built once at init
    from class-level constants to avoid repeated dict construction.
    """

    # --- Class-level brand mapping constants ---

    _BRAND_CN_TO_EN: dict[str, str] = {
        'oppo': 'oppo', 'vivo': 'vivo',
        '联想': 'lenovo', 'moto': 'moto', '摩托罗拉': 'moto',
        '三星': 'samsung', '苹果': 'apple', '红米': 'redmi',
        '一加': 'oneplus', '华为': 'huawei', '小米': 'xiaomi',
        '荣耀': 'honor', 'realme': 'realme', 'iqoo': 'iqoo',
        '真我': 'realme', '努比亚': 'nubia', '索尼': 'sony',
    }

    _BRAND_EN_TO_CN: dict[str, str] = {
        'redmi': '红米', 'oneplus': '一加', 'huawei': '华为',
        'honor': '荣耀', 'samsung': '三星', 'apple': '苹果',
        'lenovo': '联想', 'moto': '联想', 'xiaomi': '小米',
        'oppo': 'oppo', 'vivo': 'vivo', 'realme': '真我', 'iqoo': 'iqoo',
        'nubia': '努比亚', 'sony': '索尼',
    }

    # Combined mapping used for keyword iteration in fuzzy matching.
    # Keys are brand substrings that may appear in model names (Chinese + English).
    _BRAND_MAPPING: dict[str, str] = {
        'oppo': 'oppo', 'vivo': 'vivo',
        '联想': 'lenovo', 'moto': 'moto', '摩托罗拉': 'moto',
        '三星': 'samsung', '苹果': 'apple', '红米': 'redmi',
        '一加': 'oneplus', '华为': 'huawei', '小米': 'xiaomi',
        '荣耀': 'honor', 'realme': 'realme', 'iqoo': 'iqoo',
        '真我': 'realme', '努比亚': 'nubia', '索尼': 'sony',
        'redmi': 'redmi', 'oneplus': 'oneplus', 'huawei': 'huawei',
        'honor': 'honor', 'samsung': 'samsung', 'apple': 'apple',
        'lenovo': 'lenovo', 'iphone': 'iphone',
        'nubia': 'nubia', 'sony': 'sony',
    }

    # Regex patterns for extracting model names from markdown text.
    _TEXT_PATTERNS: list[str] = [
        r'\d+\.\s*\*\*([^*]+)\*\*\s*[-–—]',               # 1. **OPPO Find X9** -
        r'推荐[一二三四五六七八九十]+[：:]\s*\*?\*?([^*\n（(]+)',  # 推荐一：OPPO Find X9
        r'###\s*\d+\.\s*\*?\*?([^*\n（(]+)',              # ### 1. **OPPO Find X9**
        r'\*\*([^*（(]+)\*\*[：:]',                        # **OPPO Find X9**：
    ]

    # --- Lifecycle ---

    def __init__(self) -> None:
        """Initialise instance-level brand mappings from class constants."""
        self._brand_cn_to_en, self._brand_en_to_cn = self._build_brand_mappings()
        self._brand_mapping = dict(self._BRAND_MAPPING)

    # --- Public API ---

    def extract_recommended_models(self, full_reply: str, phones: list) -> list[str]:
        """Extract recommended phone model names from an LLM response.

        Tries four parsing strategies in order; the first to return a non-empty
        result wins.

        Args:
            full_reply: Complete LLM response text.
            phones: List of Phone ORM objects for candidate-based fallback.

        Returns:
            List of model name strings, e.g. ``["OPPO Find X9", "vivo X200"]``.
            May be empty if no models could be extracted.
        """
        logger.info(
            "Full reply length: %d, first 500 chars: %s",
            len(full_reply), full_reply[:500],
        )

        recommended: list[str]

        # Strategy 1: JSON code block
        recommended = self._parse_json_pattern(full_reply)
        if recommended:
            logger.info("Recommended models from JSON: %s", recommended)
            logger.info("Final recommended_models: %s", recommended)
            return recommended

        # Strategy 2: Bare JSON (no code fence)
        recommended = self._parse_bare_json_pattern(full_reply)
        if recommended:
            logger.info("Recommended models from bare JSON: %s", recommended)
            logger.info("Final recommended_models: %s", recommended)
            return recommended

        # Strategy 3: Markdown text patterns
        recommended = self._parse_text_patterns(full_reply)
        if recommended:
            logger.info("Final recommended_models: %s", recommended)
            return recommended

        # Strategy 4: Direct candidate matching from phone list
        recommended = self._match_from_candidates(full_reply, phones)
        logger.info("Final recommended_models: %s", recommended)
        return recommended

    # --- Parsing strategies (private) ---

    def _parse_json_pattern(self, text: str) -> list[str]:
        """Extract models from a ```json fenced code block.

        Looks for ``{"recommended": ["Model A", "Model B"]}`` inside the fence.
        """
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(1))
            return data.get("recommended", [])
        except json.JSONDecodeError:
            logger.warning("Failed to parse recommended models JSON")
            return []

    def _parse_bare_json_pattern(self, text: str) -> list[str]:
        """Extract models from bare JSON (no markdown code fence)."""
        match = re.search(r'\{"recommended":\s*\[.*?\]\}', text, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
            return data.get("recommended", [])
        except json.JSONDecodeError:
            logger.warning("Failed to parse bare JSON")
            return []

    def _parse_text_patterns(self, text: str) -> list[str]:
        """Extract models from markdown patterns like ``1. **Brand Model** -``.

        Iterates the class-level ``_TEXT_PATTERNS`` list and returns the first
        pattern that produces matches (up to 3).
        """
        for pattern in self._TEXT_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                result = [
                    m.strip().replace('**', '').strip() for m in matches[:3]
                ]
                logger.info(
                    "Recommended models from text pattern '%s': %s",
                    pattern, result,
                )
                return result
        return []

    def _match_from_candidates(self, text: str, phones: list) -> list[str]:
        """Match phone model names directly in the response text.

        Checks whether each phone's ``model`` field appears as a substring
        (case-insensitive) in the full reply.
        """
        matched: list[str] = []
        for p in phones:
            if p.model in text or p.model.lower() in text.lower():
                matched.append(p.display_name)
        if matched:
            logger.info(
                "Recommended models from direct phone matching: %s",
                matched[:3],
            )
            return matched[:3]
        return []

    # --- Brand mappings ---

    def _build_brand_mappings(self) -> tuple[dict[str, str], dict[str, str]]:
        """Build Chinese-to-English and English-to-Chinese brand mapping dicts.

        Returns fresh copies so callers may mutate them without affecting the
        class-level constants or other instances.

        Returns:
            Tuple of ``(cn_to_en, en_to_cn)`` brand name mappings.
        """
        return (dict(self._BRAND_CN_TO_EN), dict(self._BRAND_EN_TO_CN))

    # --- Fuzzy matching ---

    def _fuzzy_match_model(self, model_name: str, phone: Any) -> bool:
        """Fuzzy-match a model name string against a phone database record.

        Handles variations between LLM output and database fields:
        - Strips star-rating decorations from the model name.
        - Maps Chinese brand names to English (and vice versa).
        - Matches brand in both ``phone.model`` and ``phone.brand`` fields.
        - After stripping the brand, requires the remaining core model substring
          to appear in ``phone.model`` (or be empty, which matches anything).

        Args:
            model_name: Raw model name from LLM text, e.g. ``"OPPO Find X9"``.
            phone: Phone ORM object with ``.brand`` and ``.model`` attributes.

        Returns:
            ``True`` if the phone matches the model name.
        """
        # Clean star-rating decorations from the model name
        model_clean = (
            model_name
            .replace('（推荐指数：⭐⭐⭐⭐⭐）', '')
            .replace('（推荐指数：⭐⭐⭐⭐）', '')
            .strip()
        )
        model_clean_lower = model_clean.lower()
        p_model_lower = phone.model.lower()
        p_brand_lower = phone.brand.lower()

        for brand_key, brand_en in self._brand_mapping.items():
            if brand_key not in model_clean_lower:
                continue

            brand_cn = self._brand_en_to_cn.get(brand_en, brand_key)

            brand_in_model = (
                brand_key in p_model_lower or brand_en in p_model_lower
            )
            brand_in_brand_field = (
                brand_key in p_brand_lower
                or brand_en in p_brand_lower
                or brand_cn in p_brand_lower
            )

            if not (brand_in_model or brand_in_brand_field):
                continue

            # Strip the brand keyword to isolate the core model number/name
            core_model = (
                model_clean_lower
                .replace(brand_key, '')
                .replace(brand_en, '')
                .strip()
            )
            core_model = (
                core_model
                .replace('（推荐指数：⭐⭐⭐⭐⭐）', '')
                .replace('（推荐指数：⭐⭐⭐⭐）', '')
                .strip()
            )

            if not core_model or core_model in p_model_lower:
                return True

        return False

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import get_settings
import json
import re

Base = declarative_base()


class Phone(Base):
    __tablename__ = "phones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    release_date = Column(String(20))
    screen_size = Column(Float)
    screen_type = Column(String(20))
    screen_refresh = Column(Integer)
    processor = Column(String(50))
    ram = Column(Integer)
    storage = Column(Integer)
    camera_main = Column(Integer)
    camera_ultra = Column(Integer)
    camera_telephoto = Column(Integer)
    camera_front = Column(Integer)
    battery = Column(Integer)
    charging_wired = Column(Integer)
    charging_wireless = Column(Integer)
    weight = Column(Integer)
    url = Column(String(500))
    image_url = Column(String(500))
    # 影像评分相关字段（可为空，向后兼容）
    sensor_main = Column(String(50))  # 主摄传感器型号，如 "LYT-900"
    telephoto_type = Column(String(30))  # 长焦类型：双潜望/单潜望/直立长焦/无
    has_ois = Column(Boolean, default=None)  # 是否支持OIS光学防抖
    image_brand = Column(String(30))  # 影像品牌：XMAGE/徕卡/哈苏/蔡司/Blueimage/原色
    camera_score = Column(Integer)  # 综合影像评分（缓存字段）
    features = Column(Text)  # 特性标签 JSON数组，如 '["游戏", "电竞"]'
    suitable_for = Column(Text)  # 适用人群 JSON数组，如 '["游戏玩家", "学生"]'
    pros = Column(Text)  # 优点 JSON数组
    cons = Column(Text)  # 缺点 JSON数组
    created_at = Column(String(30))
    updated_at = Column(String(30))

    @staticmethod
    def _parse_json_field(value, default=None):
        """解析 JSON 字段，处理 None 和无效 JSON。"""
        if default is None:
            default = []
        if not value:
            return default
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default

    def to_dict(self):
        return {
            "id": self.id,
            "brand": self.brand,
            "model": self.model,
            "price": self.price,
            "release_date": self.release_date,
            "screen": {"size": self.screen_size, "type": self.screen_type, "refresh": self.screen_refresh},
            "processor": self.processor,
            "ram": self.ram,
            "storage": self.storage,
            "camera": {
                "main": self.camera_main,
                "ultra": self.camera_ultra,
                "telephoto": self.camera_telephoto,
                "front": self.camera_front,
                "sensorMain": self.sensor_main,
                "telephotoType": self.telephoto_type,
                "hasOis": self.has_ois,
                "imageBrand": self.image_brand,
                "score": self.camera_score
            },
            "battery": self.battery,
            "charging": {"wired": self.charging_wired, "wireless": self.charging_wireless},
            "weight": self.weight,
            "url": self.url,
            "imageUrl": self.image_url,
            "features": self._parse_json_field(self.features),
            "suitable_for": self._parse_json_field(self.suitable_for),
            "pros": self._parse_json_field(self.pros),
            "cons": self._parse_json_field(self.cons),
        }


settings = get_settings()
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    import sqlite3
    import os
    db_path = settings.database_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    conn.close()


# 安兔兔处理器跑分数据 (2026-05)
# 数据来源: https://www.antutu.com/ranking/rank301.htm
# 数据现已从 backend/data/antutu_scores.json 延迟加载
#
# 通过 _get_antutu_data() 获取 (scores_dict, aliases_dict)
# 模块级 ANTUTU_SCORES / _PROCESSOR_ALIASES 在首次导入时自动填充

def _get_antutu_data():
    """延迟加载安兔兔跑分和别名数据（从 antutu_scores.json 配置文件）。"""
    from backend.config import load_antutu_scores
    return load_antutu_scores()


# 模块级变量，保持向后兼容（首次导入时从JSON加载）
ANTUTU_SCORES, _PROCESSOR_ALIASES = _get_antutu_data()

# 处理器性能等级映射（基于安兔兔跑分）
# 用于智能排序，数值越高性能越强
PROCESSOR_PERFORMANCE_TIER = {
    # 旗舰级 (tier 4): 跑分 130万+
    "骁龙8 Gen3": 4,
    "骁龙8Gen3": 4,
    "骁龙8 Gen2": 4,
    "骁龙8Gen2": 4,
    "天玑9300+": 4,
    "天玑9300": 4,
    "天玑9200+": 4,
    "天玑9200": 4,
    "A17 Pro": 4,
    "A17Pro": 4,
    "A16": 4,

    # 高端级 (tier 3): 跑分 80-130万
    "骁龙7+ Gen3": 3,
    "骁龙7+Gen3": 3,
    "骁龙7+ Gen2": 3,
    "骁龙7+Gen2": 3,
    "天玑8300": 3,
    "天玑8300-Ultra": 3,
    "骁龙8+ Gen1": 3,
    "骁龙8+Gen1": 3,
    "骁龙8 Gen1": 3,
    "骁龙8Gen1": 3,
    "骁龙888+": 3,
    "骁龙888 Plus": 3,
    "骁龙888": 3,
    "骁龙870": 3,
    "天玑8100": 3,
    "天玑8100-Max": 3,
    "天玑8200": 3,
    "天玑8200 Ultra": 3,

    # 中端级 (tier 2): 跑分 40-80万
    "骁龙7s Gen2": 2,
    "骁龙7sGen2": 2,
    "天玑7200": 2,
    "天玑7200-Ultra": 2,
    "骁龙6 Gen1": 2,
    "骁龙6Gen1": 2,
    "骁龙778G": 2,
    "骁龙778G Plus": 2,
    "骁龙780G": 2,
    "天玑1200": 2,
    "天玑1100": 2,
    "麒麟9000": 2,
    "麒麟9000s": 2,
    "麒麟9010": 2,

    # 入门级 (tier 1): 跑分 <40万
    "天玑6020": 1,
    "骁龙480": 1,
    "骁龙695": 1,
    "天玑700": 1,
    "天玑810": 1,
    "骁龙680": 1,
    "Helio G99": 1,
}


# 品牌前缀映射（匹配前剥离）
_BRAND_PREFIX_PATTERNS = [
    "高通 ", "高通",
    "联发科 ", "联发科",
    "海思 ", "海思",
    "三星 ", "三星",
    "苹果 ", "苹果",
    "华为 ", "华为",
]


def _normalize_processor(raw: str) -> str:
    """预处理处理器字符串：剥离品牌前缀、规范化空格、应用别名。"""
    if not raw:
        return ""
    s = raw.strip()

    # 1. 剥离品牌前缀（中文 + 英文）
    for prefix in _BRAND_PREFIX_PATTERNS:
        if s.startswith(prefix):
            s = s[len(prefix):].strip()
            break
    # 剥离英文品牌前缀
    for eng_prefix in ("HUAWEI ", "HUAWEI", "Apple ", "Apple", "Samsung ", "Samsung"):
        if s.startswith(eng_prefix):
            s = s[len(eng_prefix):].strip()
            break

    # 2. 规范化空格：多个空格合并为一个
    s = re.sub(r"\s+", " ", s).strip()

    # 3. 移除中文与字母/数字之间的空格（如 "骁龙 8" -> "骁龙8", "天玑 9500+" -> "天玑9500+"）
    s = re.sub(r"([一-鿿])\s+([A-Za-z0-9])", r"\1\2", s)
    s = re.sub(r"([A-Za-z0-9])\s+([一-鿿])", r"\1\2", s)

    # 4. 应用别名映射（在空格规范化之后）
    _, aliases = _get_antutu_data()
    if s in aliases:
        s = aliases[s]

    return s


def _find_matching_key(scores: dict, processor: str) -> str | None:
    """
    在跑分字典中查找处理器的匹配键。

    匹配策略（按优先级）：
    1. 原始字符串直接匹配
    2. 规范化后直接匹配
    3. 去空格后完全相等匹配
    4. 规范化+去空格后完全相等匹配
    5. 模糊包含匹配（双向子串）
    6. 规范化后再模糊包含匹配
    7. 去空格后模糊包含匹配

    Returns:
        匹配到的键，未匹配返回 None
    """
    if not processor or not processor.strip():
        return None

    # 策略1: 原始字符串直接匹配
    if processor in scores:
        return processor

    # 策略2: 规范化后直接匹配
    normalized = _normalize_processor(processor)
    if normalized and normalized in scores:
        return normalized

    # 策略3: 去空格后完全相等匹配
    processor_no_space = processor.replace(" ", "")
    for key in scores:
        if key.replace(" ", "") == processor_no_space:
            return key

    # 策略4: 规范化+去空格后完全相等匹配
    if normalized:
        norm_no_space = normalized.replace(" ", "")
        for key in scores:
            if key.replace(" ", "") == norm_no_space:
                return key

    # 策略5: 模糊包含匹配（双向子串）
    processor_lower = processor.lower()
    for key in scores:
        if processor_lower in key.lower() or key.lower() in processor_lower:
            return key

    # 策略6: 规范化后再模糊包含匹配
    if normalized:
        norm_lower = normalized.lower()
        for key in scores:
            if norm_lower in key.lower() or key.lower() in norm_lower:
                return key

    # 策略7: 去空格后模糊包含匹配（解决 "骁龙 8" vs "骁龙8" 类差异）
    for key in scores:
        kns = key.replace(" ", "").lower()
        pns = (normalized.replace(" ", "") if normalized else processor_no_space).lower()
        if pns in kns or kns in pns:
            return key

    return None


def get_antutu_score(processor: str) -> int:
    """获取处理器的安兔兔跑分，未知处理器返回0。"""
    if not processor:
        return 0
    scores, _ = _get_antutu_data()
    key = _find_matching_key(scores, processor)
    return scores[key] if key else 0


def get_canonical_processor(processor: str) -> str:
    """返回处理器的规范形式（跑分字典中的键），无法匹配则返回原始值。"""
    if not processor:
        return processor or ""
    scores, _ = _get_antutu_data()
    key = _find_matching_key(scores, processor)
    if key:
        return key
    normalized = _normalize_processor(processor)
    return normalized if normalized else processor

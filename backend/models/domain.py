from sqlalchemy import Column, Integer, String, Text, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import get_settings
import json

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
    features = Column(Text)
    url = Column(String(500))
    image_url = Column(String(500))
    pros = Column(Text)
    cons = Column(Text)
    suitable_for = Column(Text)
    created_at = Column(String(30))
    updated_at = Column(String(30))

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
                "front": self.camera_front
            },
            "battery": self.battery,
            "charging": {"wired": self.charging_wired, "wireless": self.charging_wireless},
            "weight": self.weight,
            "features": json.loads(self.features) if self.features else [],
            "url": self.url,
            "imageUrl": self.image_url,
            "pros": json.loads(self.pros) if self.pros else [],
            "cons": json.loads(self.cons) if self.cons else [],
            "suitable_for": json.loads(self.suitable_for) if self.suitable_for else []
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

CREATE TABLE IF NOT EXISTS phones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    price INTEGER NOT NULL,
    release_date TEXT,
    screen_size REAL,
    screen_type TEXT,
    screen_refresh INTEGER,
    processor TEXT,
    ram INTEGER,
    storage INTEGER,
    camera_main INTEGER,
    camera_ultra INTEGER,
    camera_telephoto INTEGER,
    camera_front INTEGER,
    battery INTEGER,
    charging_wired INTEGER,
    charging_wireless INTEGER,
    weight INTEGER,
    features TEXT,
    url TEXT,
    image_url TEXT,
    pros TEXT,
    cons TEXT,
    suitable_for TEXT,
    -- 影像字段
    sensor_main TEXT,
    telephoto_type TEXT,
    has_ois INTEGER DEFAULT NULL,  -- 是否支持OIS光学防抖 (0=否/1=是/NULL=未知)
    image_brand TEXT,
    camera_score INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_phones_brand ON phones(brand);
CREATE INDEX IF NOT EXISTS idx_phones_price ON phones(price);
CREATE INDEX IF NOT EXISTS idx_phones_processor ON phones(processor);

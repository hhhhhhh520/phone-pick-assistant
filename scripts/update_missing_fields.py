import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 数据更新映射
# 格式: '型号': {'字段名': 值, ...}
# 特殊值: '不支持' -> 0, '无' -> 0, '支持' -> 1

updates = {
    # ========== OPPO ==========
    'Find N3': {
        'charging_wireless': 0,  # 不支持
    },
    'Find N3 Flip': {
        'charging_wireless': 0,
    },
    'OPPO A3i（8GB/256GB）': {
        'charging_wireless': 0,
        'camera_telephoto': 0,  # 无长焦镜头
        'camera_ultra': 0,  # 无超广角
        'charging_wired': 45,
        'screen_type': 'LCD',
    },
    'OPPO A5 活力版(8GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 200,
        'camera_ultra': 200,
        'charging_wired': 45,
        'camera_main': 5000,
        'camera_front': 800,
        'screen_type': 'LCD',
    },
    'OPPO A6 Pro(8GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 200,
        'camera_ultra': 200,
        'charging_wired': 80,
    },
    'OPPO A6s Pro(8GB/128GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 200,
        'camera_ultra': 200,
        'charging_wired': 80,
        'camera_main': 5000,
        'camera_front': 1600,
    },
    'OPPO A6s Pro(8GB/256GB)': {
        'charging_wireless': 0,
        'charging_wired': 80,
    },
    'OPPO Find N2（12GB/256GB）': {
        'charging_wireless': 15,
        'camera_telephoto': 3200,
        'camera_ultra': 4800,
        'charging_wired': 67,
        'sensor_main': '索尼IMX890',
        'screen_type': 'AMOLED',
    },
    'OPPO Find N5(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 800,
        'charging_wired': 80,
    },
    'OPPO Find N6(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
        'camera_main': 20000,  # 2亿像素
        'camera_front': 2000,
    },
    'OPPO Find X6 Pro（12GB/256GB）': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 100,
        'sensor_main': '索尼IMX989',
    },
    'OPPO Find X6（12GB/256GB）': {
        'charging_wireless': 0,
        'charging_wired': 80,
    },
    'OPPO Find X7 Pro': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 100,
        'sensor_main': '索尼LYT808',
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'OPPO Find X7 Ultra(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 100,
        'sensor_main': '索尼LYT900',
    },
    'OPPO Find X8 Pro(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X8 Ultra(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X8 Ultra(16GB/512GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X8(16GB/1TB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X8s(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X8s+(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X9 Pro(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'OPPO Find X9 Pro(12GB/512GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X9 Pro(16GB/512GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X9 Ultra(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'OPPO Find X9(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'OPPO Find X9(12GB/512GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
    },
    'OPPO Find X9s Pro(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 80,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'OPPO Find X9s Pro(16GB/512GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '哈苏',
    },
    'OPPO K11（12GB/512GB）': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 100,
        'sensor_main': '索尼IMX890',
    },
    'OPPO K12(8GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 100,
        'sensor_main': '索尼IMX882',
    },
    'OPPO K12s(8GB/128GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 200,
        'charging_wired': 45,
    },
    'OPPO K13 Turbo Pro(12GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 80,
    },
    'OPPO K13s（8GB/256GB）': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 200,
        'charging_wired': 45,
        'camera_main': 5000,
        'camera_front': 800,
    },
    'OPPO K15 Pro(12GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 100,
        'sensor_main': '索尼IMX890',
    },
    'OPPO K15 Pro(12GB/512GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 100,
        'sensor_main': '索尼IMX890',
    },
    'OPPO K15 Pro+(12GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 100,
        'sensor_main': '索尼IMX890',
    },
    'OPPO Reno 13(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 800,
        'charging_wired': 80,
        'sensor_main': '索尼IMX890',
    },
    'OPPO Reno14 Pro(12GB/256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 800,
        'charging_wired': 80,
    },
    'OPPO Reno14(12GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 80,
    },
    'OPPO Reno15 Pro(12GB+256GB)': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 800,
        'charging_wired': 80,
    },
    'OPPO Reno15(12GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 80,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'OPPO Reno15(12GB/512GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 80,
    },
    'OPPO Reno15c(12GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
        'charging_wired': 80,
    },
    'OPPO Reno5（12GB/256GB/全网通/5G版）': {
        'charging_wireless': 0,
        'camera_telephoto': 200,
        'camera_ultra': 800,
        'charging_wired': 65,
        'sensor_main': '豪威OV64B',
    },
    'OPPO Reno6（12GB/256GB/全网通/5G版）': {
        'charging_wireless': 0,
        'camera_telephoto': 200,
        'camera_ultra': 800,
        'charging_wired': 65,
    },
    'OPPO Reno8（8GB/256GB）': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 200,
        'charging_wired': 80,
    },
    'Reno 11 Pro': {
        'charging_wireless': 0,
    },

    # ========== 华为 ==========
    'HUAWEI Mate 60 Pro（12GB/256GB）': {
        'charging_wireless': 50,
        'camera_telephoto': 4800,
        'camera_ultra': 1200,
        'charging_wired': 88,
    },
    '华为 Pura 90 Pro': {
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': 'XMAGE',
    },
    '华为 Pura 90 Pro Max': {
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': 'XMAGE',
    },
    '华为 Pura X Max': {
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': 'XMAGE',
    },
    '华为 畅享90 Pro Max 128GB': {
        'camera_main': 5000,
        'camera_front': 800,
        'telephoto_type': '无',
        'has_ois': 0,
        'image_brand': '无',
    },
    '华为Pura X Max(16GB/512GB/典藏版)': {
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': 'XMAGE',
    },
    '华为novaFlip': {
        'charging_wireless': 0,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'HUAWEI Mate 80(12GB/256GB)': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'HUAWEI Pura X(12GB/256GB)': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '华为 Pura 90 Pro Max(16GB/512GB)': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '华为畅享90 Plus 128GB': {
        'camera_main': 5000,
        'camera_front': 800,
    },
    '华为畅享90 Pro Max 256GB': {
        'charging_wired': 22,
    },
    '华为畅享90 Pro Max 512GB': {
        'charging_wired': 22,
    },

    # ========== 小米 ==========
    'Redmi  K80至尊版(12GB/512GB)': {
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '小米',
    },
    'Redmi  Note 14 Pro(8GB/128GB)IP68防尘防水，固态电解质电池，高光护眼屏': {
        'camera_main': 5000,
        'camera_front': 1600,
        'telephoto_type': '无',
        'has_ois': 1,
    },
    'Redmi  Note 14(6GB/128GB)': {
        'camera_main': 5000,
        'camera_front': 1300,
    },
    'Redmi  Note 15(6GB/128GB)第三代骁龙6，5800mAh大电量，IP66防尘防水': {
        'camera_main': 5000,
        'camera_front': 1600,
        'telephoto_type': '无',
        'has_ois': 0,
    },
    'Redmi K40（12GB/256GB/全网通/5G版）高通骁龙870，4800万像素三摄，7.8mm轻薄设计，4520mAh大电量': {
        'camera_main': 4800,
    },
    'MIX Flip': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
    },
    'Redmi K70 Pro': {
        'charging_wireless': 0,
        'camera_telephoto': 5000,
    },
    'Redmi K80': {
        'charging_wireless': 0,
        'camera_telephoto': 5000,
    },
    'Redmi Note 14 Pro+': {
        'charging_wireless': 0,
        'camera_telephoto': 5000,
    },
    'Redmi Note 14': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
    },
    'Redmi Note 13 Pro（8GB/128GB）': {
        'camera_main': 20000,  # 2亿像素
    },
    '小米MIX FOLD 4(12GB/256GB)': {
        'camera_main': 5000,
        'camera_front': 1600,
    },
    '小米17 Pro（12GB/512GB）': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '小米 17 Ultra': {
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '徕卡',
    },

    # ========== 真我 ==========
    '真我GT Neo6(12GB/256GB)': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
    },
    '真我GT5 Pro(12GB/256GB)': {
        'charging_wireless': 50,
        'sensor_main': '索尼LYT808',
    },
    '真我GT8(12GB/256GB)': {
        'charging_wireless': 0,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '理光GR',
    },
    '真我GT8(12GB/512GB)': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '理光GR',
    },
    '真我GT8(16GB/1TB)': {
        'charging_wired': 120,
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '理光GR',
    },
    '真我GT8(16GB/256GB)': {
        'charging_wired': 100,
    },
    '真我GT8(16GB/512GB)': {
        'charging_wired': 120,
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '理光GR',
    },
    '真我GT7 Pro(12GB/256GB)': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '真我GT7 Pro(12GB/512GB)': {
        'charging_wired': 100,
    },
    '真我GT8 Pro（12GB/256GB）': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '真我GT8 Pro（12GB/512GB）': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '真我15 Pro（12GB+256GB）': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '真我Neo7 SE(8GB/256GB)': {
        'camera_main': 5000,
        'camera_front': 1600,
    },
    '真我Neo7 Turbo(12GB/256GB)': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '真我Neo7 Turbo(12GB/512GB)': {
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '真我Neo7(12GB/256GB)': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 1600,
        'telephoto_type': '无',
        'has_ois': 1,
    },
    '真我Neo7 Turbo(16GB/512GB)': {
        'charging_wired': 100,
    },
    '真我Neo7x（ 8GB+256GB）': {
        'camera_main': 5000,
        'camera_front': 1600,
    },
    '真我Neo8(12GB+256GB)': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
    },
    '真我Neo8(12GB/512GB)': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
    },
    '真我Neo8(16GB/1TB)': {
        'charging_wired': 120,
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
    },
    '真我Neo8(16GB/512GB)': {
        'charging_wired': 120,
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
    },

    # ========== 三星 ==========
    '三星Galaxy S25 Ultra': {
        'charging_wireless': 1,  # 支持Qi无线充电
        'camera_main': 20000,  # 2亿像素
        'camera_front': 1200,
        'telephoto_type': '光学变焦',
        'has_ois': 1,
        'image_brand': '三星',
    },
    '三星Galaxy A56(8GB/256GB)': {
        'camera_main': 5000,
    },
    '三星Galaxy S21 Ultra（12GB/256GB/全网通/5G版）': {
        'camera_main': 10800,  # 1.08亿像素
    },
    '三星Galaxy S24 Ultra(12GB/256GB)': {
        'charging_wired': 45,
    },
    '三星Galaxy S24(8GB/256GB)': {
        'charging_wired': 25,
    },
    '三星Galaxy S25 Ultra(12GB/256GB)': {
        'charging_wired': 45,
    },
    '三星Galaxy S25(12GB/256GB)': {
        'charging_wired': 25,
    },
    '三星Galaxy S26 Ultra(12GB/512GB)': {
        'charging_wired': 45,
    },
    '三星Galaxy S26+（12GB+512GB）': {
        'charging_wired': 45,
    },
    '三星Galaxy S26（12GB/256GB）': {
        'charging_wired': 25,
    },
    '三星Galaxy Z Flip7 FE（8GB/256GB）': {
        'charging_wired': 25,
    },
    '三星Galaxy Z Flip7（12GB/256GB）': {
        'charging_wired': 25,
        'camera_main': 5000,
    },
    '三星Galaxy Z Fold7(12GB/256GB)': {
        'camera_main': 5000,
    },
    '三星Galaxy Z TriFold（16GB/512GB）': {
        'camera_main': 20000,  # 2亿像素
    },
    '三星W25(16GB/512GB)': {
        'camera_main': 20000,  # 2亿像素
    },

    # ========== vivo ==========
    'vivo X200': {
        'charging_wireless': 30,
    },
    'iQOO 12': {
        'charging_wireless': 0,
    },
    'iQOO 12 Pro': {
        'charging_wireless': 50,
    },
    'vivo X300 Ultra(12GB/256GB)': {
        'charging_wireless': 40,
        'camera_telephoto': 20000,  # 2亿像素
        'camera_ultra': 5000,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'vivo X300 Ultra(12GB/512GB)': {
        'charging_wireless': 40,
        'camera_telephoto': 20000,
        'camera_ultra': 5000,
        'charging_wired': 90,
    },
    'vivo X300 Ultra(16GB/512GB)': {
        'charging_wireless': 40,
        'camera_telephoto': 20000,
        'camera_ultra': 5000,
        'charging_wired': 90,
    },
    'vivo X300(12GB/256GB)': {
        'charging_wireless': 40,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 90,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    'vivo Y600 Pro（8GB/256GB）': {
        'charging_wireless': 0,
        'camera_main': 5000,
        'camera_front': 800,
    },
    'vivo(S50 12GB/512GB)': {
        'charging_wireless': 30,
        'charging_wired': 90,
    },

    # ========== 一加 ==========
    '一加13（12GB/256GB）': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 5000,
        'charging_wired': 100,
        'sensor_main': '索尼LYT808',
        'camera_main': 5000,
        'camera_front': 3200,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '哈苏',
    },
    '一加13T(12GB/256GB)': {
        'charging_wired': 80,
        'camera_main': 5000,
        'camera_front': 1600,
    },
    '一加13T(12GB/512GB)': {
        'charging_wired': 80,
        'camera_main': 5000,
        'camera_front': 1600,
    },
    '一加15T(12GB/256GB)': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '一加15T(12GB/512GB)': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '一加15（12GB/256GB）': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 3200,
    },
    '一加Ace 3 Pro（12GB/256GB）': {
        'charging_wired': 100,
    },
    '一加Ace 5(12GB/256GB)': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 1600,
    },
    '一加Ace 6(12GB/256GB)': {
        'charging_wired': 100,
        'camera_main': 5000,
        'camera_front': 1600,
    },
    '一加Ace 5 至尊版(12GB/256GB)': {
        'camera_main': 5000,
        'camera_front': 1600,
    },
    '一加Ace 6 至尊版(12GB/256GB)': {
        'camera_main': 5000,
        'camera_front': 3200,
    },

    # ========== 苹果 ==========
    'Apple（苹果）iPhone Air 1TB': {
        'charging_wired': 20,
    },
    'Apple（苹果）iPhone Air 256GB': {
        'camera_main': 4800,
        'camera_front': 1200,
    },
    'iPhone 14': {
        'camera_telephoto': 1200,
    },
    'iPhone 15': {
        'camera_telephoto': 1200,
    },
    'iPhone 16': {
        'camera_telephoto': 1200,
    },
    'iPhone 16 Plus': {
        'camera_telephoto': 1200,
    },
    '苹果 iPhone 17 Pro Max': {
        'charging_wired': 35,
        'telephoto_type': '光学变焦',
        'has_ois': 1,
        'image_brand': 'Apple',
    },
    '苹果 iPhone 17': {
        'camera_main': 4800,
        'camera_front': 1200,
        'telephoto_type': '光学变焦',
        'has_ois': 1,
        'image_brand': 'Apple',
    },
    '苹果iPhone 17 Pro Max（1TB）': {
        'camera_main': 4800,
        'camera_front': 1200,
        'charging_wired': 35,
    },
    '苹果iPhone 17 Pro Max（256GB）': {
        'camera_main': 4800,
        'camera_front': 1200,
    },
    '苹果iPhone 17 Pro Max（2TB）': {
        'camera_main': 4800,
        'camera_front': 1200,
        'charging_wired': 35,
    },
    '苹果iPhone 17 Pro Max（512GB）': {
        'camera_main': 4800,
        'camera_front': 1200,
        'charging_wired': 35,
    },
    '苹果iPhone 17 Pro（1TB）': {
        'camera_main': 4800,
        'camera_front': 1200,
        'charging_wired': 35,
    },
    '苹果iPhone 17 Pro（256GB）': {
        'charging_wired': 35,
    },
    '苹果iPhone 17 Pro（512GB）': {
        'camera_main': 4800,
        'camera_front': 1200,
        'charging_wired': 35,
    },
    '苹果iPhone 17e（256GB）': {
        'camera_main': 4800,
        'camera_front': 1200,
        'charging_wired': 20,
    },
    '苹果iPhone 17（256GB）': {
        'charging_wired': 35,
    },
    '苹果iPhone 17（512GB）': {
        'charging_wired': 35,
    },
    '苹果iPhone SE 3（128GB）': {
        'charging_wired': 20,
    },

    # ========== 荣耀 ==========
    'Magic V Flip': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
    },
    '荣耀 500 Pro': {
        'charging_wireless': 50,
        'camera_telephoto': 5000,
        'camera_ultra': 1200,
        'camera_main': 20000,  # 2亿像素
        'camera_front': 5000,
        'telephoto_type': '潜望式',
        'has_ois': 1,
        'image_brand': '荣耀',
    },
    '荣耀500 Pro(12GB/256GB)': {
        'charging_wired': 80,
    },
    '荣耀X50': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
    },
    '荣耀X60 Pro': {
        'charging_wireless': 0,
        'camera_telephoto': 0,
        'camera_ultra': 800,
    },

    # ========== 魅族 ==========
    '魅族21': {
        'charging_wireless': 0,
        'camera_telephoto': 5000,
    },
    '魅族21 Note(16GB/256GB)': {
        'charging_wired': 66,
    },
    '魅族21 Note(16GB/512GB)': {
        'charging_wired': 66,
    },
    '魅族21 Pro(12GB+256GB)': {
        'charging_wired': 80,
    },
    '魅族21 Pro(16GB+512GB)': {
        'charging_wired': 80,
    },
    '魅族21(12GB/512GB)': {
        'charging_wired': 80,
    },
    '魅族21(8GB/256GB)': {
        'charging_wired': 80,
    },
    '魅族22（12GB/256GB）': {
        'charging_wired': 80,
    },
    '魅族22（12GB/512GB）': {
        'charging_wired': 80,
    },
    '魅族22（16GB+1TB）': {
        'charging_wired': 80,
    },
    '魅族22（16GB+512GB）': {
        'charging_wired': 80,
    },

    # ========== 联想 ==========
    'Moto Edge S Pro（8GB/128GB/全网通/5G版）': {
        'camera_main': 10000,  # 1亿像素
    },
    'Moto Edge S30（12GB/512GB/5G版/冠军版）': {
        'camera_main': 10000,  # 1亿像素
    },
    'moto S50 Neo(8GB/256GB)': {
        'charging_wired': 68,
    },
}

# 执行更新
updated = 0
not_found = []

for model, fields in updates.items():
    # 检查型号是否存在
    cursor.execute('SELECT id FROM phones WHERE model = ?', (model,))
    row = cursor.fetchone()

    if row:
        id = row[0]
        for field, value in fields.items():
            cursor.execute(f'UPDATE phones SET {field} = ? WHERE id = ?', (value, id))
        updated += 1
    else:
        not_found.append(model)

conn.commit()

print(f'已更新: {updated}条记录')
if not_found:
    print(f'\n未找到的型号 ({len(not_found)}条):')
    for m in not_found[:20]:  # 只显示前20条
        print(f'  {m}')
    if len(not_found) > 20:
        print(f'  ... 还有 {len(not_found) - 20} 条')

conn.close()

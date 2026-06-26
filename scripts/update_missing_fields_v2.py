import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 获取所有型号
cursor.execute('SELECT id, model FROM phones')
all_phones = {row[1]: row[0] for row in cursor.fetchall()}

def find_model(keyword):
    """模糊查找型号"""
    for model in all_phones:
        if keyword in model:
            return model, all_phones[model]
    return None, None

def update_phone(keyword, fields):
    """根据关键字更新手机"""
    model, id = find_model(keyword)
    if id:
        for field, value in fields.items():
            cursor.execute(f'UPDATE phones SET {field} = ? WHERE id = ?', (value, id))
        return True
    return False

updated = 0
not_found = []

# ========== OPPO ==========
oppo_updates = [
    ('Find N3', {'charging_wireless': 0}),
    ('Find N3 Flip', {'charging_wireless': 0}),
    ('OPPO A3i', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 0, 'charging_wired': 45, 'screen_type': 'LCD'}),
    ('OPPO A5 活力版', {'charging_wireless': 0, 'camera_telephoto': 200, 'camera_ultra': 200, 'charging_wired': 45, 'camera_main': 5000, 'camera_front': 800, 'screen_type': 'LCD'}),
    ('OPPO A6 Pro', {'charging_wireless': 0, 'camera_telephoto': 200, 'camera_ultra': 200, 'charging_wired': 80}),
    ('OPPO A6s Pro(8GB/128GB)', {'charging_wireless': 0, 'camera_telephoto': 200, 'camera_ultra': 200, 'charging_wired': 80, 'camera_main': 5000, 'camera_front': 1600}),
    ('OPPO A6s Pro(8GB/256GB)', {'charging_wireless': 0, 'charging_wired': 80}),
    ('OPPO Find N2', {'charging_wireless': 15, 'camera_telephoto': 3200, 'camera_ultra': 4800, 'charging_wired': 67, 'sensor_main': '索尼IMX890', 'screen_type': 'AMOLED'}),
    ('OPPO Find N5', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 800, 'charging_wired': 80}),
    ('OPPO Find N6', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80, 'camera_main': 20000, 'camera_front': 2000}),
    ('OPPO Find X6 Pro', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 100, 'sensor_main': '索尼IMX989'}),
    ('OPPO Find X6（', {'charging_wireless': 0, 'charging_wired': 80}),
    ('OPPO Find X7 Pro', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 100, 'sensor_main': '索尼LYT808', 'camera_main': 5000, 'camera_front': 3200}),
    ('OPPO Find X7 Ultra', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 100, 'sensor_main': '索尼LYT900'}),
    ('OPPO Find X8 Pro(12GB', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X8 Ultra(12GB', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X8 Ultra(16GB', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X8(16GB', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X8s(12GB', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X8s+', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X9 Pro(12GB/256GB)', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'camera_main': 5000, 'camera_front': 3200}),
    ('OPPO Find X9 Pro(12GB/512GB)', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X9 Pro(16GB', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X9 Ultra', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'camera_main': 5000, 'camera_front': 3200}),
    ('OPPO Find X9(12GB/256GB)', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80, 'camera_main': 5000, 'camera_front': 3200}),
    ('OPPO Find X9(12GB/512GB)', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80}),
    ('OPPO Find X9s Pro(12GB', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 80, 'camera_main': 5000, 'camera_front': 3200}),
    ('OPPO Find X9s Pro(16GB', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '哈苏'}),
    ('OPPO K11', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 100, 'sensor_main': '索尼IMX890'}),
    ('OPPO K12(8GB', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 100, 'sensor_main': '索尼IMX882'}),
    ('OPPO K12s', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 200, 'charging_wired': 45}),
    ('OPPO K13 Turbo', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 80}),
    ('OPPO K13s', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 200, 'charging_wired': 45, 'camera_main': 5000, 'camera_front': 800}),
    ('OPPO K15 Pro(12GB/256GB)', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 100, 'sensor_main': '索尼IMX890'}),
    ('OPPO K15 Pro(12GB/512GB)', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 100, 'sensor_main': '索尼IMX890'}),
    ('OPPO K15 Pro+', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 100, 'sensor_main': '索尼IMX890'}),
    ('OPPO Reno 13', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 800, 'charging_wired': 80, 'sensor_main': '索尼IMX890'}),
    ('OPPO Reno14 Pro', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 800, 'charging_wired': 80}),
    ('OPPO Reno14(12GB', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 80}),
    ('OPPO Reno15 Pro', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 800, 'charging_wired': 80}),
    ('OPPO Reno15(12GB/256GB)', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 80, 'camera_main': 5000, 'camera_front': 3200}),
    ('OPPO Reno15(12GB/512GB)', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 80}),
    ('OPPO Reno15c', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800, 'charging_wired': 80}),
    ('OPPO Reno5', {'charging_wireless': 0, 'camera_telephoto': 200, 'camera_ultra': 800, 'charging_wired': 65, 'sensor_main': '豪威OV64B'}),
    ('OPPO Reno6', {'charging_wireless': 0, 'camera_telephoto': 200, 'camera_ultra': 800, 'charging_wired': 65}),
    ('OPPO Reno8（8GB', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 200, 'charging_wired': 80}),
    ('Reno 11 Pro', {'charging_wireless': 0}),
]

for keyword, fields in oppo_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'OPPO: {keyword}')

# ========== 华为 ==========
huawei_updates = [
    ('HUAWEI Mate 60 Pro', {'charging_wireless': 50, 'camera_telephoto': 4800, 'camera_ultra': 1200, 'charging_wired': 88}),
    ('华为 Pura 90 Pro', {'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': 'XMAGE'}),
    ('华为 Pura 90 Pro Max', {'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': 'XMAGE'}),
    ('华为 Pura X Max', {'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': 'XMAGE'}),
    ('华为 畅享90 Pro Max 128GB', {'camera_main': 5000, 'camera_front': 800, 'telephoto_type': '无', 'has_ois': 0}),
    ('华为Pura X Max(16GB', {'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': 'XMAGE'}),
    ('华为novaFlip', {'charging_wireless': 0, 'camera_main': 5000, 'camera_front': 3200}),
    ('HUAWEI Mate 80', {'camera_main': 5000, 'camera_front': 3200}),
    ('HUAWEI Pura X(12GB/256GB)', {'camera_main': 5000, 'camera_front': 3200}),
    ('华为畅享90 Plus', {'camera_main': 5000, 'camera_front': 800}),
    ('华为畅享90 Pro Max 256GB', {'charging_wired': 22}),
    ('华为畅享90 Pro Max 512GB', {'charging_wired': 22}),
]

for keyword, fields in huawei_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'华为: {keyword}')

# ========== 小米 ==========
xiaomi_updates = [
    ('Redmi  K80至尊版', {'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '小米'}),
    ('Redmi  Note 14 Pro(8GB', {'camera_main': 5000, 'camera_front': 1600, 'telephoto_type': '无', 'has_ois': 1}),
    ('Redmi  Note 14(6GB', {'camera_main': 5000, 'camera_front': 1300}),
    ('Redmi  Note 15(6GB', {'camera_main': 5000, 'camera_front': 1600, 'telephoto_type': '无', 'has_ois': 0}),
    ('Redmi K40', {'camera_main': 4800}),
    ('MIX Flip', {'charging_wireless': 0, 'camera_telephoto': 0}),
    ('Redmi K70 Pro', {'charging_wireless': 0, 'camera_telephoto': 5000}),
    ('Redmi K80(12GB', {'charging_wireless': 0, 'camera_telephoto': 5000}),
    ('Redmi Note 14 Pro+', {'charging_wireless': 0, 'camera_telephoto': 5000}),
    ('Redmi Note 14', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800}),
    ('Redmi Note 13 Pro', {'camera_main': 20000}),
    ('小米MIX FOLD 4', {'camera_main': 5000, 'camera_front': 1600}),
    ('小米17 Pro', {'camera_main': 5000, 'camera_front': 3200}),
    ('小米 17 Ultra', {'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '徕卡'}),
]

for keyword, fields in xiaomi_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'小米: {keyword}')

# ========== 真我 ==========
realme_updates = [
    ('真我GT Neo6(12GB', {'charging_wireless': 0, 'camera_telephoto': 0}),
    ('真我GT5 Pro', {'charging_wireless': 50, 'sensor_main': '索尼LYT808'}),
    ('真我GT8(12GB/256GB)', {'charging_wireless': 0, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '理光GR'}),
    ('真我GT8(12GB/512GB)', {'charging_wired': 100, 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '理光GR'}),
    ('真我GT8(16GB/1TB)', {'charging_wired': 120, 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '理光GR'}),
    ('真我GT8(16GB/256GB)', {'charging_wired': 100}),
    ('真我GT8(16GB/512GB)', {'charging_wired': 120, 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '理光GR'}),
    ('真我GT7 Pro(12GB/256GB)', {'camera_main': 5000, 'camera_front': 3200}),
    ('真我GT7 Pro(12GB/512GB)', {'charging_wired': 100}),
    ('真我GT8 Pro（12GB/256GB）', {'camera_main': 5000, 'camera_front': 3200}),
    ('真我GT8 Pro（12GB/512GB）', {'camera_main': 5000, 'camera_front': 3200}),
    ('真我15 Pro', {'camera_main': 5000, 'camera_front': 3200}),
    ('真我Neo7 SE', {'camera_main': 5000, 'camera_front': 1600}),
    ('真我Neo7 Turbo(12GB/256GB)', {'camera_main': 5000, 'camera_front': 3200}),
    ('真我Neo7 Turbo(12GB/512GB)', {'camera_main': 5000, 'camera_front': 3200}),
    ('真我Neo7(12GB/256GB)', {'charging_wired': 100, 'camera_main': 5000, 'camera_front': 1600, 'telephoto_type': '无', 'has_ois': 1}),
    ('真我Neo7 Turbo(16GB', {'charging_wired': 100}),
    ('真我Neo7x', {'camera_main': 5000, 'camera_front': 1600}),
    ('真我Neo8(12GB+256GB)', {'charging_wired': 100, 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1}),
    ('真我Neo8(12GB/512GB)', {'charging_wired': 100, 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1}),
    ('真我Neo8(16GB/1TB)', {'charging_wired': 120, 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1}),
    ('真我Neo8(16GB/512GB)', {'charging_wired': 120, 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1}),
]

for keyword, fields in realme_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'真我: {keyword}')

# ========== 三星 ==========
samsung_updates = [
    ('三星Galaxy S25 Ultra', {'charging_wireless': 1, 'camera_main': 20000, 'camera_front': 1200, 'telephoto_type': '光学变焦', 'has_ois': 1, 'image_brand': '三星'}),
    ('三星Galaxy A56', {'camera_main': 5000}),
    ('三星Galaxy S21 Ultra', {'camera_main': 10800}),
    ('三星Galaxy S24 Ultra(12GB', {'charging_wired': 45}),
    ('三星Galaxy S24(8GB', {'charging_wired': 25}),
    ('三星Galaxy S25 Ultra(12GB', {'charging_wired': 45}),
    ('三星Galaxy S25(12GB', {'charging_wired': 25}),
    ('三星Galaxy S26 Ultra', {'charging_wired': 45}),
    ('三星Galaxy S26+', {'charging_wired': 45}),
    ('三星Galaxy S26（12GB', {'charging_wired': 25}),
    ('三星Galaxy Z Flip7 FE', {'charging_wired': 25}),
    ('三星Galaxy Z Flip7（12GB', {'charging_wired': 25, 'camera_main': 5000}),
    ('三星Galaxy Z TriFold', {'camera_main': 20000}),
    ('三星W25', {'camera_main': 20000}),
]

for keyword, fields in samsung_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'三星: {keyword}')

# ========== vivo ==========
vivo_updates = [
    ('vivo X200', {'charging_wireless': 30}),
    ('iQOO 12', {'charging_wireless': 0}),
    ('iQOO 12 Pro', {'charging_wireless': 50}),
    ('vivo X300 Ultra(12GB/256GB)', {'charging_wireless': 40, 'camera_telephoto': 20000, 'camera_ultra': 5000, 'camera_main': 5000, 'camera_front': 3200}),
    ('vivo X300 Ultra(12GB/512GB)', {'charging_wireless': 40, 'camera_telephoto': 20000, 'camera_ultra': 5000, 'charging_wired': 90}),
    ('vivo X300 Ultra(16GB', {'charging_wireless': 40, 'camera_telephoto': 20000, 'camera_ultra': 5000, 'charging_wired': 90}),
    ('vivo X300(12GB/256GB)', {'charging_wireless': 40, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 90, 'camera_main': 5000, 'camera_front': 3200}),
    ('vivo Y600 Pro', {'charging_wireless': 0, 'camera_main': 5000, 'camera_front': 800}),
    ('vivo(S50', {'charging_wireless': 30, 'charging_wired': 90}),
]

for keyword, fields in vivo_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'vivo: {keyword}')

# ========== 一加 ==========
oneplus_updates = [
    ('一加13（12GB/256GB）', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 5000, 'charging_wired': 100, 'sensor_main': '索尼LYT808', 'camera_main': 5000, 'camera_front': 3200, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '哈苏'}),
    ('一加13T(12GB/256GB)', {'charging_wired': 80, 'camera_main': 5000, 'camera_front': 1600}),
    ('一加13T(12GB/512GB)', {'charging_wired': 80, 'camera_main': 5000, 'camera_front': 1600}),
    ('一加15T(12GB/256GB)', {'charging_wired': 100, 'camera_main': 5000, 'camera_front': 3200}),
    ('一加15（12GB/256GB）', {'charging_wired': 100, 'camera_main': 5000, 'camera_front': 3200}),
    ('一加Ace 3 Pro', {'charging_wired': 100}),
    ('一加Ace 5(12GB/256GB)', {'charging_wired': 100, 'camera_main': 5000, 'camera_front': 1600}),
    ('一加Ace 6(12GB/256GB)', {'charging_wired': 100, 'camera_main': 5000, 'camera_front': 1600}),
    ('一加Ace 5 至尊版', {'camera_main': 5000, 'camera_front': 1600}),
    ('一加Ace 6 至尊版', {'camera_main': 5000, 'camera_front': 3200}),
]

for keyword, fields in oneplus_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'一加: {keyword}')

# ========== 苹果 ==========
apple_updates = [
    ('iPhone Air 1TB', {'charging_wired': 20}),
    ('iPhone Air 256GB', {'camera_main': 4800, 'camera_front': 1200}),
    ('iPhone 14', {'camera_telephoto': 1200}),
    ('iPhone 15', {'camera_telephoto': 1200}),
    ('iPhone 16', {'camera_telephoto': 1200}),
    ('iPhone 16 Plus', {'camera_telephoto': 1200}),
    ('苹果 iPhone 17 Pro Max', {'charging_wired': 35, 'telephoto_type': '光学变焦', 'has_ois': 1, 'image_brand': 'Apple'}),
    ('苹果 iPhone 17', {'camera_main': 4800, 'camera_front': 1200, 'telephoto_type': '光学变焦', 'has_ois': 1, 'image_brand': 'Apple'}),
    ('苹果iPhone 17 Pro Max（1TB）', {'camera_main': 4800, 'camera_front': 1200, 'charging_wired': 35}),
    ('苹果iPhone 17 Pro Max（256GB）', {'camera_main': 4800, 'camera_front': 1200}),
    ('苹果iPhone 17 Pro Max（2TB）', {'camera_main': 4800, 'camera_front': 1200, 'charging_wired': 35}),
    ('苹果iPhone 17 Pro Max（512GB）', {'camera_main': 4800, 'camera_front': 1200, 'charging_wired': 35}),
    ('苹果iPhone 17 Pro（1TB）', {'camera_main': 4800, 'camera_front': 1200, 'charging_wired': 35}),
    ('苹果iPhone 17 Pro（256GB）', {'charging_wired': 35}),
    ('苹果iPhone 17 Pro（512GB）', {'camera_main': 4800, 'camera_front': 1200, 'charging_wired': 35}),
    ('苹果iPhone 17e', {'camera_main': 4800, 'camera_front': 1200, 'charging_wired': 20}),
    ('苹果iPhone 17（256GB）', {'charging_wired': 35}),
    ('苹果iPhone 17（512GB）', {'charging_wired': 35}),
    ('苹果iPhone SE 3', {'charging_wired': 20}),
]

for keyword, fields in apple_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'苹果: {keyword}')

# ========== 荣耀 ==========
honor_updates = [
    ('Magic V Flip', {'charging_wireless': 0, 'camera_telephoto': 0}),
    ('荣耀 500 Pro', {'charging_wireless': 50, 'camera_telephoto': 5000, 'camera_ultra': 1200, 'camera_main': 20000, 'camera_front': 5000, 'telephoto_type': '潜望式', 'has_ois': 1, 'image_brand': '荣耀'}),
    ('荣耀500 Pro(12GB', {'charging_wired': 80}),
    ('荣耀X50', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800}),
    ('荣耀X60 Pro', {'charging_wireless': 0, 'camera_telephoto': 0, 'camera_ultra': 800}),
]

for keyword, fields in honor_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'荣耀: {keyword}')

# ========== 魅族 ==========
meizu_updates = [
    ('魅族21', {'charging_wireless': 0, 'camera_telephoto': 5000}),
    ('魅族21 Note(16GB/256GB)', {'charging_wired': 66}),
    ('魅族21 Note(16GB/512GB)', {'charging_wired': 66}),
    ('魅族21 Pro(12GB', {'charging_wired': 80}),
    ('魅族21 Pro(16GB', {'charging_wired': 80}),
    ('魅族21(12GB/512GB)', {'charging_wired': 80}),
    ('魅族21(8GB/256GB)', {'charging_wired': 80}),
    ('魅族22（12GB/256GB）', {'charging_wired': 80}),
    ('魅族22（12GB/512GB）', {'charging_wired': 80}),
    ('魅族22（16GB+1TB）', {'charging_wired': 80}),
    ('魅族22（16GB+512GB）', {'charging_wired': 80}),
]

for keyword, fields in meizu_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'魅族: {keyword}')

# ========== 联想 ==========
lenovo_updates = [
    ('Moto Edge S Pro', {'camera_main': 10000}),
    ('Moto Edge S30', {'camera_main': 10000}),
    ('moto S50 Neo', {'charging_wired': 68}),
]

for keyword, fields in lenovo_updates:
    if update_phone(keyword, fields):
        updated += 1
    else:
        not_found.append(f'联想: {keyword}')

conn.commit()

print(f'已更新: {updated}条记录')
if not_found:
    print(f'\n未找到的型号 ({len(not_found)}条):')
    for m in not_found:
        print(f'  {m}')

conn.close()

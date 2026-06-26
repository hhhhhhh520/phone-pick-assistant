import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 获取所有型号
cursor.execute('SELECT id, brand, model FROM phones')
all_phones = cursor.fetchall()

def find_models(keyword):
    """模糊查找型号"""
    return [(id, brand, model) for id, brand, model in all_phones if keyword in model]

def update_field(ids, field, value):
    """批量更新字段"""
    for id in ids:
        cursor.execute(f'UPDATE phones SET {field} = ? WHERE id = ?', (value, id))
    return len(ids)

updated_count = {'wireless': 0, 'image_brand': 0, 'camera_main': 0, 'camera_front': 0, 'charging_wired': 0}

# ========== 小米/Redmi ==========
# 无线充电支持
xiaomi_wireless = ['小米15', '小米14', '小米13', 'MIX Fold 4', 'Redmi K80 Pro', 'Redmi K60 Pro']
for kw in xiaomi_wireless:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 50)

# Redmi Note系列不支持无线充电
redmi_no_wireless = find_models('Redmi Note')
if redmi_no_wireless:
    ids = [m[0] for m in redmi_no_wireless]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# 小米徕卡联名
xiaomi_leica = ['小米15', '小米14', '小米13 Ultra', 'MIX Fold 4', 'MIX Flip']
for kw in xiaomi_leica:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['image_brand'] += update_field(ids, 'image_brand', '徕卡')

# ========== vivo/iQOO ==========
# vivo X系列蔡司联名
vivo_zeiss = find_models('vivo X')
if vivo_zeiss:
    ids = [m[0] for m in vivo_zeiss]
    updated_count['image_brand'] += update_field(ids, 'image_brand', '蔡司')

# vivo X系列无线充电
vivo_x_high = ['vivo X100', 'vivo X200', 'vivo X300']
for kw in vivo_x_high:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 30)

# iQOO不支持无线充电
iqoo_models = find_models('iQOO')
if iqoo_models:
    ids = [m[0] for m in iqoo_models if 'Pro' not in m[2]]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 真我 ==========
# GT8系列理光GR联名
gt8_models = find_models('真我GT8')
if gt8_models:
    ids = [m[0] for m in gt8_models]
    updated_count['image_brand'] += update_field(ids, 'image_brand', '理光GR')

# GT5 Pro/GT7 Pro无线充电
gt_pro = ['真我GT5 Pro', '真我GT7 Pro']
for kw in gt_pro:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 50)

# 真我Neo/Q系列不支持无线充电
realme_no_wireless = ['真我Neo', '真我Q', '真我GT Neo']
for kw in realme_no_wireless:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 华为 ==========
# Mate/Pura系列XMAGE
huawei_xmage = ['Mate 60', 'Mate 70', 'Mate 80', 'Pura 70', 'Pura 80', 'Pura 90', 'Pura X']
for kw in huawei_xmage:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['image_brand'] += update_field(ids, 'image_brand', 'XMAGE')

# Mate/Pura无线充电
huawei_wireless = ['Mate 60', 'Mate 70', 'Mate 80', 'Pura 70', 'Pura 80', 'Pura 90', 'Pura X', 'Mate X']
for kw in huawei_wireless:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 50)

# 畅享系列不支持无线充电
changxiang = find_models('畅享')
if changxiang:
    ids = [m[0] for m in changxiang]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 苹果 ==========
# iPhone 11及以后支持无线充电
iphone_wireless = ['iPhone 11', 'iPhone 12', 'iPhone 13', 'iPhone 14', 'iPhone 15', 'iPhone 16', 'iPhone 17']
for kw in iphone_wireless:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 15)

# iPhone SE不支持无线充电
iphone_se = find_models('iPhone SE')
if iphone_se:
    ids = [m[0] for m in iphone_se]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 一加 ==========
# 一加数字系列哈苏联名
oneplus_hasu = ['一加13', '一加12', '一加11', '一加15']
for kw in oneplus_hasu:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['image_brand'] += update_field(ids, 'image_brand', '哈苏')

# 一加数字系列无线充电
oneplus_wireless = ['一加13', '一加12', '一加15']
for kw in oneplus_wireless:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 50)

# 一加Ace不支持无线充电
oneplus_ace = find_models('一加Ace')
if oneplus_ace:
    ids = [m[0] for m in oneplus_ace]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 三星 ==========
# S系列/Ultra无线充电
samsung_wireless = ['Galaxy S', 'Galaxy Z Fold', 'Galaxy Z Flip', 'Galaxy W']
for kw in samsung_wireless:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 15)

# A系列不支持无线充电
samsung_a = find_models('Galaxy A')
if samsung_a:
    ids = [m[0] for m in samsung_a]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 游戏手机 ==========
# ROG、黑鲨、红魔不支持无线充电
gaming_phones = ['ROG', '黑鲨', '红魔', '努比亚红魔']
for kw in gaming_phones:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 荣耀 ==========
# Magic系列无线充电
honor_magic = find_models('Magic')
if honor_magic:
    ids = [m[0] for m in honor_magic]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 50)

# 荣耀X系列不支持无线充电
honor_x = find_models('荣耀X')
if honor_x:
    ids = [m[0] for m in honor_x]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 魅族 ==========
# 魅族Pro版无线充电
meizu_pro = find_models('魅族21 Pro')
if meizu_pro:
    ids = [m[0] for m in meizu_pro]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 50)

# 魅族标准版不支持无线充电
meizu_std = ['魅族21 ', '魅族22', '魅族Note']
for kw in meizu_std:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

# ========== 索尼 ==========
# Xperia无线充电
sony_xperia = find_models('Xperia')
if sony_xperia:
    ids = [m[0] for m in sony_xperia]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 15)

# ========== 联想Moto ==========
# razr无线充电
moto_razr = find_models('razr')
if moto_razr:
    ids = [m[0] for m in moto_razr]
    updated_count['wireless'] += update_field(ids, 'charging_wireless', 15)

# Moto g/edge不支持无线充电
moto_no_wireless = ['Moto g', 'Moto edge']
for kw in moto_no_wireless:
    models = find_models(kw)
    if models:
        ids = [m[0] for m in models]
        updated_count['wireless'] += update_field(ids, 'charging_wireless', 0)

conn.commit()

print('数据补充完成:')
print(f'- 无线充电补充: {updated_count["wireless"]}条')
print(f'- 影像品牌补充: {updated_count["image_brand"]}条')

# 验证
cursor.execute('SELECT COUNT(*) FROM phones WHERE charging_wireless IS NOT NULL AND charging_wireless != ""')
wireless_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM phones WHERE image_brand IS NOT NULL AND image_brand != ""')
brand_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]

print(f'\n当前完整性:')
print(f'- 无线充电: {wireless_count}/{total} ({wireless_count/total*100:.1f}%)')
print(f'- 影像品牌: {brand_count}/{total} ({brand_count/total*100:.1f}%)')

conn.close()

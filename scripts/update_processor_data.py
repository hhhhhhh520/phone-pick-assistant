import sqlite3
import shutil

# 备份数据库
shutil.copy('backend/data/phones.db', 'backend/data/phones_backup_processor_update.db')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 处理器数据映射 (brand, model, processor, correct_brand)
processor_updates = [
    # OPPO
    ('OPPO', 'OPPO A32', '高通 骁龙460', None),
    ('OPPO', 'OPPO Find X7 Pro', '高通 骁龙8 Gen 3', None),
    ('OPPO', 'OPPO Find X9', '联发科 天玑9500', None),

    # ROG (正确的)
    ('ROG', 'ROG 8', '高通 骁龙8 Gen 3', None),
    ('ROG', 'ROG 8 Pro', '高通 骁龙8 Gen 3', None),
    ('ROG', 'ROG 8骁龙8Gen3', '高通 骁龙8 Gen 3', None),
    ('ROG', 'ROG 游戏手机9', '高通 骁龙8 Gen 3', None),
    ('ROG', 'ROG 游戏手机9 Pro', '高通 骁龙8 Gen 3', None),

    # ROG 下品牌错误的 - 华为
    ('ROG', '华为 Pura 90 Pro', '麒麟9020', '华为'),
    ('ROG', '华为 畅享90 Pro Max 128GB', '麒麟8000', '华为'),

    # ROG 下品牌错误的 - 苹果
    ('ROG', '苹果 iPhone 17', '苹果 A19', '苹果'),
    ('ROG', '苹果 iPhone 17 Pro Max', '苹果 A19 Pro', '苹果'),

    # iQOO
    ('iQOO', 'iQOO 12', '高通 骁龙8 Gen 3', None),
    ('iQOO', 'iQOO 12 Pro', '高通 骁龙8 Gen 3', None),
    ('iQOO', 'iQOO 13', '高通 骁龙8 至尊版', None),
    ('iQOO', 'iQOO 15', '高通 骁龙8 至尊版', None),
    ('iQOO', 'iQOO 15 Ultra', '高通 骁龙8 至尊版', None),

    # vivo
    ('vivo', 'vivo S50', '高通 骁龙8s Gen 3', None),
    ('vivo', 'vivo X Fold5', '高通 骁龙8 Gen 3', None),
    ('vivo', 'vivo X300', '联发科 天玑9500', None),
    ('vivo', 'vivo X300 Pro', '联发科 天玑9500', None),
    ('vivo', 'vivo Y300', '联发科 天玑6300', None),
    ('vivo', 'vivo Y300 Pro', '联发科 天玑6300', None),
    ('vivo', 'vivo Y300 Pro+', '联发科 天玑6300', None),
    ('vivo', 'vivo Y300t', '联发科 天玑6300', None),
    ('vivo', 'vivo Y500', '联发科 天玑7300', None),
    ('vivo', 'vivo Y500 Pro', '联发科 天玑7300', None),

    # 一加下品牌错误的
    ('一加', 'OPPO Find X9 Ultra', '联发科 天玑9500', 'OPPO'),

    # 一加正确的
    ('一加', '一加12', '高通 骁龙8 Gen 3', None),
    ('一加', '一加13', '高通 骁龙8 至尊版', None),
    ('一加', '一加13T', '高通 骁龙8 至尊版', None),
    ('一加', '一加Ace 2', '高通 骁龙8+ Gen 1', None),

    # 三星
    ('三星', '三星Galaxy A54', '三星 Exynos 1380', None),
    ('三星', '三星Galaxy A56', '三星 Exynos 1580', None),
    ('三星', '三星Galaxy S23', '高通 骁龙8 Gen 2', None),
    ('三星', '三星Galaxy S23 Ultra', '高通 骁龙8 Gen 2', None),
    ('三星', '三星Galaxy S24', '高通 骁龙8 Gen 3', None),
    ('三星', '三星Galaxy S24 Ultra', '高通 骁龙8 Gen 3', None),
    ('三星', '三星Galaxy S25', '高通 骁龙8 至尊版', None),
    ('三星', '三星Galaxy S25 Ultra', '高通 骁龙8 至尊版', None),
    ('三星', '三星Galaxy S26', '高通 骁龙8 至尊版', None),
    ('三星', '三星Galaxy S26 Ultra', '高通 骁龙8 至尊版', None),
    ('三星', '三星Galaxy S26+', '高通 骁龙8 至尊版', None),
    ('三星', '三星Galaxy Z Flip7 Al', '高通 骁龙8 至尊版', None),
    ('三星', '三星Galaxy Z Flip7 FE', '高通 骁龙8 至尊版', None),
    ('三星', '三星Galaxy Z Fold5', '高通 骁龙8 Gen 2', None),
    ('三星', '三星Galaxy Z Fold6 AI', '高通 骁龙8 Gen 3', None),
    ('三星', '三星Galaxy Z Fold7', '高通 骁龙8 至尊版', None),

    # 努比亚
    ('努比亚', '努比亚Z50 Ultra', '高通 骁龙8 Gen 2', None),
    ('努比亚', '努比亚Z60 Ultra', '高通 骁龙8 Gen 3', None),
    ('努比亚', '努比亚Z70 Ultra', '高通 骁龙8 至尊版', None),
    ('努比亚', '努比亚Z70S Ultra 摄影师版', '高通 骁龙8 至尊版', None),
    ('努比亚', '努比亚Z80 Ultra', '高通 骁龙8 至尊版', None),
    ('努比亚', '努比亚小牛', '高通 骁龙6 Gen 4', None),
    ('努比亚', '努比亚红魔10 Pro+骁龙8至尊版', '高通 骁龙8 至尊版', None),
    ('努比亚', '努比亚红魔10 Pro骁龙8至尊版', '高通 骁龙8 至尊版', None),
    ('努比亚', '努比亚红魔9 Pro', '高通 骁龙8 Gen 3', None),
    ('努比亚', '红魔10 Pro+', '高通 骁龙8 至尊版', None),

    # 华为
    ('华为', 'HUAWEI Mate 70', '麒麟9010', None),
    ('华为', 'HUAWEI Mate 70 Pro', '麒麟9020', None),
    ('华为', 'HUAWEI Mate 70 Pro+', '麒麟9020', None),
    ('华为', 'HUAWEI Pura 70', '麒麟9000S1', None),
    ('华为', 'HUAWEI Pura 70 Pro', '麒麟9010', None),
    ('华为', 'HUAWEI Pura X', '麒麟9010', None),
    ('华为', '华为Mate X5', '麒麟9000S', None),
    ('华为', '华为Mate X7', '麒麟9020', None),
    ('华为', '华为Mate XTs 非凡大师', '麒麟9020', None),
    ('华为', '华为Mate30', '麒麟990', None),
    ('华为', '华为Mate30 Pro', '麒麟990', None),
    ('华为', '华为Pura 80', '麒麟9010S', None),
    ('华为', '华为Pura 80 Pro', '麒麟9020', None),
    ('华为', '华为Pura 80 Ultra', '麒麟9020', None),
    ('华为', '华为nova 14', '麒麟8000', None),
    ('华为', '华为nova 14 Pro', '麒麟8020', None),
    ('华为', '华为nova 14 Ultra', '麒麟8020', None),
    ('华为', '华为畅享 70X', '麒麟8000', None),
    ('华为', '华为畅享 80', '麒麟8000A', None),
    ('华为', '华为畅享 90 128GB', '麒麟8000A', None),
    ('华为', '华为畅享90 Plus 128GB', '麒麟8000', None),

    # 小米
    ('小米', '小米10', '高通 骁龙865', None),
    ('小米', '小米17 Pro', '高通 骁龙8 至尊版', None),
    ('小米', '小米MIX 4', '高通 骁龙888+', None),

    # 真我下品牌错误的 - 红米
    ('真我', 'Redmi K90 Pro Max', None, '红米'),
    ('真我', 'Redmi Turbo 5 MAX', None, '红米'),

    # 真我正确的
    ('真我', '真我15 Pro', '高通 骁龙7 Gen 4', None),
    ('真我', '真我15T', '高通 骁龙7 Gen 4', None),
    ('真我', '真我GT Neo2', '高通 骁龙870', None),
    ('真我', '真我GT Neo5 150W', '高通 骁龙8+ Gen 1', None),
    ('真我', '真我GT Neo5 SE', '高通 骁龙7+ Gen 2', None),
    ('真我', '真我GT 大师探索版', '高通 骁龙870', None),
    ('真我', '真我GT5 150W', '高通 骁龙8 Gen 2', None),
    ('真我', '真我GT5 Pro', '高通 骁龙8 Gen 3', None),
    ('真我', '真我GT6', '高通 骁龙8 Gen 3', None),
    ('真我', '真我GT7', '联发科 天玑9400+', None),
    ('真我', '真我GT7 Pro', '联发科 天玑9400+', None),
    ('真我', '真我Neo7', '高通 骁龙6 Gen 4', None),
    ('真我', '真我Neo7 SE', '高通 骁龙6 Gen 4', None),
    ('真我', '真我Neo7 Turbo', '高通 骁龙7 Gen 3', None),

    # 索尼下品牌错误的
    ('索尼', 'HUAWEI Pura X', '麒麟9010', '华为'),
    ('索尼', 'iPhone 17 Pro', '苹果 A19 Pro', '苹果'),
    ('索尼', 'iPhone Air 1TB', '苹果 A19 Pro', '苹果'),

    # 索尼正确的
    ('索尼', '索尼Xperia 1 IV', '高通 骁龙8 Gen 1', None),
    ('索尼', '索尼Xperia 10 III高通骁龙690', '高通 骁龙690', None),
    ('索尼', '索尼Xperia 10 IV', '高通 骁龙695', None),
    ('索尼', '索尼Xperia 5 III高通骁龙888', '高通 骁龙888', None),
    ('索尼', '索尼Xperia PRO-I高通骁龙888', '高通 骁龙888', None),
    ('索尼', '索尼移动Xperia 1 V', '高通 骁龙8 Gen 2', None),
    ('索尼', '索尼移动Xperia 1 VII', '高通 骁龙8 至尊版', None),
    ('索尼', '索尼移动Xperia 5 V', '高通 骁龙8 Gen 2', None),
    ('索尼', '索尼移动Xperia 5 Ⅳ 骁龙8 Gen1', '高通 骁龙8 Gen 1', None),
    ('索尼', '荣耀 500 Pro', None, '荣耀'),

    # 红米
    ('红米', 'Redmi  K80至尊版', '联发科 天玑9400+', None),
    ('红米', 'Redmi  Note 14', '联发科 Helio G99-Ultra', None),
    ('红米', 'Redmi  Note 14 Pro', '高通 骁龙7s Gen 2', None),
    ('红米', 'Redmi K70', '高通 骁龙8 Gen 2', None),
    ('红米', 'Redmi K80', '高通 骁龙8 Gen 3', None),
    ('红米', 'Redmi K80 Pro', '高通 骁龙8 Gen 3', None),
    ('红米', 'Redmi Note 13 Pro', '高通 骁龙7s Gen 2', None),
    ('红米', 'Redmi Turbo 4天玑 8400-Ultra', '联发科 天玑8400-Ultra', None),

    # 联想
    ('联想', 'Moto Edge S Pro高通骁龙870处理器', '高通 骁龙870', None),
    ('联想', 'Moto Edge S30骁龙888 Plus处理器', '高通 骁龙888+', None),
    ('联想', 'Moto Razr 50', '联发科 天玑7300X', None),
    ('联想', 'Moto S50 7300', '联发科 天玑7300', None),
    ('联想', 'Moto edge s骁龙870', '高通 骁龙870', None),
    ('联想', 'Moto g100', '高通 骁龙870', None),
    ('联想', 'Moto g100 Pro', '高通 骁龙870', None),
    ('联想', 'Moto g100s', '高通 骁龙870', None),
    ('联想', 'Moto g54', '联发科 天玑7020', None),
    ('联想', 'Moto g75', '高通 骁龙6 Gen 3', None),
    ('联想', 'Moto razr 50 Ultra', '高通 骁龙8s Gen 3', None),
    ('联想', 'Moto razr 60 12GB+512GB60万次折叠认证', '联发科 天玑7300X', None),
    ('联想', 'Moto razr 60 8GB+256GB60万次折叠认证', '联发科 天玑7300X', None),
    ('联想', 'Moto razr 60 Ultra', '高通 骁龙8s Gen 3', None),
    ('联想', 'moto S50 Neo', '高通 骁龙6s Gen 3', None),

    # 苹果
    ('苹果', 'iPhone XR', '苹果 A12', None),
    ('苹果', '苹果iPhone 16e', '苹果 A18', None),
    ('苹果', '苹果iPhone 17 Pro', '苹果 A19 Pro', None),
    ('苹果', '苹果iPhone 17 Pro Max', '苹果 A19 Pro', None),
    ('苹果', '苹果iPhone 17e', '苹果 A19', None),

    # 荣耀下品牌错误的
    ('荣耀', 'Neo7x', '高通 骁龙6 Gen 4', None),
    ('荣耀', '真我15', '高通 骁龙7 Gen 4', '真我'),
    ('荣耀', '真我GT7', '联发科 天玑9400+', '真我'),
    ('荣耀', '真我Q3', '高通 骁龙750G', '真我'),

    # 黑鲨下品牌错误的
    ('黑鲨', '小米MIX FOLD 4', '高通 骁龙8 Gen 3', '小米'),
    ('黑鲨', '红米note14', '联发科 Helio G99-Ultra', '红米'),
]

# 统计
updated_processor = 0
updated_brand = 0
not_found = []

for brand, model, processor, correct_brand in processor_updates:
    # 先查找记录
    cursor.execute('SELECT id FROM phones WHERE brand = ? AND model = ?', (brand, model))
    result = cursor.fetchone()

    if result:
        phone_id = result[0]

        # 更新处理器
        if processor:
            cursor.execute('UPDATE phones SET processor = ? WHERE id = ?', (processor, phone_id))
            updated_processor += 1

        # 更新品牌
        if correct_brand:
            cursor.execute('UPDATE phones SET brand = ? WHERE id = ?', (correct_brand, phone_id))
            updated_brand += 1
            print(f'品牌修正: {brand} -> {correct_brand} | {model}')
    else:
        not_found.append(f'{brand} | {model}')

conn.commit()

print(f'\n=== 更新统计 ===')
print(f'处理器更新: {updated_processor}条')
print(f'品牌修正: {updated_brand}条')
print(f'未找到记录: {len(not_found)}条')

if not_found:
    print('\n未找到的记录:')
    for item in not_found[:20]:
        print(f'  {item}')
    if len(not_found) > 20:
        print(f'  ... 还有 {len(not_found)-20} 条')

# 验证处理器覆盖率
cursor.execute('SELECT COUNT(*) FROM phones WHERE processor IS NOT NULL AND processor != ""')
valid = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]
print(f'\n处理器覆盖率: {valid}/{total} ({valid/total*100:.1f}%)')

conn.close()

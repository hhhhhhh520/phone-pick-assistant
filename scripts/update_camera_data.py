import sqlite3
import shutil

# 备份数据库
shutil.copy('backend/data/phones.db', 'backend/data/phones_backup_camera_update.db')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 主摄数据映射 (brand, model, camera_main)
# 格式：纯数字万像素
camera_updates = [
    # OPPO
    ('OPPO', 'OPPO A32', '1300'),
    ('OPPO', 'OPPO Find N5', '5000'),
    ('OPPO', 'OPPO Find X6', '5000'),
    ('OPPO', 'OPPO Find X6 Pro', '5000'),
    ('OPPO', 'OPPO Find X7', '5000'),
    ('OPPO', 'OPPO Find X7 Pro', '5000'),
    ('OPPO', 'OPPO Find X7 Ultra', '5000'),
    ('OPPO', 'OPPO Find X8', '5000'),
    ('OPPO', 'OPPO Find X8 Pro', '5000'),
    ('OPPO', 'OPPO Find X9', '5000'),
    ('OPPO', 'OPPO Find X9 Pro', '5000'),
    ('OPPO', 'OPPO K11', '5000'),
    ('OPPO', 'OPPO K12', '5000'),
    ('OPPO', 'OPPO Reno 12', '5000'),
    ('OPPO', 'OPPO Reno 13', '5000'),
    ('OPPO', 'OPPO Reno14', '5000'),
    ('OPPO', 'OPPO Reno14 Pro', '5000'),
    ('OPPO', 'OPPO Reno15', '5000'),
    ('OPPO', 'OPPO Reno15 Pro', '5000'),
    ('OPPO', 'OPPO Reno8', '5000'),

    # ROG
    ('ROG', '5s Pro', '6400'),
    ('ROG', '6天玑9000+', '5000'),
    ('ROG', '6矩阵式液冷', '5000'),
    ('ROG', 'ROG 8', '5000'),
    ('ROG', 'ROG 8 Pro', '5000'),
    ('ROG', 'ROG 8骁龙8Gen3', '5000'),
    ('ROG', 'ROG 游戏手机9', '5000'),
    ('ROG', 'ROG 游戏手机9 Pro', '5000'),
    ('ROG', '苹果 iPhone 17', '4800'),
    ('ROG', '苹果 iPhone 17 Pro Max', '4800'),

    # iQOO
    ('iQOO', 'iQOO 12', '5000'),
    ('iQOO', 'iQOO 12 Pro', '5000'),
    ('iQOO', 'iQOO 13', '5000'),
    ('iQOO', 'iQOO 15', '5000'),
    ('iQOO', 'iQOO 15 Ultra', '5000'),
    ('iQOO', 'iQOO Neo10', '5000'),
    ('iQOO', 'iQOO Neo11', '5000'),
    ('iQOO', 'iQOO Neo9 8', '5000'),
    ('iQOO', 'iQOO Z10 Turbo', '5000'),
    ('iQOO', 'iQOO Z10 Turbo Pro', '5000'),
    ('iQOO', 'iQOO Z10 Turbo+', '5000'),
    ('iQOO', 'iQOO Z10x', '5000'),
    ('iQOO', 'iQOO Z11', '5000'),
    ('iQOO', 'iQOO Z11 Turbo', '5000'),
    ('iQOO', 'iQOO Z11x', '5000'),
    ('iQOO', 'iQOO Z9', '5000'),
    ('iQOO', 'iQOO Z9 Turbo', '5000'),

    # vivo
    ('vivo', 'iQOO 15 Ultra', '5000'),
    ('vivo', 'iQOO Z', '5000'),
    ('vivo', 'iQOO Z10 Turbo', '5000'),
    ('vivo', 'iQOO Z9 Turbo', '5000'),
    ('vivo', 'vivo S18', '5000'),
    ('vivo', 'vivo S19', '5000'),
    ('vivo', 'vivo S20', '5000'),
    ('vivo', 'vivo S30', '5000'),
    ('vivo', 'vivo S30 Pro mini', '5000'),
    ('vivo', 'vivo S50', '5000'),
    ('vivo', 'vivo S50 Pro mini', '5000'),
    ('vivo', 'vivo X Fold3 Pro', '5000'),
    ('vivo', 'vivo X100', '5000'),
    ('vivo', 'vivo X100 Pro', '5000'),
    ('vivo', 'vivo X100 Ultra', '5000'),
    ('vivo', 'vivo X100s', '5000'),
    ('vivo', 'vivo X200', '5000'),
    ('vivo', 'vivo X200 Pro', '5000'),
    ('vivo', 'vivo X200 Pro mini', '5000'),
    ('vivo', 'vivo X200 Ultra', '5000'),
    ('vivo', 'vivo X200s', '5000'),
    ('vivo', 'vivo X300', '5000'),
    ('vivo', 'vivo X300 Pro', '5000'),
    ('vivo', 'vivo X300 Ultra', '5000'),
    ('vivo', 'vivo X300s', '5000'),
    ('vivo', 'vivo Y200i', '5000'),
    ('vivo', 'vivo Y300', '5000'),
    ('vivo', 'vivo Y300 Pro', '5000'),
    ('vivo', 'vivo Y300 Pro+', '5000'),
    ('vivo', 'vivo Y300t', '5000'),
    ('vivo', 'vivo Y500', '5000'),
    ('vivo', 'vivo Y500 Pro', '5000'),
    ('vivo', 'vivo Y600 Pro', '5000'),

    # 一加
    ('一加', '12哈苏全焦段超光影', '5000'),
    ('一加', 'iQOO Z11 Turbo', '5000'),
    ('一加', '一加12', '5000'),
    ('一加', '一加13', '5000'),
    ('一加', '一加13T', '5000'),
    ('一加', '一加15', '5000'),
    ('一加', '一加15T', '5000'),
    ('一加', '一加Ace 2', '5000'),
    ('一加', '一加Ace 3', '5000'),
    ('一加', '一加Ace 3 Pro 8', '5000'),
    ('一加', '一加Ace 5 8', '5000'),
    ('一加', '一加Ace 5 至尊版', '5000'),
    ('一加', '一加Ace 6', '5000'),
    ('一加', '一加Ace 6 至尊版', '5000'),
    ('一加', '一加Ace 6T', '5000'),

    # 三星
    ('三星', 'Galaxy S', '5000'),
    ('三星', 'Galaxy S24 Ultra', '20000'),
    ('三星', 'Galaxy S25 Ultra', '20000'),
    ('三星', 'Galaxy Z Fold', '5000'),
    ('三星', '三星Galaxy A54', '5000'),
    ('三星', '三星Galaxy A56', '5000'),
    ('三星', '三星Galaxy S23', '5000'),
    ('三星', '三星Galaxy S23 Ultra', '20000'),
    ('三星', '三星Galaxy S24', '5000'),
    ('三星', '三星Galaxy S26', '5000'),
    ('三星', '三星Galaxy S26 Ultra', '20000'),
    ('三星', '三星Galaxy S26+', '5000'),
    ('三星', '三星Galaxy Z Flip5 骁龙8 Gen2 CPU核心数:八核 ROM容量:256GB 电池容量:3700mAh 后置摄像头1 后置摄像头:1200万像素 有线充电:25w 前置摄像头1 前置摄像头:1000万像素', '1200'),
    ('三星', '三星Galaxy Z Fold5', '5000'),
    ('三星', '三星Galaxy Z Fold6 AI', '5000'),
    ('三星', '三星Galaxy Z Fold7', '5000'),

    # 努比亚
    ('努比亚', 'Z60 Ultra', '5000'),
    ('努比亚', 'Z70 Ultra', '5000'),
    ('努比亚', '努比亚Z50 Ultra', '6400'),
    ('努比亚', '努比亚Z60 Ultra', '5000'),
    ('努比亚', '努比亚Z70 Ultra', '5000'),
    ('努比亚', '努比亚Z70S Ultra 摄影师版', '5000'),
    ('努比亚', '努比亚小牛', '10800'),
    ('努比亚', '努比亚红魔10 Pro+骁龙8至尊版', '5000'),
    ('努比亚', '努比亚红魔10 Pro骁龙8至尊版', '5000'),
    ('努比亚', '努比亚红魔10S Pro+ 16GB+512GB骁龙8至尊领先版', '5000'),
    ('努比亚', '努比亚红魔9 Pro', '5000'),
    ('努比亚', '红魔10 Pro+', '5000'),

    # 华为
    ('华为', 'HUAWEI Mate 60', '5000'),
    ('华为', 'HUAWEI Mate 60 Pro', '5000'),
    ('华为', 'HUAWEI Mate 70', '5000'),
    ('华为', 'HUAWEI Mate 70 Pro', '5000'),
    ('华为', 'HUAWEI Mate 70 Pro+', '5000'),
    ('华为', 'HUAWEI Mate 80', '5000'),
    ('华为', 'HUAWEI Mate 80 Pro Max', '5000'),
    ('华为', 'HUAWEI Mate 80 Pro Max 风驰版', '5000'),
    ('华为', 'HUAWEI Pura 70', '5000'),
    ('华为', 'HUAWEI Pura 70 Pro', '5000'),
    ('华为', '华为Mate 70 Air', '5000'),
    ('华为', '华为Mate X5', '5000'),
    ('华为', '华为Mate30', '4000'),
    ('华为', '华为Mate30 Pro', '4000'),
    ('华为', '华为Pura 80', '5000'),
    ('华为', '华为Pura 80 Pro', '5000'),
    ('华为', '华为Pura 80 Ultra', '5000'),
    ('华为', '华为Pura 90', '5000'),
    ('华为', '华为Pura 90 Pro', '5000'),
    ('华为', '华为Pura 90 Pro Max', '5000'),
    ('华为', '华为nova 14', '5000'),
    ('华为', '华为nova 14 Pro', '5000'),
    ('华为', '华为nova 14 Ultra', '5000'),
    ('华为', '华为nova 15', '5000'),
    ('华为', '华为nova 15 Pro', '5000'),
    ('华为', '华为nova 15 Ultra', '5000'),
    ('华为', '华为畅享 70X', '5000'),
    ('华为', '华为畅享 80', '5000'),
    ('华为', '华为畅享 90 128GB', '5000'),
    ('华为', '华为畅享 90 256GB', '5000'),
    ('华为', '华为畅享90 Plus 128GB', '5000'),
    ('华为', '华为畅享90 Pro Max 256GB', '5000'),
    ('华为', '华为畅享90 Pro Max 512GB', '5000'),

    # 小米
    ('小米', 'Redmi Note 15 Pro', '5000'),
    ('小米', 'Redmi Turbo', '5000'),
    ('小米', 'RedmiTurbo', '5000'),
    ('小米', '小米10', '10000'),
    ('小米', '小米10S', '10000'),
    ('小米', '小米11', '10000'),
    ('小米', '小米11 Pro', '5000'),
    ('小米', '小米11 Ultra', '5000'),
    ('小米', '小米11青春版', '6400'),
    ('小米', '小米12', '5000'),
    ('小米', '小米12 Pro', '5000'),
    ('小米', '小米12S', '5000'),
    ('小米', '小米12S Pro', '5000'),
    ('小米', '小米12S Ultra', '5000'),
    ('小米', '小米13', '5000'),
    ('小米', '小米13 Pro', '5000'),
    ('小米', '小米13 Ultra', '5000'),
    ('小米', '小米14', '5000'),
    ('小米', '小米14 Pro', '5000'),
    ('小米', '小米14 Ultra', '5000'),
    ('小米', '小米15', '5000'),
    ('小米', '小米15 Pro', '5000'),
    ('小米', '小米15 Pro16GB/1TB)', '5000'),
    ('小米', '小米15 Ultra', '5000'),
    ('小米', '小米15S Pro', '5000'),
    ('小米', '小米17', '5000'),
    ('小米', '小米17 Pro', '5000'),
    ('小米', '小米17 Pro Max', '5000'),
    ('小米', '小米17 Ultra', '5000'),
    ('小米', '小米Civi 3', '5000'),
    ('小米', '小米Civi 4 Pro', '5000'),
    ('小米', '小米Civi 5 Pro', '5000'),
    ('小米', '小米MIX 4', '10000'),
    ('小米', '小米MIX Flip', '5000'),
    ('小米', '小米MIX FOLD 4', '5000'),

    # 真我
    ('真我', 'GT5 Pro', '5000'),
    ('真我', 'Redmi K90 Pro Max', '5000'),
    ('真我', 'Redmi Turbo 5 MAX', '5000'),
    ('真我', '真我15 Pro', '5000'),
    ('真我', '真我15T', '5000'),
    ('真我', '真我GT Neo2', '6400'),
    ('真我', '真我GT Neo5 150W', '5000'),
    ('真我', '真我GT Neo5 SE', '6400'),
    ('真我', '真我GT 大师探索版', '5000'),
    ('真我', '真我GT5 150W', '5000'),
    ('真我', '真我GT5 Pro', '5000'),
    ('真我', '真我GT6', '5000'),
    ('真我', '真我GT7', '5000'),
    ('真我', '真我GT7 Pro', '5000'),
    ('真我', '真我GT8', '5000'),
    ('真我', '真我GT8 Pro', '5000'),
    ('真我', '真我Neo7', '5000'),
    ('真我', '真我Neo7 SE', '5000'),
    ('真我', '真我Neo7 Turbo', '5000'),
    ('真我', '真我Neo8', '5000'),

    # 索尼
    ('索尼', 'iPhone 17 Pro', '4800'),
    ('索尼', 'iPhone Air 1TB', '4800'),
    ('索尼', 'vivo X300 Ultra', '5000'),
    ('索尼', '一加Ace 6 至尊版', '5000'),
    ('索尼', '华为 Pura 90 Pro Max', '5000'),
    ('索尼', '索尼Xperia 1 IV', '1200'),
    ('索尼', '索尼Xperia 10 III高通骁龙690', '1200'),
    ('索尼', '索尼Xperia 10 IV', '1200'),
    ('索尼', '索尼Xperia 5 III高通骁龙888', '1200'),
    ('索尼', '索尼Xperia PRO-I高通骁龙888', '1200'),
    ('索尼', '索尼移动Xperia 1 V', '4800'),
    ('索尼', '索尼移动Xperia 5 V', '4800'),
    ('索尼', '索尼移动Xperia 5 Ⅳ 骁龙8 Gen1', '1200'),
    ('索尼', '索尼移动Xperia Pro-i IICPU型号:高通 骁龙8 Gen2 CPU核心数:八核 RAM容量:12GB ROM容量:512GB 电池容量:4500mAh 后置摄像头1 后置摄像头:1220万像素 有线充电:30w', '1200'),
    ('索尼', '荣耀 500 Pro', '20000'),

    # 红米
    ('红米', 'Redmi  K80至尊版', '5000'),
    ('红米', 'Redmi  Note 14', '5000'),
    ('红米', 'Redmi  Note 14 Pro', '5000'),
    ('红米', 'Redmi  Note 15', '5000'),
    ('红米', 'Redmi K70', '5000'),
    ('红米', 'Redmi K80', '5000'),
    ('红米', 'Redmi K80 Pro', '5000'),
    ('红米', 'Redmi K90', '5000'),
    ('红米', 'Redmi K90 Max', '5000'),
    ('红米', 'Redmi Note 13 Pro', '20000'),
    ('红米', 'Redmi Note 15 Pro', '5000'),
    ('红米', 'Redmi Note 15 Pro+', '5000'),
    ('红米', 'Redmi Turbo 4', '5000'),
    ('红米', 'Redmi Turbo 4 Pro 8s', '5000'),
    ('红米', 'Redmi Turbo 4天玑 8400-Ultra', '5000'),
    ('红米', 'Redmi Turbo 5', '5000'),

    # 联想
    ('联想', 'Moto Edge S Pro高通骁龙870处理器', '10800'),
    ('联想', 'Moto Edge S30骁龙888 Plus处理器', '10800'),
    ('联想', 'Moto Razr 50', '5000'),
    ('联想', 'Moto edge s骁龙870', '6400'),
    ('联想', 'Moto g100', '6400'),
    ('联想', 'Moto g100 Pro', '6400'),
    ('联想', 'Moto g100s', '6400'),
    ('联想', 'Moto g54', '5000'),
    ('联想', 'Moto g75', '5000'),
    ('联想', 'Moto razr 50 Ultra', '5000'),
    ('联想', 'Moto razr 60 12GB+512GB60万次折叠认证', '5000'),
    ('联想', 'Moto razr 60 8GB+256GB60万次折叠认证', '5000'),
    ('联想', 'Moto razr 60 Ultra', '5000'),
    ('联想', 'moto S50 Neo', '5000'),

    # 苹果
    ('苹果', 'iPhone Air 1TB', '4800'),
    ('苹果', 'iPhone Air 256GB', '4800'),
    ('苹果', 'iPhone XR', '1200'),
    ('苹果', '苹果iPhone 15', '4800'),
    ('苹果', '苹果iPhone 15 Plus', '4800'),
    ('苹果', '苹果iPhone 15 Pro', '4800'),
    ('苹果', '苹果iPhone 15 Pro Max', '4800'),
    ('苹果', '苹果iPhone 16', '4800'),
    ('苹果', '苹果iPhone 16 Plus', '4800'),
    ('苹果', '苹果iPhone 16 Pro', '4800'),
    ('苹果', '苹果iPhone 16 Pro Max', '4800'),
    ('苹果', '苹果iPhone 16e', '4800'),
    ('苹果', '苹果iPhone 17', '4800'),
    ('苹果', '苹果iPhone 17 Pro', '4800'),
    ('苹果', '苹果iPhone 17 Pro Max', '4800'),

    # 荣耀
    ('荣耀', '真我GT6', '5000'),
    ('荣耀', '真我GT7', '5000'),
    ('荣耀', '真我GT7 Pro', '5000'),
    ('荣耀', '真我GT7 Pro竞速版', '5000'),
    ('荣耀', '真我GT8', '5000'),
    ('荣耀', '真我Neo7', '5000'),
    ('荣耀', '真我Neo7 Turbo', '5000'),
    ('荣耀', '真我Neo8', '5000'),
    ('荣耀', '荣耀500 Pro', '20000'),

    # 魅族
    ('魅族', '17 Pro', '6400'),
    ('魅族', '17超线性扬声器', '6400'),
    ('魅族', '21 Note', '5000'),
    ('魅族', '21 Pro', '5000'),
    ('魅族', '魅族22', '5000'),

    # 黑鲨
    ('黑鲨', '4S Pro', '6400'),
    ('黑鲨', '4骁龙870', '4800'),
    ('黑鲨', '小米MIX FOLD 4', '5000'),
    ('黑鲨', '红米note14', '5000'),
]

# 统计
updated = 0
not_found = []

for brand, model, camera in camera_updates:
    cursor.execute('SELECT id FROM phones WHERE brand = ? AND model = ?', (brand, model))
    result = cursor.fetchone()

    if result:
        phone_id = result[0]
        cursor.execute('UPDATE phones SET camera_main = ? WHERE id = ?', (camera, phone_id))
        updated += 1
    else:
        not_found.append(f'{brand} | {model}')

conn.commit()

print(f'=== 更新统计 ===')
print(f'主摄更新: {updated}条')
print(f'未找到记录: {len(not_found)}条')

if not_found:
    print('\n未找到的记录 (前20条):')
    for item in not_found[:20]:
        print(f'  {item}')

# 验证主摄覆盖率
cursor.execute('SELECT COUNT(*) FROM phones WHERE camera_main IS NOT NULL AND camera_main != ""')
valid = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]
print(f'\n主摄覆盖率: {valid}/{total} ({valid/total*100:.1f}%)')

conn.close()

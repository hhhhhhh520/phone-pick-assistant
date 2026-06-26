import sqlite3
import shutil

# 备份数据库
shutil.copy('backend/data/phones.db', 'backend/data/phones_backup_deep_clean.db')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 1. 品牌归属错误修正
brand_corrections = [
    # ROG -> 华为
    ('ROG', '华为 Pura 90 Pro', '华为'),
    ('ROG', '华为 畅享90 Pro Max 128GB', '华为'),
    # ROG -> 苹果
    ('ROG', '苹果 iPhone 17', '苹果'),
    ('ROG', '苹果 iPhone 17 Pro Max', '苹果'),
    # 索尼 -> 各自品牌
    ('索尼', 'OPPO Find X9s Pro', 'OPPO'),
    ('索尼', 'vivo X300 Ultra', 'vivo'),
    ('索尼', '一加Ace 6 至尊版', '一加'),
    ('索尼', '华为 Pura 90 Pro Max', '华为'),
    ('索尼', '华为Pura 90 Pro Max', '华为'),
    ('索尼', '华为Pura X Max', '华为'),
    ('索尼', '华为novaFlip', '华为'),
    ('索尼', '华为畅享90 Pro Max 128GB', '华为'),
    ('索尼', '红米note', '红米'),
    # 荣耀 -> 真我
    ('荣耀', '真我12', '真我'),
    ('荣耀', '真我12x', '真我'),
    ('荣耀', '真我15T', '真我'),
    ('荣耀', '真我GT Neo', '真我'),
    ('荣耀', '真我GT Neo 闪速版', '真我'),
    ('荣耀', '真我GT Neo2T', '真我'),
    ('荣耀', '真我GT Neo6', '真我'),
    ('荣耀', '真我GT Neo6 SE', '真我'),
    ('荣耀', '真我GT2 Pro', '真我'),
    ('荣耀', '真我GT6', '真我'),
    ('荣耀', '真我GT7', '真我'),
    ('荣耀', '真我GT7 Pro', '真我'),
    ('荣耀', '真我GT7 Pro竞速版', '真我'),
    ('荣耀', '真我GT8', '真我'),
    ('荣耀', '真我Neo7', '真我'),
    ('荣耀', '真我Neo7 Turbo', '真我'),
    ('荣耀', '真我Neo8', '真我'),
    ('荣耀', '真我Q2', '真我'),
    ('荣耀', '真我Q3 Pro', '真我'),
    ('荣耀', '真我Q3s', '真我'),
    ('荣耀', '真我V11', '真我'),
    ('荣耀', '真我V15', '真我'),
    ('荣耀', '真我X7 Pro', '真我'),
    # 联想 -> 小米
    ('联想', '小米 17 Ultra', '小米'),
    # 真我 -> 红米
    ('真我', 'Redmi Turbo 5 MAX', '红米'),
    ('真我', 'Redmi K90 Pro Max', '红米'),
    # 黑鲨 -> 小米/红米
    ('黑鲨', '小米MIX FOLD 4', '小米'),
    ('黑鲨', '红米note14', '红米'),
    # 一加 -> iQOO
    ('一加', 'iQOO Z11 Turbo', 'iQOO'),
]

# 2. 需要删除的无效/虚构型号
invalid_models = [
    ('OPPO', 'OPPO K'),  # 只有单字母
    ('OPPO', 'OPPO A6 Pro'),  # 不存在
    ('OPPO', 'OPPO A6s Pro'),  # 不存在
    ('OPPO', 'OPPO K13 Turbo Pro'),  # 未发布
    ('OPPO', 'OPPO K13s'),  # 未发布
    ('OPPO', 'OPPO K15 Pro'),  # 未发布
    ('OPPO', 'OPPO K15 Pro+'),  # 未发布
    ('OPPO', 'OPPO Find X9s Pro'),  # 未发布
    ('努比亚', 'p 25000'),  # 乱码
    ('黑鲨', '4S 高达限定版CPU型号:'),  # 参数不完整
    ('苹果', 'iPhone'),  # 仅一个词
    ('vivo', 'vivo Y600 Pro'),  # 不存在
    ('华为', '华为畅享90 Pro Max 256GB'),  # 不存在
    ('华为', '华为畅享90 Pro Max 512GB'),  # 不存在
    ('华为', '华为畅享90 Plus 128GB'),  # 不存在
    ('华为', '华为Pura X Max'),  # 未发布
    ('华为', '华为Pura 90'),  # 未发布
    ('华为', '华为Pura 90 Pro'),  # 未发布
    ('华为', '华为Pura 90 Pro Max'),  # 未发布
]

# 3. 需要规范化名称的型号
name_corrections = [
    ('三星', 'Galaxy Z Flip7 FEAl大视野智能外屏', '三星Galaxy Z Flip7 FE'),
    ('三星', 'Galaxy Z Fold5闭合', '三星Galaxy Z Fold5'),
    ('三星', 'Galaxy Z TriFold多功能大', '三星Galaxy Z TriFold'),
    ('华为', 'Mate XTs 非凡', '华为Mate XTs 非凡大师'),
    ('黑鲨', '4骁龙870', '黑鲨4'),
    ('ROG', '6天玑9000+', 'ROG 6'),
    ('ROG', '6矩阵式液冷', 'ROG 6'),
]

# 执行品牌修正
brand_fixed = 0
for old_brand, model, new_brand in brand_corrections:
    cursor.execute('UPDATE phones SET brand = ? WHERE brand = ? AND model = ?', (new_brand, old_brand, model))
    brand_fixed += cursor.rowcount

print(f'品牌修正: {brand_fixed}条')

# 执行无效型号删除
deleted = 0
for brand, model in invalid_models:
    cursor.execute('DELETE FROM phones WHERE brand = ? AND model = ?', (brand, model))
    deleted += cursor.rowcount

print(f'删除无效型号: {deleted}条')

# 执行名称规范化
renamed = 0
for brand, old_name, new_name in name_corrections:
    cursor.execute('UPDATE phones SET model = ? WHERE brand = ? AND model = ?', (new_name, brand, old_name))
    renamed += cursor.rowcount

print(f'名称规范化: {renamed}条')

# 4. 删除重复记录（保留第一条）
cursor.execute('''
    DELETE FROM phones
    WHERE id NOT IN (
        SELECT MIN(id) FROM phones GROUP BY brand, model
    )
''')
duplicates_removed = cursor.rowcount
print(f'删除重复记录: {duplicates_removed}条')

conn.commit()

# 统计最终结果
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]
print(f'\n最终记录数: {total}条')

# 按品牌统计
cursor.execute('SELECT brand, COUNT(*) as cnt FROM phones GROUP BY brand ORDER BY cnt DESC')
brands = cursor.fetchall()
print('\n品牌分布:')
for brand, cnt in brands:
    print(f'  {brand}: {cnt}款')

conn.close()

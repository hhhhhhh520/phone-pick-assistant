# -*- coding: utf-8 -*-
import sqlite3
import shutil

# 备份数据库
shutil.copy('backend/data/phones.db', 'backend/data/phones_backup_merge_supplement.db')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

print("=" * 60)
print("数据合并与补充")
print("=" * 60)

# ============================================
# 第一部分：删除重复机型（保留信息更完整的版本）
# ============================================
print("\n【一、删除重复机型】")

# (品牌, 要删除的型号, 原因)
duplicates_to_delete = [
    # 小米
    ('小米', '小米MIX Flip', '保留处理器信息更完整的版本'),  # 保留 小米MIX Flip (骁龙8 Gen3)
    ('小米', '小米MIX FOLD 4', '大小写重复，保留 Fold 版本'),
    ('小米', '小米 17 Ultra', '多余空格，保留无空格版本'),
    # 真我
    ('真我', '真我GT Neo5 SE', '保留处理器信息更完整的版本'),  # 骁龙7+ Gen 2
    ('真我', '真我GT Neo6 SE', '保留有主摄的版本'),  # 保留有主摄的版本
]

deleted = 0
for brand, model, reason in duplicates_to_delete:
    cursor.execute('DELETE FROM phones WHERE brand = ? AND model = ?', (brand, model))
    if cursor.rowcount > 0:
        deleted += cursor.rowcount
        print(f"  删除: {brand} - {model} ({reason})")

print(f"\n删除重复机型: {deleted}条")

# ============================================
# 第二部分：补充缺失的主摄数据
# ============================================
print("\n【二、补充缺失主摄】")

camera_supplements = [
    # OPPO
    ('OPPO', 'OPPO Find N2', '5000万'),
    ('OPPO', 'OPPO Find N3', '4800万'),
    ('OPPO', 'OPPO Find N6', '2亿'),
    ('OPPO', 'OPPO Find X8 Ultra', '5000万'),
    ('OPPO', 'OPPO Find X9 Ultra', '2亿'),
    # 一加
    ('一加', '一加Turbo 6 风驰版', '5000万'),
    ('一加', '一加Turbo 6V', '5000万'),
    # 三星
    ('三星', '三星W25', '2亿'),
    ('三星', '三星W26', '2亿'),
    # 努比亚
    ('努比亚', '努比亚Flip 2', '5000万'),
    ('努比亚', '努比亚红魔11 Air', '5000万'),
    ('努比亚', '努比亚红魔11Pro', '5000万'),
    ('努比亚', '努比亚红魔11Pro+', '5000万'),
    # 华为
    ('华为', '华为Mate XTs 非凡大师', '5000万'),
    ('华为', '华为Mate X7', '5000万'),
    ('华为', 'HUAWEI Pura X', '5000万'),
    ('华为', '华为畅享90 Pro Max 128GB', '5000万'),
    ('华为', '华为novaFlip', '5000万'),
    # 小米
    ('小米', '小米MIX Flip 2', '5000万'),
    # 真我
    ('真我', '真我12', '1亿'),
    ('真我', '真我12x', '5000万'),
    ('真我', '真我15', '5000万'),
    ('真我', '真我15T', '5000万'),
    ('真我', '真我GT Neo', '6400万'),
    ('真我', '真我GT Neo 闪速版', '6400万'),
    ('真我', '真我GT Neo2T', '6400万'),
    ('真我', '真我GT Neo6', '5000万'),
    ('真我', '真我GT Neo6 SE', '5000万'),
    ('真我', '真我GT2 Pro', '5000万'),
    ('真我', '真我Q2', '4800万'),
    ('真我', '真我Q3', '4800万'),
    ('真我', '真我Q3 Pro', '6400万'),
    ('真我', '真我Q3s', '4800万'),
    ('真我', '真我V11', '1300万'),
    ('真我', '真我V15', '6400万'),
    ('真我', '真我X7 Pro', '6400万'),
    # 红米
    ('红米', 'Redmi  K80至尊版', '5000万'),
    ('红米', 'Redmi K90 Pro Max', '5000万'),
    ('红米', 'Redmi Turbo 5 MAX', '5000万'),
    # 联想
    ('联想', 'Moto Razr', '5000万'),
    ('联想', 'Moto S50 7300', '5000万'),
    ('联想', 'Moto X70 Air', '5000万'),
    ('联想', 'Moto X70 Air Pro', '5000万'),
    ('联想', 'Moto edge', '5000万'),
    ('联想', 'Moto edge 60 Pro', '5000万'),
    ('联想', 'Moto razr', '5000万'),
    # 苹果
    ('苹果', '苹果 iPhone 17', '4800万'),
    ('苹果', '苹果iPhone 17 Pro Max', '4800万'),
    ('苹果', '苹果iPhone 17e', '4800万'),
    # 荣耀
    ('荣耀', 'Neo7x', '5000万'),
    ('荣耀', '荣耀 500 Pro', '2亿'),
]

supplemented = 0
for brand, model, camera in camera_supplements:
    cursor.execute('UPDATE phones SET camera_main = ? WHERE brand = ? AND model = ? AND (camera_main IS NULL OR camera_main = "" OR camera_main = "无")', (camera, brand, model))
    if cursor.rowcount > 0:
        supplemented += cursor.rowcount
        print(f"  补充: {brand} - {model} -> {camera}")

print(f"\n补充主摄数据: {supplemented}条")

conn.commit()

# ============================================
# 统计最终结果
# ============================================
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM phones WHERE processor IS NOT NULL AND processor != "" AND processor != "无"')
processor_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM phones WHERE camera_main IS NOT NULL AND camera_main != "" AND camera_main != "无"')
camera_count = cursor.fetchone()[0]

print("\n" + "=" * 60)
print("最终数据质量")
print("=" * 60)
print(f"总记录数: {total}款")
print(f"处理器覆盖率: {processor_count}/{total} ({processor_count/total*100:.1f}%)")
print(f"主摄覆盖率: {camera_count}/{total} ({camera_count/total*100:.1f}%)")

# 按品牌统计
cursor.execute('SELECT brand, COUNT(*) as cnt FROM phones GROUP BY brand ORDER BY cnt DESC')
brands = cursor.fetchall()
print("\n品牌分布:")
for brand, cnt in brands:
    print(f"  {brand}: {cnt}款")

conn.close()

print("\n完成! 备份文件: backend/data/phones_backup_merge_supplement.db")

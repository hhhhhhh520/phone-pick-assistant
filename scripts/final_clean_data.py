# -*- coding: utf-8 -*-
import sqlite3
import shutil

# 备份数据库
shutil.copy('backend/data/phones.db', 'backend/data/phones_backup_final_clean.db')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

print("=" * 60)
print("数据最终清洗")
print("=" * 60)

# ============================================
# 第一部分：像素格式统一（万 → 亿）
# ============================================
print("\n【一、像素格式统一】")

pixel_corrections = [
    # 三星 2亿像素
    ('三星', 'Galaxy S24 Ultra', '2亿'),
    ('三星', 'Galaxy S25 Ultra', '2亿'),
    ('三星', 'Galaxy S26 Ultra', '2亿'),
    ('三星', '三星Galaxy S23 Ultra', '2亿'),
    ('三星', '三星Galaxy S26 Ultra', '2亿'),
    ('三星', '三星Galaxy Z TriFold', '2亿'),
    # 小米 1亿像素
    ('小米', '小米10', '1亿'),
    ('小米', '小米10S', '1亿'),
    ('小米', '小米11', '1亿'),
    ('小米', '小米MIX 4', '1亿'),
    ('小米', 'Redmi Note 13 Pro', '2亿'),
    # 红米
    ('红米', 'Redmi Note 13 Pro', '2亿'),
    # 努比亚
    ('努比亚', '努比亚小牛', '1.08亿'),
    # 荣耀
    ('荣耀', '荣耀500 Pro', '2亿'),
    ('荣耀', '荣耀X60 Pro', '1.08亿'),
    # 联想
    ('联想', 'Moto Edge S Pro高通骁龙870处理器', '1.08亿'),
    ('联想', 'Moto Edge S30骁龙888 Plus处理器', '1.08亿'),
    ('联想', 'Moto Edge', '1亿'),
]

pixel_fixed = 0
for brand, model, new_pixel in pixel_corrections:
    cursor.execute('UPDATE phones SET camera_main = ? WHERE brand = ? AND model = ?', (new_pixel, brand, model))
    if cursor.rowcount > 0:
        pixel_fixed += cursor.rowcount

print(f"像素格式统一: {pixel_fixed}条")

# ============================================
# 第二部分：删除重复记录（无前缀版本）
# ============================================
print("\n【二、删除重复记录】")

# 需要删除的无前缀版本（保留带完整品牌前缀的）
duplicates_to_delete = [
    # OPPO
    ('OPPO', 'Find X6 Pro'),
    ('OPPO', 'Find X7 Pro'),
    ('OPPO', 'Find X8 Pro'),
    ('OPPO', 'Find X9 Pro'),
    # vivo
    ('vivo', 'X Fold3 Pro'),
    ('vivo', 'X100 Pro'),
    ('vivo', 'X200 Pro'),
    ('vivo', 'iQOO 12 Pro'),  # 应归 iQOO
    ('vivo', 'iQOO 15 Ultra'),  # 应归 iQOO
    ('vivo', 'iQOO Neo'),
    ('vivo', 'iQOO Z'),
    ('vivo', 'iQOO Z10 Turbo'),
    ('vivo', 'iQOO Z9 Turbo'),
    # 一加
    ('一加', 'Ace 3 Pro'),
    ('一加', 'Ace 6T'),
    ('一加', 'Turbo 6V'),
    ('一加', '12哈苏全焦段超光影'),  # 非正式名称
    # 三星
    ('三星', 'Galaxy S23 Ultra'),
    ('三星', 'Galaxy S24 Ultra'),
    ('三星', 'Galaxy S25 Ultra'),
    ('三星', 'Galaxy S26 Ultra'),
    ('三星', 'Galaxy Z Flip7多模态Galaxy Al'),  # 保留更完整的版本
    # 努比亚
    ('努比亚', 'Z50 Ultra'),
    ('努比亚', 'Z60 Ultra'),
    ('努比亚', 'Z70 Ultra'),
    ('努比亚', 'Z80 Ultra'),
    ('努比亚', '红魔10 Pro'),
    ('努比亚', '红魔10 Pro+'),
    ('努比亚', '红魔11 Air'),
    ('努比亚', '红魔11Pro'),
    ('努比亚', '红魔9 Pro'),
    # 华为
    ('华为', 'Mate 60 Pro'),
    ('华为', 'Mate 70 Pro'),
    ('华为', 'Mate 80 Pro'),
    ('华为', 'Pura 70 Pro'),
    ('华为', 'Pura 80 Pro'),
    ('华为', 'Pura 80 Ultra'),
    ('华为', 'Pura 90 Pro'),
    ('华为', 'Pura X Max'),
    ('华为', 'nova 14 Pro'),
    ('华为', 'nova 14 Ultra'),
    ('华为', 'nova 15 Pro'),
    ('华为', 'nova 15 Ultra'),
    ('华为', '华为 Pura 90 Pro'),  # 有空格版本
    # 小米
    ('小米', 'MIX FOLD'),
    ('小米', 'RedmiTurbo'),  # 拼写错误
    # 真我
    ('真我', 'GT2 Pro'),
    ('真我', 'GT5 Pro'),
    ('真我', 'GT7 Pro'),
    ('真我', 'GT8 Pro'),
    ('真我', '15 Pro'),
    # 红米
    ('红米', '红米note14'),  # 格式不统一
    # 苹果
    ('苹果', 'iPhone 15 Plus'),
    ('苹果', 'iPhone 15 Pro'),
    ('苹果', 'iPhone 16 Plus'),
    ('苹果', 'iPhone 16 Pro'),
    ('苹果', 'iPhone 17 Pro'),
    ('苹果', '苹果 iPhone 17 Pro Max'),  # 有空格版本
    # 荣耀
    ('荣耀', '荣耀 500 Pro'),  # 有空格版本
    # 魅族 - 非正式名称
    ('魅族', '17 Pro'),
    ('魅族', '17超线性扬声器'),
    ('魅族', '18 Pro'),
    ('魅族', '20 INFINITY'),
    ('魅族', '20 Pro'),
    ('魅族', '21 Note'),
    ('魅族', '21 Pro'),
    ('魅族', 'Note 16 Pro'),
    # 黑鲨
    ('黑鲨', '4S Pro'),
]

deleted = 0
for brand, model in duplicates_to_delete:
    cursor.execute('DELETE FROM phones WHERE brand = ? AND model = ?', (brand, model))
    if cursor.rowcount > 0:
        deleted += cursor.rowcount

print(f"删除重复记录: {deleted}条")

# ============================================
# 第三部分：名称规范化
# ============================================
print("\n【三、名称规范化】")

name_corrections = [
    # OPPO
    ('OPPO', 'Reno 11 Pro', 'OPPO Reno 11 Pro'),
    # ROG
    ('ROG', '5s Pro', 'ROG 5s Pro'),
    ('ROG', 'ROG 6', 'ROG 6'),
    # vivo
    ('vivo', 'X Fold', 'vivo X Fold'),
    # 三星
    ('三星', 'Galaxy Z Flip7 FEAl大视野智能外屏', '三星Galaxy Z Flip7 FE'),
    # 努比亚
    ('努比亚', '努比亚红魔10 Pro+骁龙8至尊版', '努比亚红魔10 Pro+'),
    ('努比亚', '努比亚红魔10 Pro骁龙8至尊版', '努比亚红魔10 Pro'),
    # 华为
    ('华为', 'Mate XTs 非凡', '华为Mate XTs 非凡大师'),
    # 小米
    ('小米', 'MIX Flip', '小米MIX Flip'),
    ('小米', 'MIX Fold', '小米MIX Fold 4'),
    # 真我 - 统一GT系列格式
    ('真我', 'GT Neo5', '真我GT Neo5'),
    ('真我', 'GT Neo5 SE', '真我GT Neo5 SE'),
    ('真我', 'GT Neo6 SE', '真我GT Neo6 SE'),
    # 联想
    ('联想', 'moto S50 Neo', 'Moto S50 Neo'),
    # 魅族 - 添加品牌前缀
    ('魅族', '魅族22', '魅族22'),  # 保持不变，已正确
]

renamed = 0
for brand, old_name, new_name in name_corrections:
    cursor.execute('UPDATE phones SET model = ? WHERE brand = ? AND model = ?', (new_name, brand, old_name))
    if cursor.rowcount > 0:
        renamed += cursor.rowcount

print(f"名称规范化: {renamed}条")

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

print("\n✅ 清洗完成！备份文件: backend/data/phones_backup_final_clean.db")

# -*- coding: utf-8 -*-
import sqlite3
import shutil

# 备份数据库
shutil.copy('backend/data/phones.db', 'backend/data/phones_backup_price_supplement.db')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 价格补充数据（参考京东/天猫价格，单位：元）
price_supplements = {
    # OPPO
    ('OPPO', 'A32'): 999,
    ('OPPO', 'Find N3'): 9999,
    ('OPPO', 'Find X7'): 3999,
    ('OPPO', 'Find X7 Ultra'): 5999,
    ('OPPO', 'Find X8'): 4199,
    ('OPPO', 'Find X8 Pro'): 5299,
    ('OPPO', 'Reno 12'): 2699,

    # vivo
    ('vivo', 'S19'): 2499,
    ('vivo', 'X Fold3 Pro'): 9999,
    ('vivo', 'X100'): 3699,
    ('vivo', 'X100 Pro'): 4999,
    ('vivo', 'X100 Ultra'): 6499,
    ('vivo', 'X100s'): 3999,
    ('vivo', 'X200'): 3699,
    ('vivo', 'X200 Pro mini'): 4699,

    # 一加
    ('一加', '一加15T'): 3999,
    ('一加', '一加Ace 6T'): 2999,
    ('一加', '一加Turbo 6 风驰版'): 1999,

    # 三星
    ('三星', '三星W26'): 15999,

    # 努比亚
    ('努比亚', '努比亚Z80 Ultra'): 5999,
    ('努比亚', '努比亚红魔11Pro'): 4999,

    # 华为
    ('华为', 'HUAWEI Pura 70'): 4999,
    ('华为', '华为Mate30'): 3999,
    ('华为', '华为Mate30 Pro'): 5799,

    # 小米
    ('小米', '小米10'): 3799,
    ('小米', '小米10S'): 3299,
    ('小米', '小米11'): 3999,
    ('小米', '小米11青春版'): 2299,
    ('小米', '小米14'): 3999,
    ('小米', '小米15'): 4499,
    ('小米', '小米15 Pro16GB/1TB'): 5999,
    ('小米', '小米15 Ultra'): 6499,
    ('小米', '小米15S Pro'): 4999,
    ('小米', '小米17'): 4999,
    ('小米', '小米17 Pro'): 5999,
    ('小米', '小米17 Pro Max'): 6999,
    ('小米', '小米17 Ultra'): 7999,
    ('小米', '小米Civi'): 2599,
    ('小米', '小米Civi 3'): 2499,
    ('小米', '小米Civi 4 Pro'): 2999,
    ('小米', '小米Civi 5 Pro'): 3299,
    ('小米', '小米MIX 4'): 4999,
    ('小米', '小米MIX FOLD 4'): 9999,
    ('小米', '小米MIX Flip'): 5999,
    ('小米', '小米MIX Flip 2'): 6499,
    ('小米', 'Redmi K'): 1999,
    ('小米', 'Redmi K70 Pro'): 3299,
    ('小米', 'Redmi K80 Pro'): 3699,
    ('小米', 'Redmi K90 Pro'): 3999,
    ('小米', 'Redmi Note'): 1199,
    ('小米', 'Redmi Note 13 Pro'): 1699,
    ('小米', 'Redmi Note 14 Pro'): 1999,
    ('小米', 'Redmi Note 15 Pro'): 2299,
    ('小米', 'Redmi Turbo'): 1999,
    ('小米', 'Redmi Turbo 4 Pro'): 2499,
    ('小米', 'RedmiTurbo'): 1999,

    # 真我
    ('真我', '15 Pro'): 2499,
    ('真我', '15T前后5000万'): 1999,
    ('真我', 'GT Neo'): 2299,
    ('真我', 'GT Neo5'): 2799,
    ('真我', 'GT Neo5 SE'): 1999,
    ('真我', 'GT Neo6 SE'): 2299,
    ('真我', 'GT2 Pro'): 3999,
    ('真我', 'GT5 Pro'): 3599,
    ('真我', 'GT7 Pro'): 3999,
    ('真我', 'GT8 Pro'): 4499,
    ('真我', 'Q3 Pro'): 1999,
    ('真我', '真我15'): 1799,
    ('真我', '真我15 Pro'): 2499,
    ('真我', '真我15T'): 1999,
    ('真我', '真我GT Neo2'): 2299,
    ('真我', '真我GT Neo5 150W'): 2999,
    ('真我', '真我GT Neo5 SE'): 1999,
    ('真我', '真我GT 大师探索版'): 2799,
    ('真我', '真我GT5 150W'): 3299,
    ('真我', '真我GT5 Pro'): 3599,
    ('真我', '真我GT6'): 3299,
    ('真我', '真我GT7'): 3699,
    ('真我', '真我GT7 Pro'): 3999,
    ('真我', '真我GT7 Pro竞速版'): 3799,
    ('真我', '真我GT8'): 3999,
    ('真我', '真我GT8 Pro'): 4499,
    ('真我', '真我Neo7'): 2999,
    ('真我', '真我Neo7 SE'): 1999,
    ('真我', '真我Neo7 Turbo'): 2499,
    ('真我', '真我Neo8'): 3299,
    ('真我', '真我Q3'): 1399,
    ('真我', '真我Q3 Pro'): 1999,
    ('真我', '真我Q3s'): 1599,
    ('真我', '真我V11'): 1199,
    ('真我', '真我V15'): 1799,
    ('真我', '真我X7 Pro'): 2299,

    # 索尼
    ('索尼', 'Xperia'): 4999,
    ('索尼', 'Xperia PRO-I'): 7999,
    ('索尼', '索尼Xperia 1 IV'): 6999,
    ('索尼', '索尼Xperia 10 III高通骁龙690'): 2499,
    ('索尼', '索尼Xperia 10 IV'): 2999,
    ('索尼', '索尼Xperia 5 III高通骁龙888'): 5999,
    ('索尼', '索尼Xperia PRO-I高通骁龙888'): 7999,
    ('索尼', '索尼Xperia Pro360度天线设计'): 9999,
    ('索尼', '索尼移动Xperia 1 V'): 7999,
    ('索尼', '索尼移动Xperia 1 VII'): 8999,
    ('索尼', '索尼移动Xperia 5 V'): 5999,
    ('索尼', '索尼移动Xperia 5 Ⅳ 骁龙8 Gen1'): 5999,
    ('索尼', '索尼移动Xperia Pro-i II'): 9999,

    # 红米
    ('红米', 'Redmi  K80至尊版'): 3299,
    ('红米', 'Redmi  Note 14'): 1399,
    ('红米', 'Redmi  Note 14 Pro'): 1799,
    ('红米', 'Redmi  Note 15'): 1599,
    ('红米', 'Redmi K70'): 2499,
    ('红米', 'Redmi K80'): 2699,
    ('红米', 'Redmi K80 Pro'): 3699,
    ('红米', 'Redmi K80至尊版'): 3299,
    ('红米', 'Redmi K90'): 2999,
    ('红米', 'Redmi K90 Max'): 3499,
    ('红米', 'Redmi K90 Pro Max'): 3999,
    ('红米', 'Redmi Note 13 Pro'): 1699,
    ('红米', 'Redmi Note 15 Pro'): 2299,
    ('红米', 'Redmi Note 15 Pro+'): 2699,
    ('红米', 'Redmi Turbo 4'): 1999,
    ('红米', 'Redmi Turbo 4 Pro 8s'): 2499,
    ('红米', 'Redmi Turbo 4天玑 8400-Ultra'): 1999,
    ('红米', 'Redmi Turbo 5'): 2499,
    ('红米', 'Redmi Turbo 5 MAX'): 2999,
    ('红米', '红米note'): 999,

    # 联想
    ('联想', 'Moto Edge'): 2999,
    ('联想', 'Moto Edge S Pro高通骁龙870处理器'): 2499,
    ('联想', 'Moto Edge S30骁龙888 Plus处理器'): 2799,
    ('联想', 'Moto Razr'): 5999,
    ('联想', 'Moto Razr 50'): 3999,
    ('联想', 'Moto S'): 2499,
    ('联想', 'Moto S50 7300'): 2499,
    ('联想', 'Moto X70 Air'): 2999,
    ('联想', 'Moto X70 Air Pro'): 3999,
    ('联想', 'Moto edge'): 2999,
    ('联想', 'Moto edge 60 Pro'): 3299,
    ('联想', 'Moto edge s骁龙870'): 2499,
    ('联想', 'Moto g'): 1299,
    ('联想', 'Moto g100'): 2499,
    ('联想', 'Moto g100 Pro'): 2799,
    ('联想', 'Moto g100s'): 2699,
    ('联想', 'Moto g54'): 1499,
    ('联想', 'Moto g75'): 1799,
    ('联想', 'Moto razr'): 5999,
    ('联想', 'Moto razr 50 Ultra'): 6999,
    ('联想', 'Moto razr 60 12GB+512GB60万次折叠认证'): 4999,
    ('联想', 'Moto razr 60 8GB+256GB60万次折叠认证'): 4499,
    ('联想', 'Moto razr 60 Ultra'): 7999,
    ('联想', 'moto S50 Neo'): 2299,

    # 苹果
    ('苹果', 'iPhone 15 Plus'): 7999,
    ('苹果', 'iPhone 15 Pro'): 8999,
    ('苹果', 'iPhone 16 Plus'): 8999,
    ('苹果', 'iPhone 16 Pro'): 9999,
    ('苹果', 'iPhone 17 Pro'): 10999,
    ('苹果', 'iPhone Air 1TB'): 12999,
    ('苹果', 'iPhone Air 256GB'): 9999,
    ('苹果', 'iPhone XR'): 4999,
    ('苹果', '苹果 iPhone 17'): 7999,
    ('苹果', '苹果 iPhone 17 Pro Max'): 12999,
    ('苹果', '苹果iPhone 15'): 6999,
    ('苹果', '苹果iPhone 15 Plus'): 7999,
    ('苹果', '苹果iPhone 15 Pro'): 8999,
    ('苹果', '苹果iPhone 15 Pro Max'): 9999,
    ('苹果', '苹果iPhone 16'): 7999,
    ('苹果', '苹果iPhone 16 Plus'): 8999,
    ('苹果', '苹果iPhone 16 Pro'): 9999,
    ('苹果', '苹果iPhone 16 Pro Max'): 10999,
    ('苹果', '苹果iPhone 16e'): 5999,
    ('苹果', '苹果iPhone 17'): 7999,
    ('苹果', '苹果iPhone 17 Pro'): 10999,
    ('苹果', '苹果iPhone 17 Pro Max'): 12999,
    ('苹果', '苹果iPhone 17e'): 5999,

    # 荣耀
    ('荣耀', 'Magic V'): 9999,
    ('荣耀', 'Magic V Flip'): 6999,
    ('荣耀', 'Magic6 Pro'): 5999,
    ('荣耀', 'Magic7 Pro'): 6499,
    ('荣耀', 'Neo7x'): 1999,
    ('荣耀', '荣耀 500 Pro'): 2999,
    ('荣耀', '荣耀500 Pro'): 2999,
    ('荣耀', '荣耀X60 Pro'): 1999,

    # 魅族
    ('魅族', '17 Pro'): 3999,
    ('魅族', '17超线性扬声器'): 3699,
    ('魅族', '18 Pro'): 4999,
    ('魅族', '20 INFINITY'): 5999,
    ('魅族', '20 Pro'): 4999,
    ('魅族', '21 Note'): 2999,
    ('魅族', '21 Pro'): 5399,
    ('魅族', 'Note 16 Pro'): 1999,
    ('魅族', '魅族22'): 3999,

    # 黑鲨
    ('黑鲨', '4S Pro'): 3999,
    ('黑鲨', '黑鲨4'): 2999,

    # ROG
    ('ROG', '5s Pro'): 4999,
    ('ROG', 'ROG 6'): 5999,
    ('ROG', 'ROG 8'): 5999,
    ('ROG', 'ROG 8 Pro'): 7999,
    ('ROG', 'ROG 8骁龙8Gen3'): 5999,
    ('ROG', 'ROG 游戏手机9'): 6999,
    ('ROG', 'ROG 游戏手机9 Pro'): 7999,

    # iQOO
    ('iQOO', 'iQOO 12'): 3999,
    ('iQOO', 'iQOO 12 Pro'): 4999,
    ('iQOO', 'iQOO 13'): 4499,
    ('iQOO', 'iQOO 15'): 4999,
    ('iQOO', 'iQOO 15 Ultra'): 6999,
    ('iQOO', 'iQOO Neo10'): 3299,
    ('iQOO', 'iQOO Neo11'): 3699,
    ('iQOO', 'iQOO Neo9 8'): 2999,
    ('iQOO', 'iQOO Z10 Turbo'): 2299,
    ('iQOO', 'iQOO Z10 Turbo Pro'): 2699,
    ('iQOO', 'iQOO Z10 Turbo+'): 2999,
    ('iQOO', 'iQOO Z10x'): 1699,
    ('iQOO', 'iQOO Z11'): 1999,
    ('iQOO', 'iQOO Z11 Turbo'): 2499,
    ('iQOO', 'iQOO Z11x'): 1499,
    ('iQOO', 'iQOO Z9'): 1799,
    ('iQOO', 'iQOO Z9 Turbo'): 2299,
    ('iQOO', 'iQOO Z9 Turbo 长续航版'): 2499,
}

# 执行更新
updated = 0
for (brand, model), price in price_supplements.items():
    cursor.execute('''
        UPDATE phones SET price = ?
        WHERE brand = ? AND model = ? AND (price IS NULL OR price = 0 OR price = '')
    ''', (price, brand, model))
    if cursor.rowcount > 0:
        updated += cursor.rowcount

conn.commit()

# 统计
cursor.execute('SELECT COUNT(*) FROM phones WHERE price IS NOT NULL AND price != 0 AND price != ""')
price_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]

print(f'价格补充: {updated}条')
print(f'价格覆盖率: {price_count}/{total} ({price_count/total*100:.1f}%)')

conn.close()

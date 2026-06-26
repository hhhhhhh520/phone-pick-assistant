# -*- coding: utf-8 -*-
import sqlite3
import shutil

# 备份数据库
shutil.copy('backend/data/phones.db', 'backend/data/phones_backup_processor_supplement.db')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 处理器补充数据（基于常见型号配置）
processor_supplements = {
    # OPPO
    ('OPPO', 'Find N6'): '高通 骁龙8 至尊版',
    ('OPPO', 'Reno15'): '联发科 天玑8350',

    # iQOO
    ('iQOO', 'Neo10'): '高通 骁龙8 Gen3',
    ('iQOO', 'Neo11'): '联发科 天玑9400',
    ('iQOO', 'Neo9 8'): '高通 骁龙8 Gen2',
    ('iQOO', 'Z10 Turbo'): '高通 骁龙8s Gen3',
    ('iQOO', 'Z10 Turbo Pro'): '高通 骁龙8s Gen3',
    ('iQOO', 'Z10 Turbo+'): '联发科 天玑9300+',
    ('iQOO', 'Z10x'): '高通 骁龙6 Gen3',
    ('iQOO', 'Z11'): '联发科 天玑9400',
    ('iQOO', 'Z11 Turbo'): '高通 骁龙8s Gen3',
    ('iQOO', 'Z11x'): '高通 骁龙7 Gen3',
    ('iQOO', 'Z9'): '高通 骁龙7 Gen3',
    ('iQOO', 'Z9 Turbo'): '高通 骁龙8s Gen3',
    ('iQOO', 'Z9 Turbo 长续航版'): '高通 骁龙8s Gen3',

    # vivo
    ('vivo', 'X300 Ultra'): '高通 骁龙8 至尊版',
    ('vivo', 'Y200i'): '高通 骁龙4 Gen2',

    # 一加
    ('一加', '一加15'): '高通 骁龙8 至尊版',
    ('一加', '一加15T'): '高通 骁龙8 至尊版',
    ('一加', '一加Ace 3'): '高通 骁龙8 Gen2',
    ('一加', '一加Ace 3 Pro 8'): '高通 骁龙8 Gen3',
    ('一加', '一加Ace 5 8'): '高通 骁龙8 Gen3',
    ('一加', '一加Ace 5 至尊版'): '高通 骁龙8 至尊版',
    ('一加', '一加Ace 6'): '高通 骁龙8 至尊版',
    ('一加', '一加Ace 6 至尊版'): '高通 骁龙8 至尊版',
    ('一加', '一加Ace 6T'): '高通 骁龙8 至尊版',

    # 华为
    ('华为', 'HUAWEI Mate 80 Pro'): '海思 麒麟9030',
    ('华为', 'HUAWEI Pura X'): '海思 麒麟9010',
    ('华为', '华为Mate X7'): '海思 麒麟9020',
    ('华为', '华为Mate XTs 非凡大师'): '海思 麒麟9020',
    ('华为', '华为nova 15'): '海思 麒麟8020',
    ('华为', '华为novaFlip'): '海思 麒麟8000',
    ('华为', '华为畅享90 Pro Max 128GB'): '海思 麒麟8000',

    # 小米
    ('小米', '小米15 Pro'): '高通 骁龙8 至尊版',
    ('小米', '小米15 Ultra'): '高通 骁龙8 至尊版',
    ('小米', '小米MIX Flip 2'): '高通 骁龙8 至尊版',

    # 真我
    ('真我', '真我GT8'): '高通 骁龙8 至尊版',
    ('真我', '真我GT8 Pro'): '高通 骁龙8 至尊版',

    # 红米
    ('红米', 'Redmi  K80至尊版'): '联发科 天玑9400+',
    ('红米', 'Redmi K80至尊版'): '联发科 天玑9400+',
    ('红米', 'Redmi K90'): '高通 骁龙8 Gen3',
    ('红米', 'Redmi K90 Max'): '高通 骁龙8 至尊版',
    ('红米', 'Redmi K90 Pro Max'): '高通 骁龙8 至尊版',
    ('红米', 'Redmi Note 15'): '联发科 天玑7300',
    ('红米', 'Redmi Note 15 Pro+'): '联发科 天玑8400',
    ('红米', 'Redmi Turbo 4'): '联发科 天玑8400-Ultra',
    ('红米', 'Redmi Turbo 4 Pro 8s'): '高通 骁龙8s Gen3',
    ('红米', 'Redmi Turbo 5'): '高通 骁龙8s Gen3',
    ('红米', 'Redmi Turbo 5 MAX'): '高通 骁龙8 至尊版',

    # 联想
    ('联想', 'Moto X70 Air'): '高通 骁龙7 Gen3',
    ('联想', 'Moto X70 Air Pro'): '高通 骁龙8 至尊版',
    ('联想', 'Moto edge'): '高通 骁龙8 Gen3',
    ('联想', 'Moto edge 60 Pro'): '联发科 天玑8350',
    ('联想', 'Moto razr'): '联发科 天玑7400',

    # 努比亚
    ('努比亚', '努比亚Flip 2'): '高通 骁龙7 Gen3',
    ('努比亚', '努比亚红魔11 Air'): '高通 骁龙8 至尊版',
    ('努比亚', '努比亚红魔11Pro'): '高通 骁龙8 至尊版',
    ('努比亚', '努比亚红魔11Pro+'): '高通 骁龙8 至尊版',
    ('努比亚', '努比亚Z80 Ultra'): '高通 骁龙8 至尊版',

    # 三星
    ('三星', '三星Galaxy S24 Ultra'): '高通 骁龙8 Gen3',
    ('三星', '三星Galaxy S25'): '高通 骁龙8 至尊版',
    ('三星', '三星Galaxy S25 Ultra'): '高通 骁龙8 至尊版',
    ('三星', '三星Galaxy Z Flip7 Al'): '高通 骁龙8 至尊版',
    ('三星', '三星W25'): '高通 骁龙8 至尊版',
    ('三星', '三星W26'): '高通 骁龙8 至尊版',

    # 苹果
    ('苹果', 'iPhone 17 Pro'): '苹果 A19 Pro',
    ('苹果', '苹果 iPhone 17'): '苹果 A19',
    ('苹果', '苹果iPhone 17 Pro Max'): '苹果 A19 Pro',
    ('苹果', '苹果iPhone 17e'): '苹果 A19',

    # 荣耀
    ('荣耀', '荣耀 500 Pro'): '高通 骁龙8 至尊版',
    ('荣耀', 'Neo7x'): '高通 骁龙6 Gen4',
}

# 执行更新
updated = 0
for (brand, model), processor in processor_supplements.items():
    cursor.execute('''
        UPDATE phones SET processor = ?
        WHERE brand = ? AND model = ? AND (processor IS NULL OR processor = '' OR processor = '无')
    ''', (processor, brand, model))
    if cursor.rowcount > 0:
        updated += cursor.rowcount
        print(f'  更新: {brand} - {model} -> {processor}')

conn.commit()

# 统计
cursor.execute('SELECT COUNT(*) FROM phones WHERE processor IS NOT NULL AND processor != "" AND processor != "无"')
processor_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]

print(f'\n处理器补充: {updated}条')
print(f'处理器覆盖率: {processor_count}/{total} ({processor_count/total*100:.1f}%)')

conn.close()

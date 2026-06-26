# -*- coding: utf-8 -*-
import sqlite3
import shutil

# 备份数据库
shutil.copy('backend/data/phones.db', 'backend/data/phones_backup_camera_supplement.db')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 主摄补充数据
camera_supplements = {
    # OPPO
    ('OPPO', 'Find X8s'): '5000万',
    ('OPPO', 'Find X8s+'): '5000万',

    # iQOO
    ('iQOO', 'Z9 Turbo 长续航版'): '5000万',

    # vivo
    ('vivo', 'X Fold'): '5000万',
    ('vivo', 'X Fold5'): '5000万',
    ('vivo', 'vivo'): '5000万',

    # 三星
    ('三星', '三星Galaxy S24 Ultra'): '2亿',
    ('三星', '三星Galaxy S25'): '5000万',
    ('三星', '三星Galaxy S25 Ultra'): '2亿',
    ('三星', '三星Galaxy Z Flip7 Al'): '5000万',

    # 努比亚
    ('努比亚', '努比亚Z80 Ultra'): '5000万',

    # 华为
    ('华为', 'HUAWEI Mate 80 Pro'): '5000万',
    ('华为', '华为畅享90 Pro Max 128GB'): '5000万',

    # 小米
    ('小米', 'Redmi K90 Pro'): '5000万',

    # 真我
    ('真我', '15T前后5000万'): '5000万',

    # 索尼
    ('索尼', 'Xperia'): '1200万',
    ('索尼', '索尼Xperia Pro360度天线设计'): '1200万',
    ('索尼', '索尼移动Xperia 1 VII'): '4800万',

    # 红米
    ('红米', 'Redmi K80至尊版'): '5000万',
}

# 执行更新
updated = 0
for (brand, model), camera in camera_supplements.items():
    cursor.execute('''
        UPDATE phones SET camera_main = ?
        WHERE brand = ? AND model = ? AND (camera_main IS NULL OR camera_main = '' OR camera_main = '无')
    ''', (camera, brand, model))
    if cursor.rowcount > 0:
        updated += cursor.rowcount
        print(f'  更新: {brand} - {model} -> {camera}')

conn.commit()

# 统计
cursor.execute('SELECT COUNT(*) FROM phones WHERE camera_main IS NOT NULL AND camera_main != "" AND camera_main != "无"')
camera_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]

print(f'\n主摄补充: {updated}条')
print(f'主摄覆盖率: {camera_count}/{total} ({camera_count/total*100:.1f}%)')

conn.close()

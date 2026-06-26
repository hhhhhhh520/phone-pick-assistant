# -*- coding: utf-8 -*-
"""补充缺失数据"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from backend.api.dependencies import get_db  # noqa: E402
from backend.models.domain import Phone  # noqa: E402

db = next(get_db())

# 补充数据映射 (型号 -> 字段更新)
updates = {
    # 苹果
    'iPhone 16': {'camera_main': '4800万像素'},
    'iPhone 17 Pro': {'storage': '未知', 'ram': '未知', 'camera_main': '未知'},
    'iPhone Air 256GB': {'ram': '8GB'},
    'iPhone 17': {'storage': '未知', 'ram': '未知'},
    'iPhone 13': {'camera_main': '1200万像素'},
    'iPhone 13 Pro': {'ram': '6GB'},
    'iPhone 11 Pro': {'camera_main': '1200万像素'},
    'iPhone 12 mini': {'camera_main': '1200万像素'},
    'iPhone Air 1TB': {'ram': '8GB'},

    # 小米
    'Redmi K80': {'camera_main': '5000万像素'},
    'Redmi Turbo 4': {'storage': '256GB', 'ram': '12GB', 'camera_main': '5000万像素'},
    'Redmi K90': {'camera_main': '未知'},
    'Redmi K90 Pro': {'camera_main': '未知'},
    'Redmi Note 15 Pro': {'camera_main': '未知'},
    'Redmi Turbo 5': {'camera_main': '未知'},
    'Redmi K70': {'camera_main': '5000万像素'},
    'Redmi K80 至尊版': {'camera_main': '5000万像素'},
    'Redmi K80 Pro': {'camera_main': '5000万像素'},
    'Redmi K60': {'camera_main': '6400万像素'},
    'MIX 4': {'camera_main': '1亿像素'},

    # vivo
    'iQOO 12': {'camera_main': '5000万像素'},
    'iQOO Neo10': {'camera_main': '5000万像素'},
    'iQOO Z9 Turbo': {'camera_main': '5000万像素'},
    'X Fold5': {'camera_main': '未知'},
    'vivo Y300 Pro': {'camera_main': '5000万像素'},
    'vivo S50': {'camera_main': '5000万像素'},
    'vivo Y500': {'camera_main': '5000万像素'},
    'vivo Y500 Pro': {'camera_main': '5000万像素'},
    'vivo X300 Pro': {'camera_main': '未知'},
    'vivo Y300': {'camera_main': '5000万像素'},
    'vivo Y200': {'camera_main': '5000万像素'},
    'iQOO Z11 Turbo': {'camera_main': '未知'},
    'iQOO 15': {'camera_main': '未知'},
    'iQOO 15 Ultra': {'camera_main': '未知'},
    'iQOO Z11': {'camera_main': '未知'},
    'iQOO Neo11': {'camera_main': '未知'},
    'iQOO Z10': {'camera_main': '未知'},
    'iQOO Z10 Turbo': {'camera_main': '未知'},
    'iQOO Z9': {'camera_main': '5000万像素'},
    'iQOO 13': {'camera_main': '5000万像素'},
    'iQOO Neo5': {'camera_main': '4800万像素'},
    'iQOO Neo9': {'camera_main': '5000万像素'},
    'iQOO Neo8': {'camera_main': '5000万像素'},
    'iQOO 12 Pro': {'camera_main': '5000万像素'},

    # 真我
    'GT5 Pro': {'camera_main': '5000万像素'},
    'GT8': {'camera_main': '未知'},
    'GT7': {'camera_main': '未知'},
    'GT Neo5 150W': {'camera_main': '5000万像素'},
    'GT5': {'camera_main': '5000万像素'},
    'GT Neo5 SE': {'camera_main': '6400万像素'},
    'GT 大师探索版': {'camera_main': '5000万像素'},
    'GT Neo2': {'camera_main': '6400万像素'},
    'GT Neo6 SE': {'camera_main': '5000万像素'},
    'Q3': {'camera_main': '4800万像素'},
    '15': {'camera_main': '5000万像素'},
    '15T': {'camera_main': '5000万像素'},
    'Neo7': {'camera_main': '5000万像素'},
    'Neo8': {'camera_main': '5000万像素'},
    'GT6': {'camera_main': '5000万像素'},

    # 一加
    '12': {'camera_main': '5000万像素'},
    '13': {'camera_main': '5000万像素'},
    'Ace 3': {'camera_main': '5000万像素'},
    'Ace 3 Pro': {'camera_main': '5000万像素'},
    'Ace 6 至尊版': {'camera_main': '未知'},
    'Ace 6T': {'camera_main': '未知'},
    'Ace 2': {'camera_main': '5000万像素'},
    'Turbo 6V': {'camera_main': '未知'},
    'Turbo 6': {'camera_main': '未知'},

    # 荣耀
    '荣耀500 Pro': {'storage': '未知', 'ram': '未知'},

    # 华为
    '畅享90 Pro': {'ram': '未知', 'camera_main': '未知'},
    'Pura 90 Pro': {'storage': '未知', 'ram': '未知', 'camera_main': '未知'},
    '畅享 90': {'ram': '未知', 'camera_main': '未知'},
    'nova 15': {'ram': '未知', 'camera_main': '未知'},
    'nova 15 Pro': {'ram': '未知'},
    '畅享 70': {'ram': '未知', 'camera_main': '未知'},
    'nova 15 Ultra': {'ram': '未知'},
    '畅享90 Plus': {'ram': '未知'},
    'Mate X7': {'camera_main': '未知'},
    'nova 14 Ultra': {'ram': '未知'},
    'Pura 80 Pro': {'camera_main': '未知'},
    'P40 Pro': {'camera_main': '5000万像素'},
    '畅享 80': {'ram': '未知'},
    'nova 14 Pro': {'ram': '未知'},
    'Pura 80 Ultra': {'camera_main': '未知'},
    'nova 14': {'ram': '未知'},
    'Mate XTs': {'camera_main': '未知'},
    'novaFlip': {'storage': '256GB', 'ram': '8GB'},
    'Pura X Max': {'storage': '未知', 'ram': '未知'},

    # 三星
    'Galaxy S25 Ultra': {'storage': '256GB', 'ram': '12GB', 'camera_main': '2亿像素'},
    'Galaxy S26 Ultra': {'camera_main': '未知'},
    'Galaxy S24 Ultra': {'camera_main': '2亿像素'},
    'Galaxy S23 Ultra': {'camera_main': '2亿像素'},
    'Galaxy S26': {'camera_main': '未知'},
    'Galaxy S25': {'camera_main': '5000万像素'},
    'Galaxy Note 20 Ultra': {'camera_main': '1.08亿像素'},
    'Galaxy S24': {'camera_main': '5000万像素'},
    'Galaxy S23': {'camera_main': '5000万像素'},
    'Galaxy S22 Ultra': {'camera_main': '1.08亿像素'},
    'Galaxy Z Fold6': {'camera_main': '5000万像素'},
    'Galaxy Z Fold5': {'camera_main': '5000万像素'},
    'Galaxy S20': {'camera_main': '6400万像素'},
    'Galaxy A54': {'camera_main': '5000万像素'},
    'Galaxy S22': {'camera_main': '5000万像素'},

    # 魅族
    '魅族22': {'camera_main': '5000万像素'},
    'Lucky 08': {'camera_main': '1亿像素'},
    '17 Pro': {'camera_main': '6400万像素'},
    'Note 16': {'camera_main': '未知'},
    '21 Pro': {'camera_main': '5000万像素'},
    '20 Pro': {'camera_main': '5000万像素'},
    '20': {'camera_main': '5000万像素'},
    '21 Note': {'camera_main': '5000万像素'},
    '20 INFINITY': {'camera_main': '5000万像素'},
    '17': {'camera_main': '6400万像素'},
    '18X': {'camera_main': '6400万像素'},
    '18': {'camera_main': '6400万像素'},
    '18s': {'camera_main': '6400万像素'},
    '18 Pro': {'camera_main': '5000万像素'},

    # 努比亚
    'Z60 Ultra': {'camera_main': '5000万像素'},
    '红魔11 Air': {'camera_main': '未知'},
    'Z80 Ultra': {'camera_main': '未知'},
    '红魔11 Pro+': {'camera_main': '未知'},
    '红魔10': {'storage': '256GB', 'ram': '12GB', 'camera_main': '5000万像素'},
    'Z70 Ultra': {'camera_main': '5000万像素'},
    '红魔10 Pro': {'camera_main': '5000万像素'},
    '红魔10 Pro+': {'camera_main': '5000万像素'},
    '红魔8 PRO': {'camera_main': '5000万像素'},
    'Z50': {'camera_main': '6400万像素'},
    'Z50 Ultra': {'camera_main': '6400万像素'},
    '红魔9 Pro': {'camera_main': '5000万像素'},
    '小牛': {'camera_main': '5000万像素'},

    # 索尼
    'Xperia 1 IV': {'camera_main': '1200万像素'},
    'Xperia 1 V': {'camera_main': '1200万像素'},
    'Xperia PRO-I': {'camera_main': '1200万像素'},
    'Xperia 5 III': {'camera_main': '1200万像素'},
    'Xperia 5 IV': {'camera_main': '1200万像素'},
    'Xperia 1 VII': {'camera_main': '1200万像素'},
    'Xperia 5 V': {'camera_main': '1200万像素'},

    # 黑鲨
    '黑鲨5 Pro': {'camera_main': '1亿像素'},
    '黑鲨5 RS': {'camera_main': '6400万像素'},
    '黑鲨4': {'camera_main': '4800万像素'},
    '黑鲨4 Pro': {'camera_main': '6400万像素'},
    '黑鲨4S': {'camera_main': '4800万像素'},
    '黑鲨5': {'camera_main': '6400万像素'},
    '黑鲨5 高能版': {'camera_main': '6400万像素'},

    # ROG
    'ROG 7': {'camera_main': '5000万像素'},
    'ROG 8': {'camera_main': '5000万像素'},
    'ROG 9': {'camera_main': '5000万像素'},
    'ROG 5': {'camera_main': '6400万像素'},
    'ROG 5s': {'camera_main': '6400万像素'},
    'ROG 5 Pro': {'camera_main': '6400万像素'},
    'ROG 6': {'camera_main': '5000万像素'},
    'ROG 6 Pro': {'camera_main': '5000万像素'},

    # 联想
    'Moto g100': {'camera_main': '5000万像素'},
    'Moto edge 60 Pro': {'camera_main': '未知'},
    'Moto razr 50 Ultra': {'camera_main': '5000万像素'},
    'Moto S50': {'camera_main': '5000万像素'},
    'Moto razr 60 Ultra': {'camera_main': '未知'},
    'Moto g100 Pro': {'camera_main': '未知'},
    'Moto Razr 50': {'camera_main': '5000万像素'},
    'Moto razr 60': {'storage': '未知', 'ram': '未知', 'camera_main': '未知'},
    'Moto g75': {'camera_main': '未知'},
    'Moto X70 Air': {'camera_main': '未知'},
    'Moto edge s': {'camera_main': '6400万像素'},
    'Moto g54': {'camera_main': '5000万像素'},
}


def main():
    updated_count = 0
    not_found = []

    for model_name, fields in updates.items():
        # 模糊匹配型号
        phone = db.query(Phone).filter(Phone.model.like(f'%{model_name}%')).first()
        if phone:
            for field, value in fields.items():
                setattr(phone, field, value)
            updated_count += 1
        else:
            not_found.append(model_name)

    db.commit()

    print(f'已更新 {updated_count} 条记录')
    if not_found:
        print(f'\n未找到的型号 ({len(not_found)}):')
        for m in not_found[:20]:
            print(f'  - {m}')


if __name__ == '__main__':
    main()

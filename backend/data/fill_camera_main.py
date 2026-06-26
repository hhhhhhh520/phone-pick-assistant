# -*- coding: utf-8 -*-
"""
补充缺失主摄数据 - SUB-004
运行: python -m backend.data.fill_camera_main
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.stdout.reconfigure(encoding='utf-8')

from backend.models.domain import SessionLocal, Phone  # noqa: E402

db = SessionLocal()

# 主摄数据映射 (型号关键词 -> 主摄值)
# 基于官方参数和公开信息
camera_updates = {
    # 已发布机型 - 有确切参数
    'X Fold': '5000万像素',  # vivo X Fold, GN5传感器
    'Find X8s': '5000万像素',  # OPPO Find X8s, LYT700传感器
    'Find X8s+': '5000万像素',  # OPPO Find X8s+, LYT700传感器
    'Galaxy S25 Ultra': '2亿像素',  # 三星 S25 Ultra, HP2传感器
    'Galaxy S24 Ultra': '2亿像素',  # 三星 S24 Ultra, HP2传感器
    'Galaxy S25': '5000万像素',  # 三星 S25
    'Galaxy Z Flip7': '5000万像素',  # 三星 Z Flip7系列
    '畅享90 Pro Max': '1亿像素',  # 华为畅享系列
    'Z9 Turbo 长续航版': '5000万像素',  # iQOO Z9系列
    'Z80 Ultra': '5000万像素',  # 努比亚旗舰系列
    'Xperia 1 VII': '1200万像素',  # 索尼旗舰系列(保持索尼一贯的1200万)

    # 型号名称已包含参数
    '15T前后5000万': '5000万像素',  # 真我型号已标明

    # 未发布/概念机型 - 标记为"待确认"
    'Redmi K90 Pro': '待确认',  # 未发布
    'HUAWEI Mate 80 Pro': '待确认',  # 未发布
    'X Fold5': '待确认',  # 未发布
    'Xperia Pro360': '待确认',  # 特殊型号
}


def main():
    updated_count = 0
    not_found = []
    already_has_data = []

    for keyword, camera_main in camera_updates.items():
        # 模糊匹配型号
        phone = db.query(Phone).filter(Phone.model.like(f'%{keyword}%')).first()
        if phone:
            # 检查是否已有主摄数据
            if phone.camera_main and phone.camera_main not in ['', '无', 'None']:
                already_has_data.append(f'{phone.model}: 已有 {phone.camera_main}')
                continue

            phone.camera_main = camera_main
            updated_count += 1
            print(f'更新: {phone.model} -> {camera_main}')
        else:
            not_found.append(keyword)

    db.commit()

    print('\n=== 补充完成 ===')
    print(f'成功更新: {updated_count} 条')
    print(f'未找到型号: {len(not_found)} 条')
    print(f'已有数据跳过: {len(already_has_data)} 条')

    if not_found:
        print('\n未找到的型号关键词:')
        for m in not_found:
            print(f'  - {m}')

    if already_has_data:
        print('\n已有数据的记录:')
        for m in already_has_data[:10]:
            print(f'  - {m}')


if __name__ == '__main__':
    try:
        main()
    finally:
        db.close()

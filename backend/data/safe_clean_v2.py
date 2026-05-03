"""
安全数据清洗脚本 v2 - 修复版
只做最小化处理，绝不截断型号名称

安全规则:
1. 只移除逗号后的广告文字
2. 只移除括号内的配置参数（精确匹配）
3. 不移除品牌前缀（这是导致之前损坏的原因）
4. 品牌名称统一：HUAWEI → 华为
5. 最小长度保护

用法:
    python safe_clean_v2.py --dry-run  # 仅预览
    python safe_clean_v2.py --apply    # 自动执行
"""

import argparse
import sqlite3
import re
import shutil
from pathlib import Path
from datetime import datetime


def safe_clean_model(model: str) -> tuple[str, list[str]]:
    """
    安全清洗型号名称 - 最小化处理

    只做两件事:
    1. 移除逗号后的广告文字
    2. 移除括号内的配置参数
    """
    changes = []
    original = model

    # 1. 移除中文逗号后的广告文字
    if '，' in model:
        parts = model.split('，')
        model = parts[0].strip()
        changes.append(f"移除中文逗号后内容")

    # 2. 移除英文逗号后的广告文字
    if not changes and ',' in model:
        parts = model.split(',')
        model = parts[0].strip()
        changes.append(f"移除英文逗号后内容")

    # 3. 移除括号内的配置参数 - 精确匹配
    # 只匹配明确的存储配置格式，不匹配其他括号内容
    # 注意：移除括号后，括号后面的文字也会被移除（如果紧邻括号）
    config_patterns = [
        # 复杂格式：（8GB/128GB/全网通/5G版/纪念版）
        r'\s*[（(]\d+GB[/+]\d+GB[/一-龥a-zA-Z0-9/+]+[）)]',
        # 简单格式：（12GB/256GB）5000万像素
        r'\s*[（(]\d+GB[/+]\d+GB[）)][^\s]*',
        r'\s*[（(]\d+GB[/+]\d+TB[）)][^\s]*',
        r'\s*[（(]\d+GB[）)][^\s]*',
        r'\s*[（(]\d+TB[）)][^\s]*',
        # 英文括号
        r'\s*\(\d+GB[/+]\d+GB[/a-zA-Z0-9+]+\)',
        r'\s*\([A-Z]\d+\s+\d+GB/\d+GB\)',  # (S50 12GB/512GB)
    ]

    for pattern in config_patterns:
        if re.search(pattern, model):
            model = re.sub(pattern, '', model).strip()
            changes.append(f"移除配置参数括号")
            break

    # 安全检查: 如果清洗后太短，回退
    if len(model) < 3:
        model = original.split('，')[0].split(',')[0].strip()
        changes.append(f"长度保护触发，回退")

    return model, changes


def safe_clean_brand(brand: str) -> str:
    """统一品牌名称"""
    brand_map = {
        'HUAWEI': '华为',
        'HONOR': '荣耀',
        'VIVO': 'vivo',
        'Xiaomi': '小米',
        'Samsung': '三星',
        'Apple': '苹果',
    }
    return brand_map.get(brand, brand)


def preview_changes(db_path: str) -> list[dict]:
    """预览所有变更"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, brand, model FROM phones ORDER BY id")
    rows = cur.fetchall()
    conn.close()

    changes = []
    for row in rows:
        new_model, model_changes = safe_clean_model(row['model'])
        new_brand = safe_clean_brand(row['brand'])

        if new_model != row['model'] or new_brand != row['brand']:
            changes.append({
                'id': row['id'],
                'old_brand': row['brand'],
                'new_brand': new_brand,
                'old_model': row['model'],
                'new_model': new_model,
                'changes': model_changes,
            })

    return changes


def apply_changes(db_path: str, changes: list[dict], backup: bool = True) -> bool:
    """应用变更"""
    db_file = Path(db_path)

    if backup:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = db_file.parent / f"phones_backup_{timestamp}.db"
        shutil.copy2(db_file, backup_path)
        print(f"已创建备份: {backup_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        conn.execute("BEGIN TRANSACTION")

        for change in changes:
            cur.execute(
                "UPDATE phones SET brand = ?, model = ? WHERE id = ?",
                (change['new_brand'], change['new_model'], change['id'])
            )

        conn.commit()
        print(f"成功更新 {len(changes)} 条记录")
        return True

    except Exception as e:
        conn.rollback()
        print(f"更新失败，已回滚: {e}")
        return False

    finally:
        conn.close()


def verify_results(db_path: str) -> dict:
    """验证清洗结果"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 检查损坏记录
    cur.execute("SELECT COUNT(*) FROM phones WHERE LENGTH(model) <= 5")
    damaged = cur.fetchone()[0]

    # 检查空记录
    cur.execute("SELECT COUNT(*) FROM phones WHERE model IS NULL OR model = ''")
    empty = cur.fetchone()[0]

    # 检查总记录数
    cur.execute("SELECT COUNT(*) FROM phones")
    total = cur.fetchone()[0]

    # 检查HUAWEI品牌
    cur.execute("SELECT COUNT(*) FROM phones WHERE brand = 'HUAWEI'")
    huawei = cur.fetchone()[0]

    # 检查含逗号的型号
    cur.execute("SELECT COUNT(*) FROM phones WHERE model LIKE '%，%' OR model LIKE '%,%'")
    commas = cur.fetchone()[0]

    conn.close()

    return {
        'total': total,
        'damaged': damaged,
        'empty': empty,
        'huawei_brand': huawei,
        'with_commas': commas,
    }


def main():
    parser = argparse.ArgumentParser(description='安全数据清洗脚本 v2')
    parser.add_argument('--apply', action='store_true', help='自动应用变更')
    parser.add_argument('--dry-run', action='store_true', help='仅预览变更')
    args = parser.parse_args()

    db_path = Path(__file__).parent / "phones.db"

    print("=" * 60)
    print("安全数据清洗 v2 - 最小化处理")
    print("=" * 60)

    # 验证当前状态
    print("\n[0] 当前数据状态:")
    before = verify_results(str(db_path))
    print(f"  总记录: {before['total']}")
    print(f"  损坏记录(长度<=5): {before['damaged']}")
    print(f"  HUAWEI品牌: {before['huawei_brand']}")
    print(f"  含逗号型号: {before['with_commas']}")

    # 预览变更
    print("\n[1] 正在分析数据...")
    changes = preview_changes(str(db_path))

    if not changes:
        print("无需更新，数据已干净")
        return

    print(f"\n发现 {len(changes)} 条需要更新的记录")
    print("-" * 60)

    # 显示前20条变更
    for change in changes[:20]:
        print(f"\nID {change['id']}:")
        if change['old_brand'] != change['new_brand']:
            print(f"  品牌: {change['old_brand']} -> {change['new_brand']}")
        print(f"  型号: {change['old_model']}")
        print(f"    ->: {change['new_model']}")

    if len(changes) > 20:
        print(f"\n... 还有 {len(changes) - 20} 条变更")

    # 统计
    brand_changes = sum(1 for c in changes if c['old_brand'] != c['new_brand'])
    print(f"\n变更统计: 品牌 {brand_changes} 条, 型号 {len(changes)} 条")

    if args.dry_run:
        print("\nDRY-RUN 模式: 仅预览")
        return

    if args.apply:
        print("\n[2] 正在应用变更...")
        success = apply_changes(str(db_path), changes)
        if success:
            # 验证结果
            print("\n[3] 验证结果:")
            after = verify_results(str(db_path))
            print(f"  总记录: {after['total']}")
            print(f"  损坏记录: {after['damaged']}")
            print(f"  HUAWEI品牌: {after['huawei_brand']}")
            print(f"  含逗号型号: {after['with_commas']}")

            if after['damaged'] > before['damaged']:
                print("\n⚠️ 警告: 损坏记录增加!")
            else:
                print("\n✅ 清洗完成，无新增损坏")
        return

    # 交互式确认
    response = input("\n确认应用变更? (输入 'yes' 确认): ")
    if response.lower() == 'yes':
        print("\n[2] 正在应用变更...")
        success = apply_changes(str(db_path), changes)
        if success:
            after = verify_results(str(db_path))
            print(f"\n验证: 总记录 {after['total']}, 损坏 {after['damaged']}")


if __name__ == "__main__":
    main()

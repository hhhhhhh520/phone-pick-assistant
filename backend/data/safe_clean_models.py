"""
安全数据清洗脚本 - 执行省实施方案
根据工部尚书方案，仅做最小化处理，不使用关键词截断

安全规则:
1. 不使用关键词截断
2. 最小长度保护 (>=3字符)
3. 事务保护，出错回滚
4. 预览模式，需用户确认

用法:
    python safe_clean_models.py           # 预览模式，需手动确认
    python safe_clean_models.py --apply   # 自动应用变更
    python safe_clean_models.py --dry-run  # 仅预览，不执行
"""

import argparse
import sqlite3
import re
import shutil
from pathlib import Path
from datetime import datetime


def safe_clean_model(model: str) -> tuple[str, list[str]]:
    """
    安全清洗型号名称

    Returns:
        (cleaned_model, list_of_changes)
    """
    changes = []
    original = model

    # 1. 移除中文逗号后的广告文字（优先）
    if '，' in model:
        parts = model.split('，')
        if len(parts) > 1:
            model = parts[0]
            changes.append(f"移除中文逗号后内容: '{'，'.join(parts[1:])}'")

    # 2. 移除英文逗号后的广告文字（如果没中文逗号）
    if not changes and ',' in model:
        parts = model.split(',')
        if len(parts) > 1:
            model = parts[0]
            changes.append(f"移除英文逗号后内容: '{','.join(parts[1:])}'")

    # 3. 移除括号内的配置参数 - 扩展格式匹配
    # 格式列表: (12GB/256GB), (12GB+256GB), (16GB/1TB), (128GB), (S50 12GB/512GB)
    # 以及复杂的中文括号格式如: （8GB/128GB/全网通/5G版）
    config_patterns = [
        r'\(\d+GB[/+]\d+GB[/\d+a-zA-Z一-龥]+\)',  # (12GB/256GB/全网通/5G版)
        r'\(\d+GB[/+]\d+GB\)',      # (12GB/256GB), (12GB+256GB)
        r'\(\d+GB[/+]\d+TB\)',      # (12GB/1TB), (16GB+1TB)
        r'\(\d+GB[/+]\d+[A-Z]+\)',  # (16GB/11B) 错误格式
        r'\(\d+TB[/+]\d+TB\)',      # (1TB/2TB)
        r'\(\d+GB\)',                # (128GB), (256GB)
        r'\(\d+TB\)',                # (1TB), (2TB)
        r'\(\d+T\)',                 # (1T) 简写
        r'\([A-Z]\d+\s+\d+GB/\d+GB\)',  # (S50 12GB/512GB)
        r'\(\d+GB[/+]\d+GB[/一-龥a-zA-Z0-9+]+\)',  # (12GB/256GB/QQ飞车纪念版)
    ]
    for pattern in config_patterns:
        match = re.search(pattern, model)
        if match:
            model = model[:match.start()] + model[match.end():]
            changes.append(f"移除配置参数: '{match.group()}'")
            break

    # 4. 移除中文括号配置 - 包括复杂格式
    cn_config_patterns = [
        r'（\s*\d+GB[/+]\d+GB[/\d+a-zA-Z一-龥]+\s*）',  # （ 8GB+256GB）
        r'（\d+GB[/+]\d+GB[/\d+a-zA-Z一-龥]+）',  # （8GB/128GB/全网通/5G版）
        r'（\d+GB[/+]\d+GB）',     # （8GB/128GB）
        r'（\d+GB[/+]\d+TB）',     # （16GB/1TB）
        r'（\d+TB[/+]\d+TB）',     # （1TB/2TB）
        r'（\d+GB）',              # （256GB）
        r'（\d+TB）',              # （1TB）
        r'（[\d+a-zA-Z一-龥/]+）',  # 通用中文括号匹配
    ]
    for pattern in cn_config_patterns:
        match = re.search(pattern, model)
        if match:
            model = model[:match.start()] + model[match.end():]
            changes.append(f"移除中文配置参数: '{match.group()}'")
            break

    # 5. 品牌前缀处理 - 移除型号中的品牌前缀
    # 注意: 只移除 model 开头的品牌名
    brand_prefixes = ['HUAWEI ', '华为 ', 'HONOR ', '荣耀 ', 'Xiaomi ', '小米 ',
                      'OPPO ', 'vivo ', 'VIVO ', 'Redmi ', 'Samsung ', '三星 ',
                      'Apple ', '苹果 ']
    for prefix in brand_prefixes:
        if model.startswith(prefix) and model != prefix.strip():
            model = model[len(prefix):]
            changes.append(f"移除品牌前缀: '{prefix.strip()}'")
            break

    # 清理多余空格
    model = model.strip()
    while '  ' in model:
        model = model.replace('  ', ' ')

    # 最小长度保护
    if len(model) < 3:
        # 回退: 只移除逗号后内容
        model = original.split('，')[0].split(',')[0]
        changes.append(f"长度保护触发，回退到: '{model}'")

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
    """预览所有变更，返回变更列表"""
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
    """应用变更，带事务保护"""
    db_file = Path(db_path)

    # 备份
    if backup:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = db_file.parent / f"phones_backup_{timestamp}.db"
        shutil.copy2(db_file, backup_path)
        print(f"已创建备份: {backup_path}")

    # 事务更新
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


def main():
    parser = argparse.ArgumentParser(description='安全数据清洗脚本')
    parser.add_argument('--apply', action='store_true', help='自动应用变更（无需确认）')
    parser.add_argument('--dry-run', action='store_true', help='仅预览变更，不执行')
    args = parser.parse_args()

    db_path = Path(__file__).parent / "phones.db"

    print("=" * 60)
    print("安全数据清洗 - 执行省实施方案")
    print("=" * 60)

    # 1. 预览变更
    print("\n[1] 正在分析数据...")
    changes = preview_changes(str(db_path))

    if not changes:
        print("无需更新，数据已干净")
        return

    print(f"\n发现 {len(changes)} 条需要更新的记录:")
    print("-" * 60)

    # 2. 显示变更预览 (限制显示数量)
    max_display = 30
    for i, change in enumerate(changes[:max_display]):
        print(f"\nID {change['id']}:")
        if change['old_brand'] != change['new_brand']:
            print(f"  品牌: {change['old_brand']} -> {change['new_brand']}")
        print(f"  型号: {change['old_model']}")
        print(f"    ->: {change['new_model']}")
        for c in change['changes']:
            print(f"       {c}")

    if len(changes) > max_display:
        print(f"\n... 还有 {len(changes) - max_display} 条变更未显示")

    # 3. 统计变更类型
    print("\n" + "=" * 60)
    print("变更统计:")

    brand_changes = sum(1 for c in changes if c['old_brand'] != c['new_brand'])
    model_changes = len(changes)
    print(f"  - 品牌统一: {brand_changes} 条")
    print(f"  - 型号清洗: {model_changes} 条")

    # 4. 处理不同模式
    print("\n" + "=" * 60)

    if args.dry_run:
        print("DRY-RUN 模式: 仅预览，不执行变更")
        return

    if args.apply:
        print("--apply 模式: 自动应用变更")
        print("\n[2] 正在应用变更...")
        success = apply_changes(str(db_path), changes)
        if success:
            print("\n数据清洗完成!")
        return

    # 交互式确认
    response = input("确认应用以上变更? (输入 'yes' 确认): ")

    if response.lower() == 'yes':
        print("\n[2] 正在应用变更...")
        success = apply_changes(str(db_path), changes)
        if success:
            print("\n数据清洗完成!")
    else:
        print("\n已取消，数据未修改")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理器数据清洗脚本
移除处理器字段中的后缀描述，保留核心型号
"""

import sqlite3
import shutil
import re
import sys
from pathlib import Path

# 设置标准输出编码为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path(__file__).parent / 'phones.db'
BACKUP_PATH = Path(__file__).parent / 'phones_backup_processor_format.db'


def clean_processor(processor: str) -> str:
    """清洗处理器字段，移除后缀描述"""
    if not processor:
        return processor

    original = processor  # noqa: F841 - 保留用于调试对比

    # 移除 "行业最高：xxx" 后缀
    processor = re.sub(r'\s*行业最高[：:].+$', '', processor)

    # 移除 "更多xxx" 后缀
    processor = re.sub(r'\s*更多.+$', '', processor)

    # 移除 "定制版"、"行业版" 后缀（保留空格前的内容）
    processor = re.sub(r'\s*(定制版|行业版)\s*$', '', processor)

    # 清理多余空格
    processor = processor.strip()

    return processor


def main():
    # 1. 备份数据库
    shutil.copy(DB_PATH, BACKUP_PATH)
    print(f'已备份数据库到: {BACKUP_PATH}')

    # 2. 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 3. 查询所有不同的 processor 值
    cursor.execute('SELECT DISTINCT processor FROM phones WHERE processor IS NOT NULL')
    processors = cursor.fetchall()
    print(f'\n共有 {len(processors)} 种不同的处理器值')

    # 4. 显示清洗前的值
    print('\n清洗前的处理器值:')
    for p in processors:
        print(f'  - {p[0]}')

    # 5. 识别需要清洗的记录
    cursor.execute('SELECT id, processor FROM phones WHERE processor IS NOT NULL')
    all_records = cursor.fetchall()

    updates = []
    examples = []

    for record_id, processor in all_records:
        cleaned = clean_processor(processor)
        if cleaned != processor:
            updates.append((cleaned, record_id))
            if len(examples) < 10:  # 保存前10个示例
                examples.append({
                    'id': record_id,
                    'before': processor,
                    'after': cleaned
                })

    # 6. 执行更新
    if updates:
        cursor.executemany('UPDATE phones SET processor = ? WHERE id = ?', updates)
        conn.commit()
        print(f'\n已更新 {len(updates)} 条记录')
    else:
        print('\n没有需要更新的记录')

    # 7. 显示清洗示例
    if examples:
        print('\n清洗前后对比示例:')
        for i, ex in enumerate(examples, 1):
            print(f'  {i}. ID={ex["id"]}')
            print(f'     前: {ex["before"]}')
            print(f'     后: {ex["after"]}')

    # 8. 验证更新结果
    cursor.execute('SELECT DISTINCT processor FROM phones WHERE processor IS NOT NULL')
    new_processors = cursor.fetchall()
    print(f'\n清洗后共有 {len(new_processors)} 种不同的处理器值:')
    for p in new_processors:
        print(f'  - {p[0]}')

    conn.close()
    print('\n数据清洗完成!')


if __name__ == '__main__':
    main()

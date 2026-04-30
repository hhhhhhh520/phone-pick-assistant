"""
数据清洗脚本 - 清洗 demo_phone_data.json
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# 项目根目录
ROOT = Path(__file__).parent.parent
INPUT_FILE = ROOT / "demo_phone_data.json"
OUTPUT_FILE = ROOT / "phones_cleaned.json"


def clean_value(key: str, value: str) -> str:
    """清洗参数值"""
    if not value:
        return value

    # 移除常见噪音
    noise_patterns = [
        r'行业最高[：:][^>＞]+',      # 行业最高：xxx
        r'大于[\d.]+%[^>＞]*',        # 大于78.29%手机内存
        r'行业最高[：:].*?[>＞]',      # 行业最高：xxx＞
        r'纠错',                       # 纠错
        r'查看外观图?[>＞]?',          # 查看外观图>
        r'高清级像素',                  # 高清级像素
        r'普通级像素',                  # 普通级像素
        r'游戏运行良好',                # 游戏运行良好
        r'大电池',                      # 大电池
        r'需双手打字',                  # 需双手打字
        r'2K超清',                      # 2K超清
        r'[>＞]$',                      # 结尾的 > 或 ＞
    ]

    result = value
    for pattern in noise_patterns:
        result = re.sub(pattern, '', result)

    # 根据键类型提取核心值
    if key in ['CPU', '处理器', 'CPU型号']:
        # 提取处理器名称，如 "海思 麒麟9030 Pro"
        match = re.match(r'^([^\s行业]+(?:\s[^\s行业]+)?)', result)
        if match:
            result = match.group(1)

    elif key in ['内存', 'RAM', 'RAM容量']:
        # 提取 GB 数
        match = re.search(r'(\d+)\s*GB', result, re.IGNORECASE)
        if match:
            result = f"{match.group(1)}GB"

    elif key in ['存储', 'ROM', 'ROM容量']:
        # 提取 GB/TB 数
        match = re.search(r'(\d+)\s*(GB|TB)', result, re.IGNORECASE)
        if match:
            result = f"{match.group(1)}{match.group(2).upper()}"

    elif key in ['电池', '电池容量']:
        # 提取 mAh 数
        match = re.search(r'(\d+)\s*mAh', result, re.IGNORECASE)
        if match:
            result = f"{match.group(1)}mAh"

    elif key in ['屏幕', '屏幕尺寸', '主屏尺寸']:
        # 提取英寸数
        match = re.search(r'([\d.]+)\s*英寸', result)
        if match:
            result = f"{match.group(1)}英寸"

    elif key in ['分辨率']:
        # 提取分辨率
        match = re.search(r'(\d+)\s*[x×*]\s*(\d+)\s*px?', result, re.IGNORECASE)
        if match:
            result = f"{match.group(1)}x{match.group(2)}px"

    elif key in ['后置', '前置', '像素']:
        # 提取像素数
        match = re.search(r'(\d+)万?像素', result)
        if match:
            result = f"{match.group(1)}万像素"

    elif key in ['屏幕刷新率', '刷新率']:
        match = re.search(r'(\d+)\s*Hz', result, re.IGNORECASE)
        if match:
            result = f"{match.group(1)}Hz"

    elif key in ['重量']:
        match = re.search(r'(\d+)\s*g', result)
        if match:
            result = f"{match.group(1)}g"

    elif key in ['价格', '电商报价']:
        match = re.search(r'[￥¥]?\s*(\d+)', result)
        if match:
            result = f"￥{match.group(1)}"

    # 清理多余空白和标点
    result = re.sub(r'\s+', ' ', result).strip()
    result = re.sub(r'[>＞，,]+$', '', result)

    # 清理列表中的 > 符号
    result = re.sub(r'[>＞]\s*，?', '，', result)
    result = re.sub(r'，+', '，', result)
    result = result.strip('，')

    return result


def clean_phone(phone: dict) -> dict:
    """清洗单条手机数据"""
    cleaned = {
        'name': phone.get('name', ''),
        'brand': phone.get('brand', ''),
        'price': phone.get('price'),
        'images': phone.get('images', []),
    }

    # 清洗参数
    params = phone.get('params', {})
    cleaned_params = {}

    # 核心参数映射（保留的字段）
    key_mapping = {
        'CPU': 'processor',
        'CPU型号': 'processor',
        '处理器': 'processor',
        '内存': 'ram',
        'RAM': 'ram',
        'RAM容量': 'ram',
        '存储': 'storage',
        'ROM': 'storage',
        'ROM容量': 'storage',
        '电池': 'battery',
        '电池容量': 'battery',
        '屏幕': 'screen_size',
        '屏幕尺寸': 'screen_size',
        '主屏尺寸': 'screen_size',
        '分辨率': 'resolution',
        '屏幕刷新率': 'refresh_rate',
        '刷新率': 'refresh_rate',
        '后置': 'camera_main',
        '前置': 'camera_front',
        '重量': 'weight',
        '操作系统': 'os',
        '上市日期': 'release_date',
        '国内发布时间': 'release_date',
        '机身颜色': 'colors',
        '机身材质': 'material',
        '使用场景': 'use_cases',
    }

    for raw_key, value in params.items():
        # 清洗键名
        clean_key = raw_key.strip()

        # 清洗值
        clean_val = clean_value(clean_key, str(value))

        if clean_val:
            # 如果是核心参数，映射到标准字段
            if clean_key in key_mapping:
                std_key = key_mapping[clean_key]
                cleaned[std_key] = clean_val
            else:
                # 其他参数保留
                cleaned_params[clean_key] = clean_val

    # 保留清洗后的其他参数
    if cleaned_params:
        cleaned['params'] = cleaned_params

    return cleaned


def main():
    print("=" * 60)
    print("数据清洗")
    print("=" * 60)

    # 读取原始数据
    with open(INPUT_FILE, encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f"原始数据: {len(raw_data)} 条")

    # 清洗数据
    cleaned_data = []
    for phone in raw_data:
        cleaned = clean_phone(phone)
        cleaned_data.append(cleaned)

    # 保存清洗后的数据
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    print(f"清洗后: {len(cleaned_data)} 条")
    print(f"输出文件: {OUTPUT_FILE}")

    # 显示示例
    print("\n清洗示例:")
    print("-" * 40)
    sample = cleaned_data[0]
    for k, v in sample.items():
        if v and k != 'params':
            print(f"  {k}: {v}")

    print("\n完成!")


if __name__ == "__main__":
    main()

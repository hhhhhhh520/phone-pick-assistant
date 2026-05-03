# -*- coding: utf-8 -*-
"""清洗型号名称脚本"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
from backend.api.dependencies import get_db
from backend.models.domain import Phone

def clean_model_name(brand, model):
    '''清洗型号名称 - 稳健版本'''
    original = model

    # 1. 移除换行符，统一空格
    model = ' '.join(model.replace('\n', ' ').replace('\r', ' ').split())

    # 2. 移除中文逗号及之后的内容（这是广告语的分隔符）
    if '，' in model:
        model = model.split('，')[0].strip()

    # 3. 移除英文逗号及之后的内容
    if ',' in model:
        model = model.split(',')[0].strip()

    # 4. 移除括号及其内容（配置参数如 12GB/256GB）
    model = re.sub(r'[（(][^）)]*[）)]', '', model).strip()

    # 5. 移除常见品牌前缀（型号不应重复品牌）
    prefixes_to_remove = {
        '苹果': ['苹果', 'Apple（苹果）', 'Apple'],
        '三星': ['三星'],
        '华为': ['华为'],
        '一加': ['一加'],
        '真我': ['真我'],
        '魅族': ['魅族'],
        '努比亚': ['努比亚'],
        '黑鲨': ['黑鲨'],
        '索尼': ['索尼', '索尼移动'],
        'ROG': ['ROG 游戏手机'],
    }

    if brand in prefixes_to_remove:
        for prefix in prefixes_to_remove[brand]:
            if model.startswith(prefix):
                model = model[len(prefix):].strip()
                break

    # Redmi（红米） -> Redmi
    if 'Redmi（红米）' in model:
        model = model.replace('Redmi（红米）', 'Redmi')

    # 6. 使用正则提取型号核心
    patterns = [
        # iPhone 系列
        r'iPhone\s*\d+\s*(Pro|Max|Plus|Mini|Pro Max|Pro Plus)?(?:\s*(Pro|Max|Plus|Mini))?',
        # Galaxy 系列
        r'Galaxy\s*(S|Note|A|Z|W)\s*\d+\s*(Ultra|Plus|Pro|FE)?(?:\s*(Ultra|Plus|Pro|FE))?',
        r'Galaxy\s*(Fold|Flip)\s*\d+\s*(Pro|Plus|Ultra)?',
        # 华为系列
        r'(Mate|P|Pura|nova|畅享)\s*\d+\s*(Pro|Plus|Ultra|Max|Pro Max|非凡大师)?(?:\s*(Pro|Plus|Ultra|Max))?',
        r'Mate\s*X\s*\d+\s*(Pro|Plus|Ultra|非凡大师)?',
        r'nova\s*(Flip|Pro|Ultra)?',
        # 小米/Redmi 系列
        r'小米\s*\d+\s*(Pro|Plus|Ultra|Pro Max|Civi)?',
        r'Redmi\s*(K|Note|Turbo)\s*\d+\s*(Pro|Plus|Ultra|Pro Max|至尊版)?(?:\s*(Pro|Plus|Ultra))?',
        r'Redmi\s*\d+\s*(Pro|Plus|Ultra)?',
        r'MIX\s*(Flip|Fold)?\s*\d*',
        # vivo/iQOO 系列
        r'iQOO\s*(\d+|Neo\d*|Z\d*)\s*(Pro|Plus|Ultra|Turbo|Turbo\+)?(?:\s*(Pro|Plus|Ultra|Turbo))?',
        r'vivo\s*(X|S|Y)\s*\d+\s*(Pro|Plus|Ultra|Fold|Flip)?',
        r'X\s*(Fold|Flip)\s*\d*\s*(Pro|Plus)?',
        # OPPO/一加系列
        r'Ace\s*\d+\s*(Pro|Plus|Ultra|V|至尊版|T)?(?:\s*(V|T))?',
        r'Find\s*(X|N)\s*\d*\s*(Pro|Plus|Ultra|Flip|Fold)?',
        # 真我系列
        r'(GT|Neo)\s*\d*\s*(Pro|Plus|Ultra|大师探索版)?(?:\s*(Pro|Plus|Ultra))?',
        # 魅族系列
        r'魅族\s*\d+\s*(Pro|Plus|Note|Lucky)?(?:\s*(Pro|Plus|Note))?',
        # 努比亚/红魔系列
        r'红魔\s*\d+\s*(Pro|Plus|Ultra|Air|摄影师版|非凡大师)?(?:\s*(Pro|Plus|Ultra))?',
        r'Z\s*\d+\s*(Ultra|Pro|Plus)?',
        r'Flip\s*\d+',
        # ROG系列
        r'ROG\s*\d+\s*(Pro|Plus)?',
        # 黑鲨系列
        r'黑鲨\s*\d+\s*(Pro|Plus|RS|高能版)?(?:\s*(Pro|Plus|RS))?',
        # 索尼系列
        r'Xperia\s*(\d+|PRO-I|5\s*[IV]+|1\s*[IV]+)',
        # Moto系列
        r'Moto\s*(edge|g|razr|S)\s*\d*\s*(Pro|Plus|Ultra|Neo|Air)?(?:\s*(Pro|Plus|Ultra))?',
        r'razr\s*\d+\s*(Ultra|FE)?',
    ]

    matched = None
    for pattern in patterns:
        match = re.search(pattern, model, re.IGNORECASE)
        if match:
            matched = match.group(0).strip()
            break

    if matched and len(matched) >= 3:
        model = matched

    # 7. 如果正则没匹配，尝试关键词截断
    if not matched:
        stop_keywords = [
            '骁龙', '天玑', 'mAh', 'Hz', '像素', '电池', '屏幕', '充电',
            '影像', '散热', '护眼', '电竞', 'W', 'CPU', 'ROM', 'RAM',
            '核心', '英寸', 'mm', 'IP', '旗舰', '至尊', '光显', '矩阵',
            '液冷', '肩键', '触控', '冰川', '泰坦', '星海', '蓝海',
            '东方屏', '珠峰屏', '潜望', '长焦', '主摄', '相机', '拍照',
            '防抖', '防水', '抗摔', '轻薄', '折叠', 'S Pen', 'Bixby',
            'Flyme', '哈苏', '理光', '传感器', '光学', '变焦', 'fps',
            'OIS', 'EIS', 'NFC', '蓝牙', 'WiFi', '5G版', '全网通',
            '移动平台', '处理器', '引擎', '独显', '游戏', '超清', '超光',
            '第五代', '第四代', '第三代', '第二代', '全新', '满血',
            '自研', '全系', '透明', '主动', '风扇', '脉动', '水冷',
            '潘通', '悬浮', '直觉', '交互', '无界', '星轨', '科技',
            '美学', '按键', '天线', '战神', '持久', '流畅', '认证',
            '三防', '品质', '极边', '四曲', '微弧', '大师', '全场景',
            '超声波', '指纹', '解锁', '纯净', '系统', '极窄', '四等',
            '龙晶', '固态', '电解质', '高光', '新国', '全焦段', '光影',
            '猎人', '晓龙', '蓝晶', '技术栈', '万里', '追光', '超核',
            '立体', '无线', '立式', '充电器', '莱茵', 'LCD', 'OLED',
            '光域', 'VC', '超拟人', '智慧', 'AI智享', '超视觉', '装甲',
            '非凡大师', '摄影师版', '暗夜骑士', '冠军版', '限定版',
            'QQ飞车', '高达', '定制', '限量', '万次', '康宁', '防护',
            '湿手', '星轨', '战神', '超级',
        ]

        for kw in stop_keywords:
            idx = model.find(kw)
            if idx > 2:
                model = model[:idx].strip()
                break

    # 8. 清理末尾残留
    model = re.sub(r'\d+万$', '', model)
    model = re.sub(r'全新$', '', model)
    model = model.strip()

    # 9. 如果太短，保守返回
    if len(model) < 2:
        return original.split('，')[0].split(',')[0].strip()

    return model


def main():
    db = next(get_db())
    phones = db.query(Phone).all()

    updated_count = 0
    changes = []

    for p in phones:
        original = p.model
        cleaned = clean_model_name(p.brand, original)

        if cleaned != original:
            changes.append({
                'id': p.id,
                'brand': p.brand,
                'original': original,
                'cleaned': cleaned
            })
            p.model = cleaned
            updated_count += 1

    print(f'总记录数: {len(phones)}')
    print(f'需要更新: {updated_count}')
    print()

    # 显示前20个变更
    print('=== 变更预览 (前20条) ===')
    for c in changes[:20]:
        print(f"ID {c['id']:4d} | {c['brand']:6}")
        print(f"  原始: {c['original'][:60]}")
        print(f"  清洗: {c['cleaned']}")
        print()

    # 确认后提交
    if updated_count > 0:
        confirm = input(f'确认更新 {updated_count} 条记录? (y/n): ')
        if confirm.lower() == 'y':
            db.commit()
            print(f'已更新 {updated_count} 条记录')
        else:
            print('已取消')
            db.rollback()
    else:
        print('无需更新')


if __name__ == '__main__':
    main()

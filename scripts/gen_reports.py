import json, sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('data/antutu_articles/articles.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

os.makedirs('data/phone_reports', exist_ok=True)

def extract_brand(title):
    if 'Redmi' in title or 'POCO' in title: return '小米'
    if 'Mi' in title.upper(): return '小米'
    if 'Honor' in title.upper() or '荣耀' in title: return '华为'
    if 'HUAWEI' in title.upper() or 'Mate' in title.upper(): return '华为'
    if 'OPPO' in title.upper() or 'realme' in title.lower(): return 'OPPO/真我'
    if 'vivo' in title.lower() or 'iQOO' in title.upper(): return 'vivo'
    if 'OnePlus' in title.upper() or '一加' in title: return '一加'
    if '三星' in title: return '三星'
    if 'Sony' in title.upper() or 'Xperia' in title.upper(): return '索尼'
    if 'Google' in title.upper() or 'Pixel' in title.upper(): return '谷歌'
    if 'LG' in title.upper(): return 'LG'
    if 'Motorola' in title.upper() or 'moto' in title.lower(): return '摩托罗拉'
    if 'Nokia' in title.upper() or '诺基亚' in title: return 'HMD Global'
    if 'Nothing' in title.upper(): return 'Nothing'
    if '魅族' in title: return '魅族'
    if '联想' in title: return '联想'
    if '中兴' in title: return '中兴'
    if '努比亚' in title: return '努比亚'
    return ''

def extract_positioning(title, model_name):
    if any(kw in title.upper() for kw in ['Pro', 'Ultra', 'Max', 'Prime']):
        return '高端'
    if any(kw in title.upper() for kw in ['SE', 'Lite', 'mini', '青春版']):
        return '中端'
    if any(kw in title.upper() for kw in ['Ultra', 'Find', 'N']):
        return '旗舰'
    return '中端'

for i in range(min(60, len(data))):
    item = data[i]
    title = item.get('title', '')
    content = item.get('content', '')

    # Extract model from title (last word before space)
    words = title.split()
    model_name = words[-1] if words else ''

    # Clean model name
    model_name = re.sub(r'[^\w一-鿿]', '', model_name)

    brand = extract_brand(title)
    positioning = extract_positioning(title, model_name)

    processor = ''
    screen = ''
    battery = ''
    ram_str = ''
    storage_str = ''
    cameras = ''
    features = []

    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '处理器' in line or '芯片' in line:
            processor = line
        if '屏幕' in line:
            screen = line
        if '电池' in line:
            battery = line
        if '内存' in line or '存储' in line:
            ram_str += line + '\n'
        if any(kw in line for kw in ['主摄', '超广角', '长焦', '前置']):
            cameras = line
        if any(kw in line for kw in ['散热', 'NFC', '红外', '防水', '折叠', '风扇', '一亿像素', '120Hz', '90Hz', '快充']):
            if any(kw in line for kw in ['散热', 'NFC', '红外', '防水', '折叠', '风扇']):
                features.append(line)

    if '+' in ram_str:
        ram_parts = ram_str.split('+')
        ram_str = ram_parts[0].strip()
        storage_str = ram_parts[1].strip() if len(ram_parts) > 1 else ''

    report = f"""# {model_name}

## 基本信息
- **品牌**: {brand}
- **定位**: {positioning}
- **发布时间**: 信息待补充

## 核心配置
| 参数 | 详情 |
|------|------|
| 处理器 | {processor} |
| 屏幕 | {screen} |
| 电池 | {battery} |
| 内存 | {ram_str} {storage_str} |
| 摄像头 | {cameras} |
| 其他 | {', '.join(features)} |

## 产品亮点
- 独特的功能或技术（如独立散热风扇、折叠屏、影像系统等）
- 性价比优势
- 目标用户群体

## 优缺点分析
### 优点
- ...
### 不足
- ...

## 适合人群
- 推荐购买场景/用户画像
"""

    filename = f"data/phone_reports/{model_name}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Done: {model_name}")

print(f"\nTotal: {len(data[:60])} reports generated")

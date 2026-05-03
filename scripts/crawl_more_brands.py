"""
补充爬取：三星、红米、iQOO、真我、魅族、一加、努比亚、Moto
只爬列表页基本信息 + 参数页详情
"""
import requests
from bs4 import BeautifulSoup
import time
import json
import re
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent.parent
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
}

# 要补充的品牌: 名称 -> (品牌ID, 显示名)
TARGET_BRANDS = {
    '三星': ('98', '三星'),
    '红米': ('55731', '红米'),
    'iQOO': ('55075', 'iQOO'),
    '真我': ('55535', '真我'),
    '魅族': ('1434', '魅族'),
    '一加': ('35579', '一加'),
    '努比亚': ('35005', '努比亚'),
    'Moto': ('295', '联想'),  # Moto属于联想
    '索尼': ('1069', '索尼'),
    '谷歌': ('1922', '谷歌'),
    '黑鲨': ('53765', '黑鲨'),
    'ROG': ('41373', 'ROG'),
}

def clean_value(text):
    """清洗参数值 - 去掉营销文案和垃圾字符"""
    if not text:
        return text
    text = text.strip()
    # 移除"纠错"及之后内容
    if '纠错' in text:
        text = text.split('纠错')[0].strip()
    # 移除">" 分隔符
    text = text.replace('>', '，')
    # 截断营销文案分隔符
    for sep in ['行业最高', '大于', '游戏运行', '需双手', '大电池', '高清',
                '手机性能排', '更多', '手机续航', '手机屏幕', '手机内存']:
        if sep in text:
            text = text.split(sep)[0].strip()
    return text

def parse_phone_list(brand_id, brand_name, max_pages=2):
    """爬取品牌列表页，返回手机列表 [{name, url}]"""
    phones = []
    for page in range(1, max_pages + 1):
        url = f'https://detail.zol.com.cn/cell_phone_index/subcate57_{brand_id}_list_{page}.html'
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.encoding = 'gbk'
            if resp.status_code != 200:
                print(f'  {brand_name} 第{page}页: HTTP {resp.status_code}')
                break
        except Exception as e:
            print(f'  {brand_name} 第{page}页: {e}')
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        page_phones = []

        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if 'index' in href and href.endswith('.shtml'):
                name = a.get_text(strip=True) or a.get('title', '')
                if not name or len(name) < 3:
                    continue
                if any(kw in name for kw in ['分', '点评', '对比', '更多', '下一页', '上一页', '首页']):
                    continue
                if not re.search(r'\d', href):  # URL需要包含数字ID
                    continue

                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://detail.zol.com.cn' + href

                page_phones.append({'name': name, 'url': href, 'brand': brand_name})

        # 去重
        seen = set()
        for p in page_phones:
            if p['url'] not in seen:
                seen.add(p['url'])
                phones.append(p)

        print(f'  {brand_name} 第{page}页: {len(page_phones)}款 (去重后累计{len(phones)})')

        if len(page_phones) == 0:
            break
        time.sleep(1)

    return phones

def parse_detail(url, name):
    """解析手机详情页（先找参数页链接，再爬参数）"""
    # Step 1: 访问index页，找参数页链接和价格
    try:
        idx_resp = requests.get(url, headers=HEADERS, timeout=15)
        idx_resp.encoding = 'gbk'
        if idx_resp.status_code != 200:
            return None
    except:
        return None

    idx_soup = BeautifulSoup(idx_resp.text, 'html.parser')

    # 找参数页链接
    param_url = None
    for a in idx_soup.find_all('a', href=True):
        href = a['href']
        if 'param.shtml' in href:
            if href.startswith('/'):
                param_url = 'https://detail.zol.com.cn' + href
            elif href.startswith('//'):
                param_url = 'https:' + href
            else:
                param_url = href
            break

    if not param_url:
        return None

    # 提取价格
    price = None
    for pe in idx_soup.select('.price-type b, .price b, .current-price, .price-value, .product-price'):
        price_match = re.search(r'[\d.]+', pe.get_text(strip=True))
        if price_match:
            try:
                p = int(float(price_match.group()))
                if 500 <= p <= 20000:
                    price = p
                    break
            except:
                pass

    # 提取图片
    images = []
    for img in idx_soup.find_all('img', src=True)[:5]:
        src = img.get('src') or img.get('data-src', '')
        if src and 'http' in src and not any(kw in src.lower() for kw in ['icon', 'logo', 'placeholder']):
            if src.startswith('//'):
                src = 'https:' + src
            images.append(src)

    # Step 2: 访问参数页
    try:
        param_resp = requests.get(param_url, headers=HEADERS, timeout=15)
        param_resp.encoding = 'gbk'
        if param_resp.status_code != 200:
            return {'name': name, 'brand': None, 'price': price, 'params': {}, 'images': images, 'url': url}
    except:
        return {'name': name, 'brand': None, 'price': price, 'params': {}, 'images': images, 'url': url}

    param_soup = BeautifulSoup(param_resp.text, 'html.parser')
    params = {}

    # 解析参数表格
    for row in param_soup.select('tr'):
        th = row.find('th')
        td = row.find('td')
        if th and td:
            key = th.get_text(strip=True)
            value = clean_value(td.get_text(strip=True))
            if key and value and len(key) < 30 and len(value) < 200:
                params[key] = value

    # 如果参数太少，尝试li格式
    if len(params) < 5:
        for li in param_soup.find_all('li'):
            text = li.get_text(strip=True)
            m = re.match(r'([^：:]+)[：:](.+)', text)
            if m:
                key = m.group(1).strip()
                value = clean_value(m.group(2).strip())
                if key and value and len(key) < 30 and len(value) < 200:
                    params[key] = value

    return {
        'name': name,
        'brand': None,  # 由调用者设置
        'price': price,
        'params': params,
        'images': images,
        'url': url,
    }

def import_to_db_simple(phone_data, db_path):
    """简易导入数据库"""
    import sqlite3
    from datetime import datetime

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    brand = phone_data['brand']
    model = phone_data['name']
    price = phone_data.get('price') or 0
    params = phone_data.get('params', {})
    images = phone_data.get('images', [])

    # 从参数提取信息
    processor = params.get('CPU', '') or params.get('处理器', '')
    ram = int(m.group(1)) if (m := re.search(r'(\d+)GB', params.get('RAM', '') or params.get('内存', '') or params.get('运行内存', ''))) else None
    storage = int(m.group(1)) if (m := re.search(r'(\d+)GB', params.get('ROM', '') or params.get('存储', '') or params.get('机身存储', ''))) else None
    battery = int(m.group(1)) if (m := re.search(r'(\d+)mAh', params.get('电池容量', '') or params.get('电池', ''), re.IGNORECASE)) else None
    screen_size = float(m.group(1)) if (m := re.search(r'([\d.]+)英寸', params.get('主屏尺寸', '') or params.get('屏幕尺寸', ''))) else None
    weight = int(m.group(1)) if (m := re.search(r'(\d+)g', params.get('重量', '') or params.get('手机重量', ''))) else None
    refresh = int(m.group(1)) if (m := re.search(r'(\d+)Hz', params.get('屏幕刷新率', '') or '')) else None
    camera_main = int(m.group(1)) if (m := re.search(r'(\d+)万', params.get('后置摄像头', '') or params.get('摄像头', '') or '')) else None
    camera_front = int(m.group(1)) if (m := re.search(r'(\d+)万', params.get('前置摄像头', '') or '')) else None
    charging = int(m.group(1)) if (m := re.search(r'(\d+)w', params.get('有线充电', '') or params.get('快充', '') or '', re.IGNORECASE)) else None

    image_url = images[0] if images else None

    # 检查是否已存在
    cursor.execute("SELECT id FROM phones WHERE model LIKE ? OR (brand=? AND model LIKE ?)",
                   (f"%{model[:20]}%", brand, f"%{model[:20]}%"))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE phones SET brand=?, price=?, processor=?, ram=?, storage=?,
            battery=?, screen_size=?, weight=?, screen_refresh=?,
            camera_main=?, camera_front=?, image_url=?, charging_wired=?, updated_at=?
            WHERE id=?
        """, (brand, price, processor, ram, storage, battery, screen_size,
              weight, refresh, camera_main, camera_front, image_url,
              charging, now, existing[0]))
        conn.commit()
        conn.close()
        return ('updated', existing[0])
    else:
        cursor.execute("""
            INSERT INTO phones (brand, model, price, processor, ram, storage,
            battery, screen_size, weight, screen_refresh, camera_main, camera_front,
            image_url, charging_wired, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (brand, model, price, processor, ram, storage, battery, screen_size,
              weight, refresh, camera_main, camera_front, image_url, charging, now, now))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return ('inserted', new_id)


def main():
    print("=" * 60)
    print("补充爬取手机数据")
    print("=" * 60)

    db_path = ROOT / "backend" / "data" / "phones.db"

    total_new, total_updated = 0, 0

    for brand_name, (brand_id, display_name) in TARGET_BRANDS.items():
        print(f"\n{'='*40}")
        print(f"爬取: {brand_name} (ID={brand_id})")
        print(f"{'='*40}")

        # 爬取列表
        phones = parse_phone_list(brand_id, brand_name, max_pages=2)
        print(f"共获取 {len(phones)} 款 {brand_name} 手机")

        if not phones:
            continue

        # 爬取详情（限制每品牌30款）
        detail_count = 0
        for i, phone in enumerate(phones[:30]):
            print(f"  [{i+1}/{min(len(phones), 30)}] {phone['name'][:30]}...", end=' ')
            time.sleep(0.8)  # 礼貌延时

            detail = parse_detail(phone['url'], phone['name'])
            if detail:
                detail['brand'] = display_name
                action, result_id = import_to_db_simple(detail, db_path)
                if action == 'inserted':
                    total_new += 1
                    print(f'新增 id={result_id}')
                else:
                    total_updated += 1
                    print(f'更新 id={result_id}')
                detail_count += 1
            else:
                print('失败')

    print(f"\n{'='*60}")
    print(f"完成! 新增 {total_new} 款, 更新 {total_updated} 款")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()

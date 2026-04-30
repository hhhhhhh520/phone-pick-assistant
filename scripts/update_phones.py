"""
批量抓取手机数据并更新到数据库
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
import sys
from datetime import datetime

# Windows编码修复
sys.stdout.reconfigure(encoding='utf-8')

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 品牌列表页URL
BRANDS = {
    '华为': 'https://detail.zol.com.cn/cell_phone_index/subcate57_613_list_1.html',
    '苹果': 'https://detail.zol.com.cn/cell_phone_index/subcate57_544_list_1.html',
    '小米': 'https://detail.zol.com.cn/cell_phone_index/subcate57_34645_list_1.html',
    'OPPO': 'https://detail.zol.com.cn/cell_phone_index/subcate57_1673_list_1.html',
    'vivo': 'https://detail.zol.com.cn/cell_phone_index/subcate57_1795_list_1.html',
    '荣耀': 'https://detail.zol.com.cn/cell_phone_index/subcate57_55535_list_1.html',
    '三星': 'https://detail.zol.com.cn/cell_phone_index/subcate57_19_list_1.html',
    '一加': 'https://detail.zol.com.cn/cell_phone_index/subcate57_35579_list_1.html',
}


def clean_param_value(key: str, value: str) -> str:
    """清洗参数值"""
    if not value:
        return value

    stop_words = ['行业最高', '大于', '游戏运行', '需双手', '大电池', '高清']
    for stop_word in stop_words:
        if stop_word in value:
            value = value.split(stop_word)[0].strip()

    if key in ['CPU', '处理器']:
        match = re.match(r'^([^\s行业]+(?:\s[^\s行业]+)*)', value)
        if match:
            value = match.group(1)
    elif key in ['内存', 'RAM']:
        match = re.search(r'(\d+GB)', value)
        if match:
            value = match.group(1)
    elif key in ['电池', '电池容量']:
        match = re.search(r'(\d+mAh)', value, re.IGNORECASE)
        if match:
            value = match.group(1)
    elif key in ['屏幕', '主屏尺寸']:
        match = re.search(r'([\d.]+英寸)', value)
        if match:
            value = match.group(1)
    elif key in ['分辨率']:
        match = re.search(r'(\d+x\d+px?)', value, re.IGNORECASE)
        if match:
            value = match.group(1)
    elif key in ['存储', 'ROM']:
        match = re.search(r'(\d+GB|\d+TB)', value)
        if match:
            value = match.group(1)

    return value.strip()


def get_brand_phones(brand: str, url: str, limit: int = 15) -> list:
    """获取品牌手机列表"""
    phones = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'gbk'

        if response.status_code != 200:
            return phones

        soup = BeautifulSoup(response.text, 'html.parser')
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '')
            if 'index' in href and '.shtml' in href:
                name = link.get_text(strip=True) or link.get('title', '')
                if not name or len(name) < 3:
                    continue
                if any(kw in name for kw in ['分', '点评', '对比', '更多', '下一页', '上一页']):
                    continue

                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://detail.zol.com.cn' + href

                phones.append({'name': name, 'url': href, 'brand': brand})

        # 去重
        seen = set()
        unique = []
        for p in phones:
            if p['name'] not in seen:
                seen.add(p['name'])
                unique.append(p)

        return unique[:limit]

    except Exception as e:
        print(f"  获取{brand}列表失败: {e}")
        return phones


def get_phone_detail(url: str) -> dict:
    """获取手机详情"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'gbk'

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取真实名称
        name = None
        title_elem = soup.select_one('h1.product-name, .pro-name, h1')
        if title_elem:
            name = title_elem.get_text(strip=True)

        # 获取参数
        params = {}
        all_lis = soup.find_all('li')
        for li in all_lis:
            text = li.get_text(strip=True)
            match = re.match(r'([^：:]+)[：:](.+)', text)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                phone_keywords = ['屏幕', '电池', '内存', '存储', '处理器', 'CPU', '摄像头',
                                 '分辨率', '主屏', '核心', 'RAM', 'ROM']
                exclude_keywords = ['发表于', '评论', '赞', '外观', '影像', '续航', '系统', '发货', '流畅', '升级', '设计', '精致']
                if any(kw in key for kw in phone_keywords):
                    if not any(kw in key for kw in exclude_keywords) and len(key) < 20:
                        params[key] = value

        # 清洗参数
        params_cleaned = {k: clean_param_value(k, v) for k, v in params.items()}

        # 获取价格 - 多种选择器
        price = None

        # 方法1: _j_price_num 类（中关村主要价格显示）
        price_elems = soup.select('span._j_price_num, span.m-price._j_price_num')
        for elem in price_elems:
            price_text = elem.get_text(strip=True)
            # 提取数字（去除¥符号）
            price_match = re.search(r'[\d.]+', price_text)
            if price_match:
                price_val = float(price_match.group())
                if 500 <= price_val <= 20000:
                    price = int(price_val)
                    break

        # 方法2: 其他价格选择器
        if not price:
            price_selectors = ['.price-type b', '.price b', '.current-price', '.price-value',
                              'span[class*="price"]', '.product-price']
            for sel in price_selectors:
                price_elem = soup.select_one(sel)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'[\d.]+', price_text)
                    if price_match:
                        price_val = float(price_match.group())
                        if 500 <= price_val <= 20000:
                            price = int(price_val)
                            break

        return {
            'name': name,
            'price': price,
            'params': params_cleaned
        }

    except Exception as e:
        return None


def parse_phone_data(detail: dict, brand: str) -> dict:
    """解析手机数据为数据库格式"""
    params = detail.get('params', {})

    # 解析内存 (GB)
    ram = None
    ram_str = params.get('内存', params.get('RAM', ''))
    if ram_str:
        match = re.search(r'(\d+)', ram_str)
        if match:
            ram = int(match.group(1))

    # 解析电池 (mAh)
    battery = None
    battery_str = params.get('电池', params.get('电池容量', ''))
    if battery_str:
        match = re.search(r'(\d+)', battery_str)
        if match:
            battery = int(match.group(1))

    # 解析屏幕尺寸
    screen_size = None
    screen_str = params.get('屏幕', params.get('主屏尺寸', ''))
    if screen_str:
        match = re.search(r'([\d.]+)', screen_str)
        if match:
            screen_size = float(match.group(1))

    # 解析处理器
    processor = params.get('CPU', params.get('处理器', ''))

    return {
        'brand': brand,
        'model': detail.get('name', ''),
        'price': detail.get('price'),
        'processor': processor,
        'ram': ram,
        'battery': battery,
        'screen_size': screen_size,
        'url': detail.get('url', '')
    }


def main():
    print("=" * 60)
    print("手机数据批量抓取")
    print("=" * 60)

    # 连接数据库
    conn = sqlite3.connect('data/phones.db')
    cursor = conn.cursor()

    all_phones = []

    # 获取各品牌手机列表
    for brand, url in BRANDS.items():
        print(f"\n获取 {brand} 手机列表...")
        phones = get_brand_phones(brand, url, limit=15)
        print(f"  找到 {len(phones)} 款")
        all_phones.extend(phones)
        time.sleep(0.3)

    print(f"\n总共 {len(all_phones)} 款手机待抓取")

    # 抓取详情
    results = []
    for i, phone in enumerate(all_phones, 1):
        print(f"\n[{i}/{len(all_phones)}] {phone['name'][:20]}...")
        time.sleep(0.3)

        detail = get_phone_detail(phone['url'])
        if detail and detail.get('name'):
            detail['url'] = phone['url']
            phone_data = parse_phone_data(detail, phone['brand'])
            results.append(phone_data)
            print(f"  成功: {phone_data['model'][:20]} | {phone_data['price']}元")

    print(f"\n成功抓取 {len(results)} 款手机")

    # 更新数据库
    if results:
        print("\n更新数据库...")
        updated = 0
        inserted = 0

        for phone in results:
            if not phone['model']:
                continue

            # 检查是否已存在
            cursor.execute(
                "SELECT id FROM phones WHERE model LIKE ?",
                (f"%{phone['model'][:20]}%",)
            )
            existing = cursor.fetchone()

            if existing:
                # 更新（只更新非空字段）
                update_fields = []
                update_values = []
                if phone['price']:
                    update_fields.append("price = ?")
                    update_values.append(phone['price'])
                if phone['processor']:
                    update_fields.append("processor = ?")
                    update_values.append(phone['processor'])
                if phone['ram']:
                    update_fields.append("ram = ?")
                    update_values.append(phone['ram'])
                if phone['battery']:
                    update_fields.append("battery = ?")
                    update_values.append(phone['battery'])
                if phone['screen_size']:
                    update_fields.append("screen_size = ?")
                    update_values.append(phone['screen_size'])
                if phone['url']:
                    update_fields.append("url = ?")
                    update_values.append(phone['url'])
                update_fields.append("updated_at = ?")
                update_values.append(datetime.now().isoformat())
                update_values.append(existing[0])

                cursor.execute(f"""
                    UPDATE phones SET {', '.join(update_fields)}
                    WHERE id = ?
                """, update_values)
                updated += 1
            else:
                # 插入（价格可以为空）
                cursor.execute("""
                    INSERT INTO phones (brand, model, price, processor, ram, battery, screen_size, url, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    phone['brand'],
                    phone['model'],
                    phone['price'] or 0,  # 默认0
                    phone['processor'],
                    phone['ram'],
                    phone['battery'],
                    phone['screen_size'],
                    phone['url'],
                    datetime.now().isoformat()
                ))
                inserted += 1

        conn.commit()
        print(f"  更新: {updated} 条")
        print(f"  新增: {inserted} 条")

        # 统计
        cursor.execute("SELECT COUNT(*) FROM phones")
        total = cursor.fetchone()[0]
        print(f"  数据库总计: {total} 款手机")

    conn.close()
    print("\n完成!")


if __name__ == "__main__":
    main()

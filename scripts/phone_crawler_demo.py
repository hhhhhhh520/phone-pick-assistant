"""
手机数据爬虫 Demo - 中关村在线
测试反爬机制和数据抓取可行性
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
import sys
import os
from pathlib import Path

# Windows编码修复
sys.stdout.reconfigure(encoding='utf-8')

# 请求头，模拟浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}


def clean_param_value(key: str, value: str) -> str:
    """
    清洗参数值，去除营销文案

    Args:
        key: 参数名（如 "CPU"、"内存"）
        value: 原始参数值

    Returns:
        清洗后的参数值
    """
    if not value:
        return value

    # 通用清洗：移除"行业最高"、"大于XX%"等营销文案
    # 这些文案通常出现在参数值后面
    stop_words = ['行业最高', '大于', '游戏运行', '需双手', '大电池', '高清']

    for stop_word in stop_words:
        if stop_word in value:
            value = value.split(stop_word)[0].strip()

    # 针对特定参数的清洗规则
    if key in ['CPU', '处理器']:
        # CPU: "海思 麒麟 9030S行业最高：骁龙8至尊版" -> "海思 麒麟 9030S"
        match = re.match(r'^([^\s行业]+(?:\s[^\s行业]+)*)', value)
        if match:
            value = match.group(1)

    elif key in ['内存', 'RAM']:
        # 内存: "16GB游戏运行良好大于98.07%手机内存行业最高：24G＞" -> "16GB"
        match = re.search(r'(\d+GB)', value)
        if match:
            value = match.group(1)

    elif key in ['电池']:
        # 电池: "6000mAh大电池大于83.65%手机续航行业最高：10200mAh" -> "6000mAh"
        match = re.search(r'(\d+mAh)', value, re.IGNORECASE)
        if match:
            value = match.group(1)

    elif key in ['屏幕']:
        # 屏幕: "6.6英寸需双手打字大于32.06%手机屏幕尺寸行业最高：10.19英寸＞" -> "6.6英寸"
        match = re.search(r'([\d.]+英寸)', value)
        if match:
            value = match.group(1)

    elif key in ['分辨率']:
        # 分辨率: "2760x1256px1080P高清大于69.99%手机分辨率行业最高：3840*2160＞" -> "2760x1256px"
        match = re.search(r'(\d+x\d+px?)', value, re.IGNORECASE)
        if match:
            value = match.group(1)

    elif key in ['存储', 'ROM']:
        # 存储: "256GB大于XX%" -> "256GB"
        match = re.search(r'(\d+GB|\d+TB)', value)
        if match:
            value = match.group(1)

    elif key in ['摄像头', '像素', '后置摄像头', '前置摄像头']:
        # 摄像头: "5000万像素" -> "5000万像素"
        match = re.search(r'(\d+万像素|\d+MP)', value)
        if match:
            value = match.group(1)

    elif key in ['重量']:
        # 重量: "189g大于XX%" -> "189g"
        match = re.search(r'(\d+g)', value)
        if match:
            value = match.group(1)

    elif key in ['价格']:
        # 价格已经是数字，不需要清洗
        pass

    return value.strip()


def clean_params(params: dict) -> dict:
    """
    清洗所有参数

    Args:
        params: 原始参数字典

    Returns:
        清洗后的参数字典
    """
    cleaned = {}
    for key, value in params.items():
        cleaned[key] = clean_param_value(key, value)
    return cleaned

def test_access():
    """测试网站访问"""
    print("=" * 50)
    print("测试1: 访问中关村在线手机频道")
    print("=" * 50)

    url = "https://mobile.zol.com.cn/"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应大小: {len(response.text)} 字符")

        if response.status_code == 200:
            print("✅ 访问成功")
            return True
        else:
            print("❌ 访问失败")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def get_phone_list():
    """获取手机列表"""
    print("\n" + "=" * 50)
    print("测试2: 获取手机列表页")
    print("=" * 50)

    # 从各品牌列表页获取手机
    # 注意：部分品牌页面有反爬限制，只爬第1页
    brands = {
        '华为': 'https://detail.zol.com.cn/cell_phone_index/subcate57_613_list_1.html',
        '苹果': 'https://detail.zol.com.cn/cell_phone_index/subcate57_544_list_1.html',
        '小米': 'https://detail.zol.com.cn/cell_phone_index/subcate57_34645_list_1.html',
        'OPPO': 'https://detail.zol.com.cn/cell_phone_index/subcate57_1673_list_1.html',
        'vivo': 'https://detail.zol.com.cn/cell_phone_index/subcate57_1795_list_1.html',
        '荣耀': 'https://detail.zol.com.cn/cell_phone_index/subcate57_55535_list_1.html',
    }

    all_phones = []

    for brand, url in brands.items():
        print(f"\n获取 {brand} 手机列表...")
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.encoding = 'gbk'

            if response.status_code != 200:
                print(f"  {brand} 列页获取失败")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            phones = parse_brand_list(soup, brand)
            all_phones.extend(phones)
            print(f"  找到 {len(phones)} 款 {brand} 手机")

            time.sleep(0.5)  # 礼貌延时

        except Exception as e:
            print(f"  {brand} 解析异常: {e}")

    print(f"\n总共找到 {len(all_phones)} 款手机")
    return all_phones


def parse_brand_list(soup, brand):
    """解析品牌列表页，获取手机名称和URL"""
    phones = []

    # 查找所有手机链接
    all_links = soup.find_all('a', href=True)

    for link in all_links:
        href = link.get('href', '')

        # 匹配手机详情页URL: index数字.shtml
        if 'index' in href and '.shtml' in href:
            # 提取手机名称
            name = link.get_text(strip=True) or link.get('title', '')

            # 过滤无效名称
            if not name or len(name) < 3:
                continue
            if any(kw in name for kw in ['分', '点评', '对比', '更多', '下一页', '上一页']):
                continue

            # 构建完整URL
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://detail.zol.com.cn' + href

            phones.append({
                'name': name,
                'url': href,
                'brand': brand
            })

    # 去重
    seen = set()
    unique_phones = []
    for p in phones:
        if p['name'] not in seen:
            seen.add(p['name'])
            unique_phones.append(p)

    return unique_phones[:60]  # 每个品牌取前60款


def parse_zol_list(soup):
    """解析中关村列表页"""
    phones = []

    # 中关村产品库结构
    products = soup.select('.list-item, .product-item')
    print(f"找到产品容器: {len(products)} 个")

    for item in products:
        name_elem = item.select_one('.pro-name a, .name a, h3 a, a[href*="param"]')
        if name_elem:
            name = name_elem.get_text(strip=True)
            href = name_elem.get('href', '')

            if name and href and len(name) > 3:
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://detail.zol.com.cn' + href

                phones.append({'name': name, 'url': href})

    # 如果没找到，尝试其他选择器
    if not phones:
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            name = link.get_text(strip=True)

            # 匹配参数页
            if 'param.shtml' in href and name and len(name) > 5:
                if '分' not in name and '点评' not in name and '对比' not in name:
                    if href.startswith('//'):
                        href = 'https:' + href
                    phones.append({'name': name, 'url': href})

    # 去重
    seen = set()
    unique_phones = []
    for p in phones:
        if p['name'] not in seen:
            seen.add(p['name'])
            unique_phones.append(p)

    print(f"解析到手机: {len(unique_phones)} 款")
    for i, p in enumerate(unique_phones[:10], 1):
        print(f"  {i}. {p['name']}")

    return unique_phones[:20]


def parse_pconline_list(soup):
    """解析太平洋电脑网列表页"""
    phones = []

    products = soup.select('.item, .product-item, li[class*="product"]')
    print(f"太平洋找到产品: {len(products)} 个")

    for item in products:
        name_elem = item.select_one('a[href*="product"], .name a, h3 a')
        if name_elem:
            name = name_elem.get_text(strip=True)
            href = name_elem.get('href', '')

            if name and href and len(name) > 3:
                phones.append({'name': name, 'url': href})

    print(f"解析到手机: {len(phones)} 款")
    return phones[:20]


def get_phone_detail(url, name):
    """获取手机详情页数据"""
    print(f"\n{'=' * 50}")
    print(f"测试3: 获取手机详情 - {name}")
    print(f"URL: {url}")
    print("=" * 50)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        # 处理GBK编码
        response.encoding = 'gbk'
        print(f"状态码: {response.status_code}")

        if response.status_code != 200:
            print("获取失败")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # 从页面标题获取真实手机名称
        title_elem = soup.select_one('h1.product-name, .pro-name, h1')
        if title_elem:
            real_name = title_elem.get_text(strip=True)
            if real_name and len(real_name) > 2:
                name = real_name
                print(f"  真实名称: {name}")

        # 从真实名称提取品牌
        brand_from_name = None
        brand_keywords = ['华为', 'HUAWEI', '苹果', 'iPhone', '小米', 'Redmi', 'OPPO', 'vivo',
                          '荣耀', 'Honor', '三星', 'Samsung', '一加', 'OnePlus', 'realme',
                          '魅族', '努比亚', '中兴', '联想', '摩托罗拉', '诺基亚']
        for kw in brand_keywords:
            if kw.lower() in name.lower():
                brand_from_name = kw
                break

        # 提取参数 - 中关村index页面结构
        params = {}

        # 方法1: 查找参数模块
        param_module = soup.select_one('.product-param, .param-list, #param-list')
        if param_module:
            items = param_module.select('li, .param-item')
            for item in items:
                text = item.get_text(strip=True)
                if '：' in text or ':' in text:
                    parts = re.split(r'[：:]', text, 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key and value and len(key) < 30:
                            params[key] = value

        # 方法2: 查找表格参数
        if len(params) < 5:
            tables = soup.select('.param-table, table[class*="param"]')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        key = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        if key and value and len(key) < 30:
                            params[key] = value

        # 方法3: 查找所有带参数的li
        if len(params) < 5:
            all_lis = soup.find_all('li')
            for li in all_lis:
                text = li.get_text(strip=True)
                # 匹配 "参数名：参数值" 格式
                match = re.match(r'([^：:]+)[：:](.+)', text)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()

                    # 过滤无效参数
                    # 1. 只保留手机相关参数
                    phone_keywords = ['屏幕', '电池', '内存', '存储', '处理器', 'CPU', '摄像头',
                                     '系统', '网络', '尺寸', '重量', '分辨率', 'SIM', 'NFC',
                                     '快充', '像素', '主屏', '核心', 'RAM', 'ROM', '后置',
                                     '前置', '闪光灯', '光圈', '频段', '蓝牙', 'WiFi',
                                     '操作系统', '机身', '厚度', '宽度', '高度', '容量',
                                     '充电', '无线充电', '防水', '防尘', '刷新率', '触控',
                                     '材质', '类型', 'GPU', '核数', '运行内存', '机身存储',
                                     '频段', '屏占比', 'HDR', '对比度', '马达', '传感器',
                                     '音频', '视频', '扬声器', '振动', '感应器', '定位',
                                     '导航', '红外', '陀螺仪', '气压', '指南针', '霍尔',
                                     '色温', '距离', '光线', '重力', '指纹', '面部',
                                     '识别', '三防', '防水', '防尘', 'IP', '上市', '发布',
                                     '型号', '颜色', '包装', '清单', '保修', '质保', '客服',
                                     'WLAN', 'GPS', '北斗', 'GLONASS', 'Galileo']
                    # 2. 排除评论、日期等无关内容
                    exclude_keywords = ['发表于', '评论', '赞', '外观', '影像', '续航', '系统',
                                       '发货', '流畅', '升级', '设计', '精致']

                    if any(kw in key for kw in phone_keywords):
                        if not any(kw in key for kw in exclude_keywords) and len(key) < 20:
                            params[key] = value

        # 方法4: 从参数详情页链接获取更完整参数
        # 始终尝试访问参数页，获取更完整数据
        param_link = soup.select_one('a[href*="param"]')
        if not param_link:
            # 尝试从URL推断参数页地址
            if 'index' in url:
                param_url = url.replace('index', 'param')
            else:
                param_url = None
        else:
            param_url = param_link.get('href', '')

        if param_url:
            if param_url.startswith('//'):
                param_url = 'https:' + param_url
            elif param_url.startswith('/'):
                param_url = 'https://detail.zol.com.cn' + param_url

            try:
                param_resp = requests.get(param_url, headers=HEADERS, timeout=10)
                param_resp.encoding = 'gbk'
                if param_resp.status_code == 200:
                    param_soup = BeautifulSoup(param_resp.text, 'html.parser')

                    # 解析参数表格
                    param_rows = param_soup.select('tr, .param-item, li[class*="param"]')
                    for row in param_rows:
                        th = row.find('th') or row.find('dt') or row.find('span', class_='name')
                        td = row.find('td') or row.find('dd') or row.find('span', class_='value')
                        if th and td:
                            key = th.get_text(strip=True)
                            value = td.get_text(strip=True)
                            if key and value and len(key) < 20 and len(value) < 200:
                                # 清洗参数值
                                if key not in params:
                                    params[key] = clean_param_value(key, value)
            except Exception:
                pass  # 参数页获取失败不影响主流程

        # 提取价格 - 改进逻辑，避免抓取错误数据
        price = None
        price_selectors = [
            '.price-type b', '.price b', '.current-price', '.price-value',
            'span[class*="price"]', '.product-price'
        ]
        for sel in price_selectors:
            price_elem = soup.select_one(sel)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d.]+', price_text)
                if price_match:
                    price_val = float(price_match.group())
                    # 价格合理性检查：手机价格应在500-20000之间
                    if 500 <= price_val <= 20000:
                        price = price_val
                        break

        # 提取图片 - 改进选择器
        images = []

        # 方法1: 查找主图区域
        main_img_selectors = [
            '.main-pic img', '.product-img img', '.preview-img img',
            '.phone-img img', '.detail-img img', '#mainImg',
            'img.main-img', 'img.product-image'
        ]
        for sel in main_img_selectors:
            img_tags = soup.select(sel)
            for img in img_tags[:3]:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://detail.zol.com.cn' + src
                    if 'http' in src and 'placeholder' not in src.lower():
                        images.append(src)
            if images:
                break

        # 方法2: 查找所有产品相关图片
        if not images:
            all_imgs = soup.find_all('img')
            for img in all_imgs:
                src = img.get('src') or img.get('data-src') or img.get('data-original') or ''
                alt = img.get('alt', '') or img.get('title', '')

                # 过滤：包含手机名称或产品相关关键词
                is_product_img = (
                    name in alt or
                    any(kw in src.lower() for kw in ['product', 'phone', 'mobile', 'cell_phone']) or
                    'detail.zol.com.cn' in src or
                    'pro-pic' in src.lower()
                )

                # 排除：小图标、占位符、广告
                is_excluded = any(kw in src.lower() for kw in ['icon', 'logo', 'placeholder', 'loading', 'ad.', 'banner'])

                if src and is_product_img and not is_excluded:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://detail.zol.com.cn' + src
                    if 'http' in src:
                        images.append(src)

        # 去重
        images = list(dict.fromkeys(images))[:5]

        result = {
            'name': name,
            'brand': brand_from_name,  # 从名称提取的品牌
            'price': price,
            'images': images,
            'params': params,
            'params_cleaned': clean_params(params)  # 添加清洗后的参数
        }

        print(f"解析成功")
        print(f"  品牌: {brand_from_name or '未识别'}")
        print(f"  价格: {price} 元" if price else "  价格: 未找到")
        print(f"  图片: {len(images)} 张")
        print(f"  参数: {len(params)} 项")

        # 显示清洗前后的对比
        if params:
            print("  原始参数:")
            for key, value in list(params.items())[:5]:
                print(f"    - {key}: {value[:40]}...")
            print("  清洗后参数:")
            for key, value in list(result['params_cleaned'].items())[:5]:
                print(f"    - {key}: {value}")

        return result

    except Exception as e:
        print(f"解析异常: {e}")
        return None


def download_images(results, output_dir='images'):
    """
    下载手机图片到本地

    Args:
        results: 手机数据列表
        output_dir: 图片输出目录

    Returns:
        更新后的手机数据列表（图片路径改为本地路径）
    """
    print("\n" + "=" * 50)
    print("下载图片到本地")
    print("=" * 50)

    # 创建输出目录
    img_dir = Path(output_dir)
    img_dir.mkdir(exist_ok=True)

    updated_results = []
    total_downloaded = 0
    total_failed = 0

    for phone in results:
        name = phone['name']
        # 清理文件名中的非法字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '', name)
        safe_name = safe_name[:50]  # 限制长度

        local_images = []

        for i, img_url in enumerate(phone.get('images', []), 1):
            # 只下载第一张主图
            if i > 1:
                break
            # 生成本地文件名
            ext = '.jpg'  # 默认扩展名
            if '.png' in img_url.lower():
                ext = '.png'
            elif '.webp' in img_url.lower():
                ext = '.webp'

            local_filename = f"{safe_name}_{i}{ext}"
            local_path = img_dir / local_filename

            try:
                print(f"  下载: {safe_name} 图片{i}...", end=' ')
                response = requests.get(img_url, headers=HEADERS, timeout=15)

                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    local_images.append(str(local_path))
                    total_downloaded += 1
                    print("✅")
                else:
                    print(f"❌ (状态码: {response.status_code})")
                    total_failed += 1

                time.sleep(0.3)  # 礼貌延时

            except Exception as e:
                print(f"❌ ({e})")
                total_failed += 1

        # 更新手机数据
        phone_copy = phone.copy()
        phone_copy['images'] = local_images
        phone_copy['images_local'] = True
        updated_results.append(phone_copy)

    print(f"\n下载完成: 成功 {total_downloaded} 张, 失败 {total_failed} 张")
    return updated_results


def main():
    print("手机数据爬虫测试")
    print("目标: 中关村在线 (mobile.zol.com.cn)")
    print()

    # 测试1: 基础访问
    if not test_access():
        print("\n无法访问网站，可能需要代理")
        return

    time.sleep(1)  # 礼貌延时

    # 测试2: 从品牌列表页获取手机
    phones = get_phone_list()

    if not phones:
        print("\n未能获取手机列表")
        return

    # 测试3: 抓取手机详情（按URL去重）
    print("\n" + "=" * 50)
    print("测试3: 抓取手机详情")
    print("=" * 50)

    # 按URL去重
    seen_urls = set()
    unique_phones = []
    for phone in phones:
        url = phone['url']
        if url not in seen_urls:
            seen_urls.add(url)
            unique_phones.append(phone)

    print(f"去重后: {len(unique_phones)} 款手机")

    # 限制抓取数量
    test_phones = unique_phones[:300]  # 抓取300款手机

    results = []
    seen_names = set()  # 再次按名称去重（防止同一手机不同URL）

    for i, phone in enumerate(test_phones, 1):
        print(f"\n[{i}/{len(test_phones)}] {phone['name']} (列表页品牌: {phone['brand']})")
        time.sleep(0.5)
        detail = get_phone_detail(phone['url'], phone['name'])
        if detail:
            # 按名称去重
            if detail['name'] in seen_names:
                print(f"  跳过重复: {detail['name']}")
                continue
            seen_names.add(detail['name'])

            # 使用从详情页提取的品牌，如果提取失败则使用列表页品牌
            if not detail.get('brand'):
                detail['brand'] = phone['brand']
            results.append(detail)

    if results:
        print("\n" + "=" * 50)
        print("测试结果汇总")
        print("=" * 50)
        print(f"成功抓取: {len(results)} 款手机")

        # 显示结果表格
        print("\n| 手机 | 品牌 | 价格 | 参数 |")
        print("|------|------|------|------|")
        for r in results:
            price_str = f"{r['price']}元" if r['price'] else "未找到"
            print(f"| {r['name'][:15]} | {r.get('brand', '-')} | {price_str} | {len(r['params'])}项 |")

        # 下载图片到本地
        results = download_images(results, output_dir='images')

        # 保存数据
        with open('demo_phone_data.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n数据已保存到 demo_phone_data.json")
    else:
        print("\n抓取失败")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
安兔兔跑分文章爬虫
从 antutu_urls.txt 读取URL，爬取文章内容并保存到 JSON 文件
"""

import asyncio
import aiohttp
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any

# 配置
URLS_FILE = "antutu_urls.txt"
OUTPUT_DIR = Path("data/antutu_articles")
TIMEOUT = 30  # 秒
RATE_LIMIT = 2  # 每秒请求数

# 中文字体设置（Windows）
try:
    import matplotlib.font_manager as fm
    if 'Microsoft YaHei' in [f.name for f in fm.fontManager.ttflist]:
        CN_FONT = 'Microsoft YaHei'
    elif 'SimHei' in [f.name for f in fm.fontManager.ttflist]:
        CN_FONT = 'SimHei'
    else:
        CN_FONT = None
except:
    CN_FONT = None


def load_urls(filename: str) -> List[str]:
    """加载URL列表"""
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


async def fetch_page(session: aiohttp.ClientSession, url: str, index: int) -> Dict[str, Any]:
    """获取单个页面内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        async with session.get(url, headers=headers, timeout=TIMEOUT) as resp:
            content = await resp.text()

        # 提取标题 - 通常在 <h1> 或 <title> 中
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
        page_title = title_match.group(1).strip() if title_match else ""

        # 清理HTML标签
        def clean_html(text):
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        # 尝试提取正文内容 - 查找主要内容区域
        article_content = extract_article_content(content)

        return {
            'index': index,
            'url': url,
            'status': 'success' if resp.status == 200 else f'HTTP {resp.status}',
            'title': clean_html(page_title),
            'content': article_content,
            'raw_length': len(content)
        }
    except asyncio.TimeoutError:
        return {'index': index, 'url': url, 'status': 'timeout'}
    except Exception as e:
        return {'index': index, 'url': url, 'status': f'error: {str(e)}'}


def extract_article_content(html: str) -> str:
    """提取文章正文内容"""
    # 移除脚本和样式
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

    # 查找所有段落
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)

    if not paragraphs:
        # 尝试其他模式
        paragraphs = re.findall(r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        if not paragraphs:
            paragraphs = re.findall(r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)

    if not paragraphs:
        # 最后手段：提取所有文本块
        text_blocks = re.findall(r'>([^<]{10,200})<', html)
        return '\n'.join(text_blocks[:50])  # 限制长度

    # 清理并合并段落
    cleaned_paragraphs = []
    for p in paragraphs:
        cleaned = re.sub(r'<[^>]+>', '', p)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if len(cleaned) > 20:
            cleaned_paragraphs.append(cleaned)

    return '\n\n'.join(cleaned_paragraphs[:100])  # 限制段落数


async def crawl_all(urls: List[str], output_dir: Path) -> List[Dict[str, Any]]:
    """并发爬取所有URL"""
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    connector = aiohttp.TCPConnector(limit=RATE_LIMIT, limit_per_host=RATE_LIMIT)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_page(session, url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # 过滤掉异常结果
    valid_results = [r for r in results if isinstance(r, dict) and r.get('status') != 'error']

    # 保存结果
    output_file = output_dir / "articles.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(valid_results, f, ensure_ascii=False, indent=2)

    print(f"\n爬取完成！成功: {len(valid_results)}/{len(urls)}")
    print(f"结果已保存到: {output_file}")

    return valid_results


def print_stats(results: List[Dict[str, Any]]):
    """打印统计信息"""
    success = sum(1 for r in results if r.get('status') == 'success')
    timeout = sum(1 for r in results if r.get('status') == 'timeout')
    error = sum(1 for r in results if r.get('status').startswith('error'))

    print(f"\n{'='*60}")
    print(f"统计信息:")
    print(f"  总数: {len(results)}")
    print(f"  成功: {success}")
    print(f"  超时: {timeout}")
    print(f"  错误: {error}")
    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("安兔兔文章爬虫")
    print("=" * 60)

    # 检查URL文件
    if not Path(URLS_FILE).exists():
        print(f"错误: 找不到 {URLS_FILE}")
        return

    # 加载URL
    urls = load_urls(URLS_FILE)
    print(f"加载了 {len(urls)} 个URL")

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 执行爬取
    results = asyncio.run(crawl_all(urls, OUTPUT_DIR))

    # 打印统计
    print_stats(results)

    # 显示示例
    if results:
        print(f"\n示例文章标题: {results[0].get('title', '无标题')}")
        print(f"内容预览: {results[0].get('content', '')[:200]}...")


if __name__ == "__main__":
    main()

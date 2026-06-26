#!/usr/bin/env python3
"""
安兔兔文章爬虫 - 完整版
支持重试、降级策略、并发控制
"""

import asyncio
import aiohttp
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 配置
URLS_FILE = "antutu_urls.txt"
OUTPUT_DIR = Path("data/antutu_articles")
MAX_RETRIES = 3
REQUEST_TIMEOUT = 45
RATE_LIMIT_DELAY = 0.5  # 每次请求间隔（秒）
MAX_CONCURRENT = 5  # 最大并发数


@dataclass
class CrawlResult:
    index: int
    url: str
    status: str  # success, timeout, error, skipped
    title: str = ""
    content: str = ""
    raw_length: int = 0
    retries: int = 0
    error_msg: str = ""


def load_urls(filename: str) -> List[str]:
    """加载URL列表"""
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def extract_article_content(html: str) -> str:
    """提取文章正文内容"""
    # 移除脚本和样式
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

    # 查找段落
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)

    if not paragraphs:
        # 尝试其他容器
        paragraphs = re.findall(r'<div[^>]*class="[^"]*(?:content|article|body|main)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)

    cleaned_paragraphs = []
    for p in paragraphs:
        cleaned = re.sub(r'<[^>]+>', '', p)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if len(cleaned) > 20:
            cleaned_paragraphs.append(cleaned)

    return '\n\n'.join(cleaned_paragraphs[:100])


async def fetch_with_retry(session: aiohttp.ClientSession, url: str, index: int, semaphore: asyncio.Semaphore) -> CrawlResult:
    """带重试的请求"""
    result = CrawlResult(index=index, url=url, status='skipped')

    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                }

                # 随机延迟，避免规律性请求
                if attempt > 0:
                    await asyncio.sleep(0.5 + (attempt * 0.3))

                async with session.get(url, headers=headers, timeout=REQUEST_TIMEOUT) as resp:
                    content = await resp.text()

                # 检查状态码
                if resp.status != 200:
                    result.status = f'HTTP {resp.status}'
                    result.retries = attempt + 1
                    continue

                # 提取标题
                title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
                page_title = clean_html(title_match.group(1)) if title_match else ""

                # 提取内容
                article_content = extract_article_content(content)

                result.status = 'success'
                result.title = page_title
                result.content = article_content
                result.raw_length = len(content)
                result.retries = attempt + 1
                break

            except asyncio.TimeoutError:
                result.status = 'timeout'
                result.retries = attempt + 1
                result.error_msg = 'Timeout'
            except Exception as e:
                result.status = f'error: {str(e)}'
                result.retries = attempt + 1
                result.error_msg = str(e)[:50]

            # 不是最后一次尝试，等待后重试
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)

        # 所有重试都失败，标记为跳过（避免阻塞后续请求）
        if result.status not in ['success', 'HTTP 200']:
            result.status = 'skipped'

    return result


def clean_html(text: str) -> str:
    """清理HTML标签"""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


async def crawl_all(urls: List[str], output_dir: Path) -> List[CrawlResult]:
    """并发爬取所有URL"""
    output_dir.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT,
        limit_per_host=MAX_CONCURRENT,
        ttl_dns_cache=300,
        use_dns_cache=True
    )

    results = []
    start_time = time.time()

    async with aiohttp.ClientSession(connector=connector) as session:
        # 分批创建任务，每批之间有间隔
        batch_size = 20
        for batch_start in range(0, len(urls), batch_size):
            batch_urls = urls[batch_start:batch_start + batch_size]
            print(f"[{batch_start + len(results) + 1}/{len(urls)}] 处理批次 {batch_start // batch_size + 1}...")

            tasks = [fetch_with_retry(session, url, i, semaphore) for i, url in enumerate(batch_urls)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 过滤异常
            for task in batch_results:
                if isinstance(task, Exception):
                    results.append(CrawlResult(index=len(results), url="", status='error', error_msg=str(task)))
                else:
                    results.append(task)

            # 批次间延迟，避免触发反爬
            if batch_start + batch_size < len(urls):
                await asyncio.sleep(2)

    elapsed = time.time() - start_time
    print(f"\n爬取完成！耗时: {elapsed:.1f}秒")

    # 保存结果
    output_file = output_dir / "articles.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([r.__dict__ for r in results], f, ensure_ascii=False, indent=2)

    # 统计
    success = sum(1 for r in results if r.status == 'success')
    timeout = sum(1 for r in results if r.status == 'timeout')
    error = sum(1 for r in results if r.status.startswith('error'))
    skipped = sum(1 for r in results if r.status == 'skipped')

    print(f"\n{'='*60}")
    print(f"统计信息:")
    print(f"  总数: {len(results)}")
    print(f"  成功: {success} ({success/len(results)*100:.1f}%)")
    print(f"  超时: {timeout} ({timeout/len(results)*100:.1f}%)")
    print(f"  错误: {error} ({error/len(results)*100:.1f}%)")
    print(f"  跳过: {skipped} ({skipped/len(results)*100:.1f}%)")
    print(f"  平均重试次数: {sum(r.retries for r in results if r.retries > 0) / max(sum(1 for r in results if r.retries > 0), 1):.1f}")
    print(f"{'='*60}")

    return results


def print_sample(results: List[CrawlResult]):
    """打印示例"""
    success_results = [r for r in results if r.status == 'success']
    if not success_results:
        print("暂无成功获取的文章")
        return

    print(f"\n{'='*60}")
    print(f"示例文章 (共{len(success_results)}篇)")
    print(f"{'='*60}")

    for i, r in enumerate(success_results[:10]):
        print(f"\n--- 文章 {i+1} ---")
        print(f"标题: {r.title[:80]}")
        content = r.content or "(无内容)"
        print(f"内容预览: {content[:300]}..." if len(content) > 300 else f"内容: {content}")


def main():
    print("=" * 60)
    print("安兔兔文章爬虫 - 完整版")
    print("=" * 60)

    if not Path(URLS_FILE).exists():
        print(f"错误: 找不到 {URLS_FILE}")
        return

    urls = load_urls(URLS_FILE)
    print(f"加载了 {len(urls)} 个URL")

    results = asyncio.run(crawl_all(urls, OUTPUT_DIR))
    print_sample(results)


if __name__ == "__main__":
    main()

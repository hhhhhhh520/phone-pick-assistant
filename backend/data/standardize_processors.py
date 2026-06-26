"""
SUB-002: P6 Processor 数据标准化脚本
- 规范化所有 processor 值（剥离品牌前缀、应用别名、统一格式）
- 补充 8 条空值记录
- 验证匹配率 >= 90%
"""
import sys
import os
import sqlite3

# 确保项目路径在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.stdout.reconfigure(encoding="utf-8")

from backend.models.domain import get_canonical_processor, get_antutu_score

DB_PATH = os.path.join(os.path.dirname(__file__), "phones.db")

# ── 8 条空值记录的 processor 补充映射 ──
EMPTY_FILL_MAP = {
    1602: "骁龙8 Gen 2",       # 三星Galaxy Z Flip5
    1605: "麒麟9030S",          # 华为 Pura 90 Pro Max
    1609: "天玑7400",           # 红米 Redmi Note 15 Pro (same model as ID=1203)
    1668: "天玑9400e",          # 一加Turbo 6 风驰版 (天玑中高端)
    1676: "天玑8400-Ultra",     # 一加Turbo 6V (天玑中端)
    1696: "骁龙8 至尊版",       # 努比亚红魔10S Pro+ (model name contains "骁龙8至尊领先版")
    1747: "骁龙8 Gen 2",        # 索尼Xperia Pro360
    1748: "骁龙8 Gen 1",        # 索尼移动Xperia Pro-i
}


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── Step 1: 填充 8 条空值记录 ──
    print("=" * 60)
    print("Step 1: 填充空值 processor 记录")
    print("=" * 60)
    filled = 0
    for pid, processor in EMPTY_FILL_MAP.items():
        # 先用 canonical 形式标准化
        canonical = get_canonical_processor(processor)
        cur.execute(
            "UPDATE phones SET processor = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
            (canonical, pid),
        )
        if cur.rowcount > 0:
            filled += 1
            score = get_antutu_score(canonical)
            print(f"  [OK] ID={pid}: '' -> '{canonical}' (跑分: {score})")
        else:
            print(f"  [SKIP] ID={pid}: 记录不存在")
    print(f"\n空值填充: {filled}/8 条\n")

    # ── Step 2: 标准化所有非空 processor ──
    print("=" * 60)
    print("Step 2: 标准化 processor 值")
    print("=" * 60)
    cur.execute("SELECT id, processor FROM phones WHERE processor IS NOT NULL AND processor != ''")
    rows = cur.fetchall()

    updated = 0
    unchanged = 0
    update_log = []

    for pid, old_val in rows:
        new_val = get_canonical_processor(old_val)
        if new_val != old_val:
            cur.execute(
                "UPDATE phones SET processor = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (new_val, pid),
            )
            updated += 1
            old_score = get_antutu_score(old_val)
            new_score = get_antutu_score(new_val)
            update_log.append((pid, old_val, new_val, old_score, new_score))
        else:
            unchanged += 1

    print(f"标准化更新: {updated} 条")
    print(f"已标准化(无需变更): {unchanged} 条")

    if update_log:
        print("\n变更详情 (前20条):")
        for pid, old, new, old_s, new_s in update_log[:20]:
            match_icon = "[+]" if new_s > 0 and old_s == 0 else "[=]" if new_s == old_s else "[~]"
            print(f"  {match_icon} ID={pid}: '{old}' -> '{new}' (跑分: {old_s} -> {new_s})")
        if len(update_log) > 20:
            print(f"  ... 还有 {len(update_log) - 20} 条变更")

    # 统计有多少记录匹配失败
    cur.execute("SELECT COUNT(*) FROM phones WHERE processor IS NOT NULL AND processor != ''")
    total_nonempty = cur.fetchone()[0]

    matched = 0
    unmatched = []
    cur.execute(
        "SELECT id, brand, model, processor FROM phones "
        "WHERE processor IS NOT NULL AND processor != ''"
    )
    for pid, brand, model, processor in cur.fetchall():
        score = get_antutu_score(processor)
        if score > 0:
            matched += 1
        else:
            unmatched.append((pid, brand, model, processor))

    print("\n" + "=" * 60)
    print("Step 3: 匹配率统计")
    print("=" * 60)
    match_rate_nonempty = matched / total_nonempty * 100 if total_nonempty > 0 else 0
    print(f"总记录数(processor非空): {total_nonempty}")
    print(f"匹配成功: {matched} ({match_rate_nonempty:.1f}%)")
    print(f"匹配失败: {len(unmatched)} ({100 - match_rate_nonempty:.1f}%)")

    if unmatched:
        print(f"\n未匹配的记录 (共 {len(unmatched)} 条):")
        for pid, brand, model, processor in unmatched:
            print(f"  ID={pid} | {brand} {model} | processor='{processor}'")

    # 汇总所有记录（包括最初空的）
    cur.execute("SELECT COUNT(*) FROM phones")
    total_all_records = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM phones WHERE processor IS NULL OR processor = ''")
    still_empty = cur.fetchone()[0]
    overall_match_rate = matched / total_all_records * 100 if total_all_records > 0 else 0
    print(f"\n全部记录: {total_all_records}")
    print(f"仍有空值: {still_empty}")
    print(f"总体匹配率: {matched}/{total_all_records} = {overall_match_rate:.1f}%")

    # ── 验证通过标准 ──
    print("\n" + "=" * 60)
    if match_rate_nonempty >= 90.0:
        print("[PASS] 匹配率 {:.1f}% >= 90%，达标！".format(match_rate_nonempty))
    else:
        print("[FAIL] 匹配率 {:.1f}% < 90%，未达标，需进一步处理。".format(match_rate_nonempty))

    conn.commit()
    conn.close()

    return match_rate_nonempty >= 90.0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""
P7 camera_main 数据清洗与标准化

将 camera_main 字段从 TEXT（如"5000万"、"2亿"、"1.08亿"）转换为 INTEGER（万像素），
同时保持 SQLite 表 schema 中的 camera_main 列类型不变（SQLite 会自动适配）。

运行前提：数据库已备份为 phones_backup_camera_normalize.db
"""
import sqlite3
import re
from typing import Optional


def parse_camera_mp(value) -> Optional[int]:
    """Parse camera_main text to 万pixel integer.

    '5000万' -> 5000, '2亿' -> 20000, '1.08亿' -> 10800
    """
    if value is None:
        return None
    s = str(value).strip()
    # Handle 亿 (hundred million)
    yi_match = re.search(r'([\d.]+)\s*亿', s)
    if yi_match:
        return int(float(yi_match.group(1)) * 10000)
    # Handle 万
    wan_match = re.search(r'([\d.]+)\s*万', s)
    if wan_match:
        return int(float(wan_match.group(1)))
    # Fallback: pure number
    num_match = re.search(r'(\d+)', s)
    if num_match:
        return int(num_match.group(1))
    return None


def main():
    db_path = "D:\\my project\\phone-pick-assistant\\backend\\data\\phones.db"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Read all records
    cur.execute("SELECT id, camera_main FROM phones WHERE camera_main IS NOT NULL AND camera_main != ''")
    rows = cur.fetchall()
    print(f"Found {len(rows)} records with non-empty camera_main")

    if len(rows) == 0:
        print("No records to process. Exiting.")
        conn.close()
        return

    # 2. Show current state
    cur.execute(
        "SELECT camera_main, COUNT(*) as cnt FROM phones "
        "WHERE camera_main IS NOT NULL AND camera_main != '' "
        "GROUP BY camera_main ORDER BY cnt DESC"
    )
    print("\nCurrent camera_main values:")
    for row in cur.fetchall():
        print(f"  '{row['camera_main']}' : {row['cnt']} records")

    # 3. Parse and update
    parsed_count = 0
    parse_errors = []
    updates = []

    for row in rows:
        parsed = parse_camera_mp(row['camera_main'])
        if parsed is not None:
            updates.append((parsed, row['id']))
            parsed_count += 1
        else:
            parse_errors.append((row['id'], row['camera_main']))

    if parse_errors:
        print(f"\nWARNING: {len(parse_errors)} records failed to parse:")
        for eid, evalue in parse_errors:
            print(f"  id={eid}: '{evalue}'")

    # 4. Write back as INTEGER
    for parsed_value, row_id in updates:
        cur.execute("UPDATE phones SET camera_main = ? WHERE id = ?", (parsed_value, row_id))

    conn.commit()
    print(f"\nUpdated {parsed_count} records. {len(parse_errors)} parse errors.")

    # 5. Verify results
    print("\n=== Verification ===")

    # 5a. Check all camera_main values are integers or NULL
    cur.execute("SELECT id, camera_main, typeof(camera_main) FROM phones")
    verify_rows = cur.fetchall()
    non_integer = []
    for vrow in verify_rows:
        val = vrow['camera_main']
        vtype = vrow['typeof(camera_main)']
        if val is not None:
            if vtype not in ('integer', 'int'):
                non_integer.append((vrow['id'], val, vtype))

    if non_integer:
        print(f"FAIL: {len(non_integer)} non-integer camera_main values found:")
        for nid, nval, ntype in non_integer[:10]:
            print(f"  id={nid}: value={nval} type={ntype}")
    else:
        print("PASS: All camera_main values are integer or NULL.")

    # 5b. Show distribution of parsed values
    cur.execute(
        "SELECT camera_main, COUNT(*) as cnt FROM phones "
        "WHERE camera_main IS NOT NULL "
        "GROUP BY camera_main ORDER BY camera_main DESC"
    )
    print("\nParsed camera_main distribution (万像素, descending):")
    for row in cur.fetchall():
        pv = row['camera_main']
        cnt = row['cnt']
        # Human-readable label
        if pv >= 10000:
            label = f"{pv/10000:.2f}亿像素"
        else:
            label = f"{pv}万像素"
        print(f"  {pv:>6} ({label}) : {cnt} records")

    # 5c. Total count check
    cur.execute("SELECT COUNT(*) as cnt FROM phones")
    total = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) as cnt FROM phones WHERE camera_main IS NOT NULL")
    with_value = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) as cnt FROM phones WHERE camera_main IS NULL")
    null_count = cur.fetchone()['cnt']
    print(f"\nTotal records: {total}")
    print(f"With camera_main: {with_value}")
    print(f"NULL camera_main: {null_count}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

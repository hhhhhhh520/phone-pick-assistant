# -*- coding: utf-8 -*-
"""推荐质量对账：LLM 最终选择 vs 全库理论最优（按场景指标）"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

import httpx
import sqlite3

from backend.models.domain import Phone, get_antutu_score
from backend.services.camera_score import camera_scoring_service

BASE = "http://localhost:8002"
conn = sqlite3.connect("backend/data/phones.db")
conn.row_factory = sqlite3.Row


def metric_value(row, metric):
    if metric == "antutu":
        return get_antutu_score(row["processor"] or "")
    if metric == "camera":
        return camera_scoring_service.calc_total_score(Phone(**{c: row[c] for c in row.keys()}))["total"]
    if metric == "battery":
        return row["battery"] or 0
    return 0


def db_top(metric, lo, hi, brand=None, k=5):
    q = "SELECT * FROM phones WHERE price > 0 AND price BETWEEN ? AND ?"
    args = [lo, hi]
    if brand:
        q += " AND brand = ?"
        args.append(brand)
    rows = [r for r in conn.execute(q, args)]
    rows.sort(key=lambda r: metric_value(r, metric), reverse=True)
    return [(f"{r['brand']} {r['model'][:20]}", r["price"], metric_value(r, metric)) for r in rows[:k]]


def chat(client, message, session_id=None):
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    ev, contents = {}, []
    with client.stream("POST", f"{BASE}/api/chat", json=payload, timeout=120) as r:
        for line in r.iter_lines():
            if line.startswith("data:"):
                try:
                    d = json.loads(line[5:])
                except json.JSONDecodeError:
                    continue
                t = d.get("type")
                if t == "content":
                    contents.append(d["data"])
                elif t == "phones":
                    ev["phones"] = d["data"]
                elif t in ("session", "intent", "notice", "question", "error", "done"):
                    ev[t] = d.get("data", "")
    ev["content"] = "".join(contents)
    return ev


SCENARIOS = [
    ("游戏 3000-4000", "预算三千到四千，主要玩游戏，推荐手机", "antutu", (3000, 4000), None),
    ("拍照 3000左右", "预算三千左右，喜欢拍照，推荐手机", "camera", (2500, 3500), None),
    ("续航 ≤2000", "预算两千以内，电池要耐用，推荐手机", "battery", (0, 2000), None),
    ("性能 5000-6000", "预算五六千，要性能最强的旗舰", "antutu", (5000, 6000), None),
    ("红米 ≤2000", "预算两千以内推荐红米手机", "antutu", (0, 2000), "红米"),
]

results = []
with httpx.Client() as c:
    for name, msg, metric, (lo, hi), brand in SCENARIOS:
        ev = chat(c, msg)
        ps = ev.get("phones", [])
        picks = [(f"{p['brand']} {p['model'][:20]}", p["price"]) for p in ps]
        ideal = db_top(metric, lo, hi, brand)
        ideal_names = {n for n, _, _ in ideal}
        # 命中数：LLM 选择 ∩ 全库理论 Top5
        hits = sum(1 for n, _ in picks if n in ideal_names)
        budget_ok = all(lo <= p <= hi for _, p in picks) if picks else False
        print(f"\n【{name}】预算{lo}-{hi} | notice: {ev.get('notice')}")
        print(f"  LLM 推荐: {picks}")
        print(f"  全库{metric}Top5: {ideal}")
        print(f"  预算符合: {'✓' if budget_ok else '✗'} | 命中理论Top5: {hits}/{len(picks)}")
        print(f"  正文摘要: {ev['content'][:120].replace(chr(10), ' ')}…")
        results.append((name, budget_ok, hits, len(picks)))

print("\n" + "=" * 60)
ok_budget = sum(1 for _, b, _, _ in results if b)
total_hits = sum(h for _, _, h, n in results)
total_picks = sum(n for _, _, _, n in results)
print(f"预算符合: {ok_budget}/{len(results)} 场景 | 推荐命中全库Top5: {total_hits}/{total_picks} 款")

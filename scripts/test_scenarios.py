"""
手机选购助手 - 端到端测试场景
"""
import httpx
import json
import time

BASE_URL = "http://localhost:8005"

def test_scene_1():
    """场景 1：模糊需求追问测试"""
    print("\n=== 场景 1：模糊需求追问测试 ===")
    data = {"message": "给我推荐一个手机", "session_id": "test-scene-1"}
    response = httpx.post(f"{BASE_URL}/api/chat", json=data, timeout=30.0)

    if response.status_code != 200:
        print(f"❌ 失败：状态码 {response.status_code}")
        print(f"响应：{response.text[:200]}")
        return False

    # 解析 SSE 流
    lines = response.text.strip().split('\n')
    has_question = False
    for line in lines:
        if line.startswith('data:'):
            try:
                event = json.loads(line[5:])
                if event.get('type') == 'question':
                    has_question = True
                    print(f"✅ 收到追问：{event['data']['question'][:50]}...")
                    print(f"✅ 快捷回复：{event['data']['quick_replies']}")
            except:
                pass

    if has_question:
        print("[PASS] 场景 1 通过")
        return True
    else:
        print("[FAIL] 场景 1 失败：未收到追问")
        return False

def test_scene_2():
    """场景 2：明确预算推荐测试"""
    print("\n=== 场景 2：明确预算推荐测试 ===")
    data = {"message": "2000-3000 元玩游戏", "session_id": "test-scene-2"}
    response = httpx.post(f"{BASE_URL}/api/chat", json=data, timeout=30.0)

    if response.status_code != 200:
        print(f"❌ 失败：状态码 {response.status_code}")
        return False

    # 解析 SSE 流
    lines = response.text.strip().split('\n')
    phones_count = 0
    for line in lines:
        if line.startswith('data:'):
            try:
                event = json.loads(line[5:])
                if event.get('type') == 'phones':
                    phones_count = len(event.get('data', []))
                    prices = [p.get('price', 0) for p in event.get('data', [])]
                    print(f"✅ 收到 {phones_count} 款手机，价格：{prices}")
            except:
                pass

    if 2 <= phones_count <= 5:
        print("[PASS] 场景 2 通过")
        return True
    else:
        print(f"[FAIL] 场景 2 失败：手机数量 {phones_count}")
        return False

def test_scene_3():
    """场景 3：品牌指定推荐测试"""
    print("\n=== 场景 3：品牌指定推荐测试 ===")
    data = {"message": "推荐红米手机", "session_id": "test-scene-3"}
    response = httpx.post(f"{BASE_URL}/api/chat", json=data, timeout=30.0)

    if response.status_code != 200:
        print(f"❌ 失败：状态码 {response.status_code}")
        return False

    # 解析 SSE 流
    lines = response.text.strip().split('\n')
    phones_count = 0
    has_redmi = False
    for line in lines:
        if line.startswith('data:'):
            try:
                event = json.loads(line[5:])
                if event.get('type') == 'phones':
                    phones_count = len(event.get('data', []))
                    brands = [p.get('brand', '') for p in event.get('data', [])]
                    print(f"✅ 收到 {phones_count} 款手机，品牌：{brands}")
                    if '红米' in brands or '小米' in brands:
                        has_redmi = True
            except:
                pass

    if has_redmi:
        print("[PASS] 场景 3 通过")
        return True
    else:
        print(f"[FAIL] 场景 3 失败：未找到红米手机")
        return False

def test_scene_4():
    """场景 4：多轮对话测试"""
    print("\n=== 场景 4：多轮对话测试 ===")

    # 第一轮
    data1 = {"message": "推荐 3000 元手机", "session_id": "test-scene-4"}
    response1 = httpx.post(f"{BASE_URL}/api/chat", json=data1, timeout=30.0)

    if response1.status_code != 200:
        print(f"❌ 第一轮失败：状态码 {response1.status_code}")
        return False

    # 解析第一轮价格
    lines1 = response1.text.strip().split('\n')
    prices1 = []
    for line in lines1:
        if line.startswith('data:'):
            try:
                event = json.loads(line[5:])
                if event.get('type') == 'phones':
                    prices1 = [p.get('price', 0) for p in event.get('data', [])]
                    print(f"✅ 第一轮：价格 {prices1}")
            except:
                pass

    # 第二轮
    data2 = {"message": "有没有便宜点的", "session_id": "test-scene-4"}
    response2 = httpx.post(f"{BASE_URL}/api/chat", json=data2, timeout=30.0)

    if response2.status_code != 200:
        print(f"❌ 第二轮失败：状态码 {response2.status_code}")
        return False

    # 解析第二轮价格
    lines2 = response2.text.strip().split('\n')
    prices2 = []
    for line in lines2:
        if line.startswith('data:'):
            try:
                event = json.loads(line[5:])
                if event.get('type') == 'phones':
                    prices2 = [p.get('price', 0) for p in event.get('data', [])]
                    print(f"✅ 第二轮：价格 {prices2}")
            except:
                pass

    # 检查价格是否降低
    if prices1 and prices2:
        avg1 = sum(prices1) / len(prices1)
        avg2 = sum(prices2) / len(prices2)
        if avg2 < avg1:
            print(f"[PASS] 场景 4 通过：价格从 {avg1:.0f} 降到 {avg2:.0f}")
            return True
        else:
            print(f"[FAIL] 场景 4 失败：价格未降低 ({avg1:.0f} -> {avg2:.0f})")
            return False
    else:
        print("[FAIL] 场景 4 失败：未获取到价格")
        return False

def test_scene_5():
    """场景 5：对比功能测试"""
    print("\n=== 场景 5：对比功能测试 ===")
    data = {"message": "对比小米 14 和华为 P60", "session_id": "test-scene-5"}
    response = httpx.post(f"{BASE_URL}/api/chat", json=data, timeout=30.0)

    if response.status_code != 200:
        print(f"❌ 失败：状态码 {response.status_code}")
        return False

    # 解析 SSE 流
    lines = response.text.strip().split('\n')
    phones_count = 0
    for line in lines:
        if line.startswith('data:'):
            try:
                event = json.loads(line[5:])
                if event.get('type') == 'phones':
                    phones_count = len(event.get('data', []))
                    models = [p.get('model', '') for p in event.get('data', [])]
                    print(f"✅ 收到 {phones_count} 款手机，型号：{models}")
            except:
                pass

    if phones_count >= 2:
        print("[PASS] 场景 5 通过")
        return True
    else:
        print(f"[FAIL] 场景 5 失败：手机数量 {phones_count}")
        return False

def main():
    print("=" * 50)
    print("手机选购助手 - 端到端测试")
    print("=" * 50)

    results = []

    # 等待后端启动
    print("\n等待后端启动...")
    time.sleep(2)

    # 执行测试
    results.append(("场景 1：模糊需求追问", test_scene_1()))
    results.append(("场景 2：明确预算推荐", test_scene_2()))
    results.append(("场景 3：品牌指定推荐", test_scene_3()))
    results.append(("场景 4：多轮对话", test_scene_4()))
    results.append(("场景 5：对比功能", test_scene_5()))

    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")

    print(f"\n总计：{passed}/{total} 通过")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

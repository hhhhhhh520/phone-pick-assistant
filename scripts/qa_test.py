"""QA Test Script for Phone Pick Assistant"""
import requests
import json
import sys

API_BASE = "http://localhost:8002"

def test_scenario_1():
    """Scenario 1: Recommendation with user quote and potential cons"""
    print("\n=== Scenario 1: Recommendation Explanation ===")

    payload = {"message": "预算3000元左右，不玩游戏，推荐一款手机"}
    response = requests.post(f"{API_BASE}/api/chat", json=payload, stream=True, timeout=60)

    full_content = ""
    phones_data = []

    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'content':
                        full_content += data.get('data', '')
                    elif data.get('type') == 'phones':
                        phones_data = data.get('data', [])
                except json.JSONDecodeError:
                    pass

    print(f"Response length: {len(full_content)} chars")
    print(f"Phones returned: {len(phones_data)}")

    # Check for user quote reference
    has_quote_ref = '"' in full_content or '"' in full_content or '需求' in full_content
    print(f"Has user quote reference: {has_quote_ref}")

    # Check for potential cons/shortcomings
    has_cons = '不足' in full_content or '缺点' in full_content or '局限' in full_content or '注意' in full_content
    print(f"Has potential cons: {has_cons}")

    # Print first 500 chars of response
    print(f"\nResponse preview:\n{full_content[:800]}...")

    result = {
        "passed": has_quote_ref and len(phones_data) > 0,
        "has_quote_ref": has_quote_ref,
        "has_cons": has_cons,
        "phones_count": len(phones_data)
    }
    assert has_quote_ref, "推荐回复应引用用户需求"
    assert len(phones_data) > 0, "应返回手机推荐数据"
    return result


def test_scenario_2():
    """Scenario 2: Pain point question trigger"""
    print("\n=== Scenario 2: Pain Point Question ===")

    payload = {"message": "预算2000元，想要游戏性能好的手机"}
    response = requests.post(f"{API_BASE}/api/chat", json=payload, stream=True, timeout=60)

    full_content = ""
    is_question = False
    quick_replies = []
    pain_point_type = None

    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'content':
                        full_content += data.get('data', '')
                    elif data.get('type') == 'question':
                        question_data = data.get('data', {})
                        full_content = question_data.get('question', '')
                        quick_replies = question_data.get('quick_replies', [])
                        pain_point_type = question_data.get('pain_point_type')
                        is_question = True
                except json.JSONDecodeError:
                    pass

    print(f"Is question: {is_question}")
    print(f"Question content: {full_content[:200] if full_content else 'N/A'}")
    print(f"Quick replies: {quick_replies}")
    print(f"Pain point type: {pain_point_type}")

    result = {
        "passed": is_question and len(quick_replies) > 0,
        "is_question": is_question,
        "has_quick_replies": len(quick_replies) > 0,
        "pain_point_type": pain_point_type
    }
    assert is_question, "预算2000元+游戏需求应触发痛点追问"
    assert len(quick_replies) > 0, "追问应包含快捷回复选项"
    return result


def test_scenario_3():
    """Scenario 3: Camera tag filtering"""
    print("\n=== Scenario 3: Camera Tag Filtering ===")

    payload = {"message": "推荐一款拍照好的手机，预算5000元左右"}
    response = requests.post(f"{API_BASE}/api/chat", json=payload, stream=True, timeout=60)

    full_content = ""
    phones_data = []

    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'content':
                        full_content += data.get('data', '')
                    elif data.get('type') == 'phones':
                        phones_data = data.get('data', [])
                except json.JSONDecodeError:
                    pass

    print(f"Phones returned: {len(phones_data)}")

    # Check for camera-related features in phones
    camera_features = ['徕卡', '哈苏', '蔡司', '影像', '潜望', '拍照']
    phones_with_camera_tags = 0

    for phone in phones_data:
        features = phone.get('features', '')
        if features:
            if any(tag in features for tag in camera_features):
                phones_with_camera_tags += 1
                print(f"  - {phone.get('brand')} {phone.get('model')}: {features[:100]}")

    print(f"Phones with camera features: {phones_with_camera_tags}/{len(phones_data)}")

    result = {
        "passed": len(phones_data) > 0,
        "phones_count": len(phones_data),
        "phones_with_camera_tags": phones_with_camera_tags
    }
    assert len(phones_data) > 0, "拍照需求应返回手机推荐"
    assert phones_with_camera_tags > 0, f"返回的手机应包含影像相关特性，实际: {phones_with_camera_tags}/{len(phones_data)}"
    return result


def test_scenario_4():
    """Scenario 4: Frontend UI - simulated via API checks"""
    print("\n=== Scenario 4: UI Component Checks ===")

    # Test 1: Phone card parameters
    response = requests.get(f"{API_BASE}/api/phones?limit=3", timeout=10)
    phones_data = response.json().get('phones', [])

    print(f"Sample phones for UI check:")
    all_have_basic_params = True
    for phone in phones_data:
        has_ram = phone.get('ram') is not None
        has_storage = phone.get('storage') is not None
        has_battery = phone.get('battery') is not None
        print(f"  - {phone.get('brand')} {phone.get('model')}: RAM={has_ram}, Storage={has_storage}, Battery={has_battery}")
        if not (has_ram or has_storage or has_battery):
            all_have_basic_params = False

    # Test 2: Quick reply buttons work
    payload = {"message": "推荐手机"}
    response = requests.post(f"{API_BASE}/api/chat", json=payload, stream=True, timeout=60)

    quick_replies = []
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'question':
                        quick_replies = data.get('data', {}).get('quick_replies', [])
                        break
                except json.JSONDecodeError:
                    pass

    print(f"Quick replies available: {quick_replies}")

    # Test 3: Pain point styling data (already tested in scenario 2)

    result = {
        "passed": all_have_basic_params and len(quick_replies) > 0,
        "all_have_basic_params": all_have_basic_params,
        "quick_replies_available": len(quick_replies) > 0
    }
    assert all_have_basic_params, "手机数据应包含基本参数(RAM/存储/电池)"
    assert len(quick_replies) > 0, "应返回快捷回复选项"
    return result


def test_edge_cases():
    """Test edge cases: empty input, error handling"""
    print("\n=== Edge Cases Testing ===")

    results = {}

    # Test 1: Empty message (should fail validation)
    try:
        response = requests.post(f"{API_BASE}/api/chat", json={"message": ""}, timeout=10)
        results["empty_message_handled"] = response.status_code != 200
        print(f"Empty message handled: {results['empty_message_handled']} (status={response.status_code})")
    except Exception as e:
        results["empty_message_handled"] = True
        print(f"Empty message error: {e}")

    # Test 2: Very long message
    long_msg = "推荐手机" * 100
    try:
        response = requests.post(f"{API_BASE}/api/chat", json={"message": long_msg}, timeout=30)
        results["long_message_handled"] = response.status_code in [200, 400, 422]
        print(f"Long message handled: {results['long_message_handled']}")
    except Exception as e:
        results["long_message_handled"] = False
        print(f"Long message error: {e}")

    # Test 3: Special characters
    try:
        response = requests.post(f"{API_BASE}/api/chat", json={"message": "<script>alert(1)</script>"}, timeout=10)
        results["xss_handled"] = response.status_code in [200, 400]
        print(f"XSS attempt handled: {results['xss_handled']}")
    except Exception as e:
        results["xss_handled"] = False
        print(f"XSS test error: {e}")

    assert results.get("empty_message_handled"), "空消息应被正确拒绝(status != 200)"
    assert results.get("long_message_handled"), "超长消息应被正确处理"
    assert results.get("xss_handled"), "XSS攻击应被正确处理"
    return results


def main():
    print("=" * 60)
    print("Phone Pick Assistant QA Test")
    print("=" * 60)

    results = {}

    try:
        results["scenario_1"] = test_scenario_1()
    except Exception as e:
        print(f"Scenario 1 error: {e}")
        results["scenario_1"] = {"passed": False, "error": str(e)}

    try:
        results["scenario_2"] = test_scenario_2()
    except Exception as e:
        print(f"Scenario 2 error: {e}")
        results["scenario_2"] = {"passed": False, "error": str(e)}

    try:
        results["scenario_3"] = test_scenario_3()
    except Exception as e:
        print(f"Scenario 3 error: {e}")
        results["scenario_3"] = {"passed": False, "error": str(e)}

    try:
        results["scenario_4"] = test_scenario_4()
    except Exception as e:
        print(f"Scenario 4 error: {e}")
        results["scenario_4"] = {"passed": False, "error": str(e)}

    try:
        results["edge_cases"] = test_edge_cases()
    except Exception as e:
        print(f"Edge cases error: {e}")
        results["edge_cases"] = {"passed": False, "error": str(e)}

    # Summary
    print("\n" + "=" * 60)
    print("QA SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for k, v in results.items() if v.get('passed', False))
    total_count = len(results)

    print(f"Passed: {passed_count}/{total_count}")

    for key, value in results.items():
        status = "PASS" if value.get('passed', False) else "FAIL"
        print(f"  {key}: {status}")

    # Generate output
    output = {
        "qa_passed": passed_count == total_count,
        "user_flows": [
            {
                "flow_name": "Scenario 1: Recommendation Explanation",
                "steps": ["Send request with explicit needs", "Check for user quote reference", "Check for potential cons"],
                "passed": results.get("scenario_1", {}).get("passed", False),
                "issues": [] if results.get("scenario_1", {}).get("passed", False) else ["Missing user quote or cons disclosure"]
            },
            {
                "flow_name": "Scenario 2: Pain Point Question",
                "steps": ["Send conflicting budget/need request", "Verify pain point question triggered", "Check quick replies"],
                "passed": results.get("scenario_2", {}).get("passed", False),
                "issues": [] if results.get("scenario_2", {}).get("passed", False) else ["Pain point not triggered properly"]
            },
            {
                "flow_name": "Scenario 3: Camera Tag Filtering",
                "steps": ["Request camera-focused phone", "Check returned phones have camera features"],
                "passed": results.get("scenario_3", {}).get("passed", False),
                "issues": [] if results.get("scenario_3", {}).get("passed", False) else ["No camera-focused phones returned"]
            },
            {
                "flow_name": "Scenario 4: UI Components",
                "steps": ["Check phone parameters", "Verify quick replies available"],
                "passed": results.get("scenario_4", {}).get("passed", False),
                "issues": [] if results.get("scenario_4", {}).get("passed", False) else ["UI components incomplete"]
            }
        ],
        "issues": [],
        "decision": "通过" if passed_count == total_count else "打回"
    }

    print(f"\nDecision: {output['decision']}")

    return output


if __name__ == "__main__":
    result = main()
    print("\n" + json.dumps(result, ensure_ascii=False, indent=2))

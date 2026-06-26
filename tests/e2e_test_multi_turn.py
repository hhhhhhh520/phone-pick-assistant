"""
端到端测试脚本 - 验证多轮对话完整流程

⚠️ 这是手动集成测试脚本，不是 pytest 测试。
运行方式：先启动后端服务，再执行此脚本。

测试场景：
1. 模糊需求触发追问
2. 多轮对话状态累积
3. 明确需求直接推荐
4. 快捷回复交互
"""

import httpx
import json
import asyncio
from typing import Optional

BASE_URL = "http://localhost:8003"


async def stream_chat(message: str, session_id: Optional[str] = None) -> dict:
    """
    发送聊天消息并收集所有 SSE 事件

    Returns:
        dict: 收集的事件数据，包含 session_id, intent, phones, content, question 等
    """
    result = {
        "session_id": None,
        "intent": None,
        "phones": [],
        "content": "",
        "question": None,
        "quick_replies": [],
        "missing_fields": [],
        "events": []
    }

    url = f"{BASE_URL}/api/chat"
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        event = json.loads(data_str)
                        result["events"].append(event)

                        if event.get("type") == "session":
                            result["session_id"] = event.get("data")
                        elif event.get("type") == "intent":
                            result["intent"] = event.get("data")
                        elif event.get("type") == "phones":
                            result["phones"] = event.get("data", [])
                        elif event.get("type") == "content":
                            result["content"] += event.get("data", "")
                        elif event.get("type") == "question":
                            question_data = event.get("data", {})
                            result["question"] = question_data.get("question", "")
                            result["quick_replies"] = question_data.get("quick_replies", [])
                            result["missing_fields"] = question_data.get("missing_fields", [])
                    except json.JSONDecodeError:
                        pass

    return result


async def test_scenario_1():
    """
    场景1：模糊需求触发追问
    用户："推荐手机"
    预期：返回追问（预算、游戏、拍照等）
    """
    print("\n" + "=" * 60)
    print("场景1：模糊需求触发追问")
    print("=" * 60)

    result = await stream_chat("推荐手机")

    print(f"\n用户输入: 推荐手机")
    print(f"Session ID: {result['session_id']}")
    print(f"Intent: {result['intent']}")

    # 检查是否触发追问
    has_question = result["question"] is not None and len(result["question"]) > 0
    has_quick_replies = len(result["quick_replies"]) > 0
    has_missing_fields = len(result["missing_fields"]) > 0

    print(f"\n追问问题: {result['question']}")
    print(f"快捷回复: {result['quick_replies']}")
    print(f"缺失字段: {result['missing_fields']}")

    # 验证结果
    success = has_question and has_quick_replies and has_missing_fields

    assert has_question, "模糊需求'推荐手机'应触发追问问题"
    assert has_quick_replies, "追问应包含快捷回复选项"
    assert has_missing_fields, "追问应包含缺失字段列表"

    return True


async def test_scenario_2():
    """
    场景2：多轮对话状态累积
    第一轮："推荐手机" → 追问
    第二轮："3000左右" → 继续追问
    第三轮："玩游戏" → 继续追问或推荐
    """
    print("\n" + "=" * 60)
    print("场景2：多轮对话状态累积")
    print("=" * 60)

    # 第一轮
    print("\n[第一轮]")
    result1 = await stream_chat("推荐手机")
    session_id = result1["session_id"]

    print(f"用户输入: 推荐手机")
    print(f"追问问题: {result1['question']}")
    print(f"缺失字段: {result1['missing_fields']}")

    first_round_has_question = result1["question"] is not None

    # 第二轮 - 回答预算
    print("\n[第二轮]")
    result2 = await stream_chat("3000左右", session_id)

    print(f"用户输入: 3000左右")
    print(f"追问问题: {result2['question']}")
    print(f"缺失字段: {result2['missing_fields']}")

    # 检查预算是否已记录（缺失字段应该减少）
    budget_recorded = "预算" not in result2["missing_fields"]
    still_has_question = result2["question"] is not None

    # 第三轮 - 回答游戏需求
    print("\n[第三轮]")
    result3 = await stream_chat("玩游戏", session_id)

    print(f"用户输入: 玩游戏")
    print(f"追问问题: {result3['question']}")
    print(f"缺失字段: {result3['missing_fields']}")
    print(f"返回手机数量: {len(result3['phones'])}")

    # 检查是否有推荐（预算+游戏需求已收集，应该可以推荐）
    has_recommendation = len(result3["phones"]) > 0 or len(result3["content"]) > 0
    no_more_question = result3["question"] is None or len(result3["question"]) == 0

    # 验证结果
    assert first_round_has_question, "第一轮'推荐手机'应触发追问"
    assert budget_recorded, "回答预算后应记录预算信息"
    assert still_has_question, "第二轮应继续追问"
    assert has_recommendation or no_more_question, "第三轮应给出推荐或停止追问"

    return True


async def test_scenario_3():
    """
    场景3：明确需求直接推荐
    用户："推荐3000元游戏手机"
    预期：直接返回手机推荐
    """
    print("\n" + "=" * 60)
    print("场景3：明确需求直接推荐")
    print("=" * 60)

    result = await stream_chat("推荐3000元游戏手机")

    print(f"\n用户输入: 推荐3000元游戏手机")
    print(f"Session ID: {result['session_id']}")
    print(f"Intent: {result['intent']}")
    print(f"返回手机数量: {len(result['phones'])}")
    print(f"推荐内容预览: {result['content'][:100]}...")

    # 检查是否直接推荐（无追问）
    has_phones = len(result["phones"]) > 0
    has_content = len(result["content"]) > 0
    no_question = result["question"] is None or len(result["question"]) == 0

    # 验证推荐的手机价格在预算范围
    if has_phones:
        prices = [p["price"] for p in result["phones"]]
        print(f"推荐手机价格: {prices}")
        in_budget = all(2000 <= p <= 4000 for p in prices)  # 3000左右 ±500
    else:
        in_budget = False

    assert has_phones, f"明确需求'推荐3000元游戏手机'应返回手机推荐，实际返回 {len(result['phones'])} 个"
    assert has_content, "应返回推荐内容"
    assert no_question, "明确需求不应触发追问"
    if has_phones:
        assert in_budget, f"推荐手机价格应在2000-4000范围内，实际价格: {prices}"

    return True


async def test_scenario_4():
    """
    场景4：快捷回复交互
    模拟点击快捷回复按钮
    """
    print("\n" + "=" * 60)
    print("场景4：快捷回复交互")
    print("=" * 60)

    # 第一轮 - 获取追问和快捷回复
    result1 = await stream_chat("推荐手机")
    session_id = result1["session_id"]

    print(f"\n[第一轮]")
    print(f"用户输入: 推荐手机")
    print(f"追问问题: {result1['question']}")
    print(f"快捷回复选项: {result1['quick_replies']}")

    has_quick_replies = len(result1["quick_replies"]) > 0
    assert has_quick_replies, "推荐手机应返回快捷回复选项"

    # 模拟点击第一个快捷回复
    first_reply = result1["quick_replies"][0]
    print(f"\n[点击快捷回复: {first_reply}]")

    result2 = await stream_chat(first_reply, session_id)

    print(f"追问问题: {result2['question']}")
    print(f"快捷回复选项: {result2['quick_replies']}")
    print(f"缺失字段: {result2['missing_fields']}")

    # 检查快捷回复是否正确处理
    # 预算快捷回复应该记录预算
    budget_quick_reply = first_reply in ["1000-2000元", "2000-3000元", "3000-5000元", "5000元以上"]

    if budget_quick_reply:
        budget_recorded = "预算" not in result2["missing_fields"]
        assert budget_recorded, f"快捷回复'{first_reply}'应记录预算，缺失字段: {result2['missing_fields']}"
    else:
        # 其他快捷回复应继续对话
        has_followup = len(result2["quick_replies"]) > 0 or len(result2["phones"]) > 0
        assert has_followup, "快捷回复交互后应继续对话或返回推荐"

    return True


async def test_scenario_5():
    """
    场景5：完整追问流程 - 从模糊到明确
    """
    print("\n" + "=" * 60)
    print("场景5：完整追问流程 - 从模糊到明确")
    print("=" * 60)

    # 第一轮
    result1 = await stream_chat("想买个手机")
    session_id = result1["session_id"]

    print(f"\n[第一轮] 用户: 想买个手机")
    print(f"追问: {result1['question']}")
    print(f"缺失字段: {result1['missing_fields']}")

    # 回答预算
    result2 = await stream_chat("2000到3000元", session_id)

    print(f"\n[第二轮] 用户: 2000到3000元")
    print(f"追问: {result2['question']}")
    print(f"缺失字段: {result2['missing_fields']}")

    # 回答游戏需求
    result3 = await stream_chat("玩王者荣耀", session_id)

    print(f"\n[第三轮] 用户: 玩王者荣耀")
    print(f"追问: {result3['question']}")
    print(f"手机数量: {len(result3['phones'])}")

    # 如果还有追问，继续回答
    if result3["question"]:
        result4 = await stream_chat("拍照一般就行", session_id)

        print(f"\n[第四轮] 用户: 拍照一般就行")
        print(f"追问: {result4['question']}")
        print(f"手机数量: {len(result4['phones'])}")

        final_result = result4
    else:
        final_result = result3

    # 验证最终推荐
    has_recommendation = len(final_result["phones"]) > 0 or len(final_result["content"]) > 0

    print(f"\n最终推荐手机数量: {len(final_result['phones'])}")
    if final_result["phones"]:
        for p in final_result["phones"][:3]:
            print(f"  - {p['brand']} {p['model']}: {p['price']}元")

    assert has_recommendation, f"完整追问流程最终应给出推荐，手机数: {len(final_result['phones'])}，内容长度: {len(final_result['content'])}"

    return True


async def main():
    """运行所有端到端测试"""
    print("\n" + "#" * 60)
    print("# 手机选购助手 - 端到端测试")
    print("#" * 60)

    results = {}

    # 运行测试场景
    results["场景1-模糊需求追问"] = await test_scenario_1()
    results["场景2-多轮状态累积"] = await test_scenario_2()
    results["场景3-明确需求推荐"] = await test_scenario_3()
    results["场景4-快捷回复交互"] = await test_scenario_4()
    results["场景5-完整追问流程"] = await test_scenario_5()

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {name}: [{status}]")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n[SUCCESS] 所有端到端测试通过!")
    else:
        print("\n[WARNING] 存在失败的测试，需要调优")


if __name__ == "__main__":
    asyncio.run(main())
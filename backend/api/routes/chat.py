from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.api.dependencies import get_db
from backend.models.schemas import ChatRequest, IntentType
from backend.services.intent import IntentService
from backend.services.retrieval import RetrievalService
from backend.services.recommend import RecommendService
from backend.services.session import SessionService
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 会话服务实例
session_service = SessionService()


@router.post("")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """对话接口 - SSE流式输出"""
    intent_service = IntentService()
    retrieval_service = RetrievalService(db)
    recommend_service = RecommendService()

    # 处理会话
    session_id = request.session_id
    if not session_id or not session_service.session_exists(session_id):
        session_id = session_service.create_session()

    # 添加用户消息到会话
    session_service.add_message(session_id, "user", request.message)

    # 获取会话历史用于LLM上下文
    history = session_service.get_messages(session_id)

    # 识别意图（传入历史上下文）
    intent_result = await intent_service.recognize(request.message, history)

    async def generate():
        # 发送会话ID
        yield f"data: {json.dumps({'type': 'session', 'data': session_id}, ensure_ascii=False)}\n\n"

        # 发送意图信息
        yield f"data: {json.dumps({'type': 'intent', 'data': intent_result.intent.value}, ensure_ascii=False)}\n\n"

        if intent_result.intent == IntentType.COMPARE:
            # 对比模式
            phones = retrieval_service.get_phones_by_model(intent_result.phones_mentioned)
            if len(phones) < 2:
                phones = retrieval_service.get_all_phones(2)

            # 发送手机信息
            phones_data = [p.to_dict() for p in phones]
            yield f"data: {json.dumps({'type': 'phones', 'data': phones_data}, ensure_ascii=False)}\n\n"

            # 收集完整回复
            full_reply = ""
            # 流式输出对比结果
            async for chunk in recommend_service.compare(phones, history):
                full_reply += chunk
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

            # 保存助手回复到会话
            session_service.add_message(session_id, "assistant", full_reply)

        else:
            # 推荐/筛选模式
            phones = retrieval_service.search(intent_result, limit=5)
            if not phones:
                phones = retrieval_service.get_all_phones(5)

            # 发送手机信息
            phones_data = [p.to_dict() for p in phones]
            yield f"data: {json.dumps({'type': 'phones', 'data': phones_data}, ensure_ascii=False)}\n\n"

            # 收集完整回复
            full_reply = ""
            # 流式输出推荐结果
            async for chunk in recommend_service.recommend(request.message, phones, history):
                full_reply += chunk
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

            # 保存助手回复到会话
            session_service.add_message(session_id, "assistant", full_reply)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.api.dependencies import get_db, get_session_service, get_intent_service, get_recommend_service
from backend.models.schemas import ChatRequest, IntentType
from backend.services.intent import IntentService
from backend.services.retrieval import RetrievalService
from backend.services.recommend import RecommendService
from backend.services.session import SessionService
from backend.utils.security import validate_chat_input
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
    intent_service: IntentService = Depends(get_intent_service),
    recommend_service: RecommendService = Depends(get_recommend_service)
):
    """对话接口 - SSE流式输出"""
    retrieval_service = RetrievalService(db)

    # 验证和清理用户输入
    is_valid, sanitized_message, error = validate_chat_input(request.message)
    if not is_valid:
        logger.warning(f"Invalid input rejected: {error}")

        async def error_response():
            yield f"data: {json.dumps({'type': 'error', 'data': error}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(error_response(), media_type="text/event-stream")

    # 记录原始输入（脱敏）
    logger.info(f"Chat request - session: {request.session_id}, message length: {len(request.message)}")

    # 处理会话
    session_id = request.session_id
    if not session_id or not session_service.session_exists(session_id):
        session_id = session_service.create_session()

    # 添加用户消息到会话（使用清理后的消息）
    session_service.add_message(session_id, "user", sanitized_message)

    # 获取会话历史用于LLM上下文
    history = session_service.get_messages(session_id)

    # 识别意图（传入历史上下文，使用转义后的消息）
    intent_result = await intent_service.recognize(sanitized_message, history)

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
            async for chunk in recommend_service.recommend(sanitized_message, phones, history):
                full_reply += chunk
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

            # 保存助手回复到会话
            session_service.add_message(session_id, "assistant", full_reply)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

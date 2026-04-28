from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.api.dependencies import get_db
from backend.models.schemas import ChatRequest, IntentType
from backend.services.intent import IntentService
from backend.services.retrieval import RetrievalService
from backend.services.recommend import RecommendService
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """对话接口 - SSE流式输出"""
    intent_service = IntentService()
    retrieval_service = RetrievalService(db)
    recommend_service = RecommendService()

    # 识别意图
    intent_result = await intent_service.recognize(request.message)

    async def generate():
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

            # 流式输出对比结果
            async for chunk in recommend_service.compare(phones):
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

        else:
            # 推荐/筛选模式
            phones = retrieval_service.search(intent_result, limit=5)
            if not phones:
                phones = retrieval_service.get_all_phones(5)

            # 发送手机信息
            phones_data = [p.to_dict() for p in phones]
            yield f"data: {json.dumps({'type': 'phones', 'data': phones_data}, ensure_ascii=False)}\n\n"

            # 流式输出推荐结果
            async for chunk in recommend_service.recommend(request.message, phones):
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

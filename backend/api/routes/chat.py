from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.api.dependencies import get_db, get_session_service, get_intent_service, get_recommend_service
from backend.models.schemas import ChatRequest, IntentType
from backend.services.intent import IntentService
from backend.services.retrieval import RetrievalService
from backend.services.recommend import RecommendService
from backend.services.session import SessionService
from backend.services.question import QuestionService
from backend.services.model_parser import ModelParserService
from backend.utils.security import validate_chat_input
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Rate limiter 实例
limiter = Limiter(key_func=get_remote_address)


def _is_explicit_request(intent_result) -> bool:
    """
    判断用户请求是否足够明确，可以直接推荐。

    明确请求的条件：
    - 有具体预算（budget_max < 100000）
    - 且有功能需求（features 非空）

    Args:
        intent_result: 意图识别结果

    Returns:
        bool: 是否可以直接推荐
    """
    has_explicit_budget = intent_result.budget_max < 100000
    has_features = bool(intent_result.features)
    return has_explicit_budget and has_features


@router.post("")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
    intent_service: IntentService = Depends(get_intent_service),
    recommend_service: RecommendService = Depends(get_recommend_service)
):
    """对话接口 - SSE流式输出，支持多轮对话追问"""
    retrieval_service = RetrievalService(db)
    question_service = QuestionService()

    # 验证和清理用户输入
    is_valid, sanitized_message, error = validate_chat_input(chat_request.message)
    if not is_valid:
        logger.warning(f"Invalid input rejected: {error}")

        async def error_response():
            yield f"data: {json.dumps({'type': 'error', 'code': 'INVALID_INPUT', 'data': error}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(error_response(), media_type="text/event-stream")

    # 记录原始输入（脱敏）
    logger.info(f"Chat request - session: {chat_request.session_id}, message length: {len(chat_request.message)}")

    # 处理会话
    session_id = chat_request.session_id
    session_existed = bool(session_id and session_service.session_exists(session_id))
    if not session_existed:
        session_id = session_service.create_session()
        logger.info(f"[SESSION] Created new session: {session_id[:8]}... (incoming was: {chat_request.session_id})")
    else:
        logger.info(f"[SESSION] Using existing session: {session_id[:8]}...")

    # 添加用户消息到会话（使用清理后的消息）
    session_service.add_message(session_id, "user", sanitized_message)

    # 获取会话历史用于LLM上下文
    history = session_service.get_messages(session_id)

    # 获取当前用户需求状态
    user_profile = session_service.get_profile(session_id)
    logger.info(f"[PROFILE] Before update: {user_profile.model_dump() if user_profile else 'None'}")

    # 识别意图（传入历史上下文和用户画像，用于需求完整性判断）
    intent_result = await intent_service.recognize(sanitized_message, history, user_profile)
    logger.info(f"[INTENT] intent={intent_result.intent.value}, budget=[{intent_result.budget_min},{intent_result.budget_max}], features={intent_result.features}, no_need={intent_result.no_need_features}, reset={intent_result.reset_profile}, need_clarification={intent_result.need_clarification}")

    # 检查是否需要重置状态
    if intent_result.reset_profile:
        logger.info(f"Resetting user profile for session {session_id}")
        user_profile = session_service.reset_profile(session_id)
    else:
        # 更新用户需求状态（增量合并）
        user_profile = session_service.update_profile(session_id, intent_result)

    logger.info(f"[PROFILE] After update: {user_profile.model_dump()}, is_complete={user_profile.is_complete()}")

    async def generate():
        try:
            # 发送会话ID
            yield f"data: {json.dumps({'type': 'session', 'data': session_id}, ensure_ascii=False)}\n\n"

            # 发送意图信息
            yield f"data: {json.dumps({'type': 'intent', 'data': intent_result.intent.value}, ensure_ascii=False)}\n\n"

            # 判断是否需要追问
            # 使用更新后的用户画像判断完整性
            # 注意：intent_result.need_clarification 是基于更新前的画像计算的，不可靠
            # 对比模式不需要追问，直接进入对比流程
            need_clarification = (
                intent_result.intent != IntentType.COMPARE and
                (
                    intent_result.pain_point_detected or
                    (not user_profile.is_complete() and not _is_explicit_request(intent_result))
                )
            )
            logger.info(f"[DECISION] need_clarification={need_clarification}, is_complete={user_profile.is_complete()}, intent={intent_result.intent.value}, is_explicit={_is_explicit_request(intent_result)}")

            if need_clarification:
                # 发送追问事件
                if intent_result.pain_point_detected:
                    # 疼痛点场景：使用意图服务生成的痛点追问
                    question_data = {
                        'question': intent_result.clarification_question,
                        'quick_replies': [],
                        'missing_fields': [],
                        'pain_point_type': intent_result.pain_point_type,
                        'pain_point_severity': intent_result.pain_point_severity
                    }
                    session_service.add_message(session_id, "assistant", intent_result.clarification_question)
                else:
                    # 普通追问：需求信息不完整
                    question_response = question_service.generate_full_response(user_profile)
                    question_data = {
                        'question': question_response.question,
                        'quick_replies': question_response.quick_replies,
                        'missing_fields': question_response.missing_fields
                    }
                    session_service.add_message(session_id, "assistant", question_response.question)

                yield f"data: {json.dumps({'type': 'question', 'data': question_data}, ensure_ascii=False)}\n\n"

            elif intent_result.intent == IntentType.COMPARE:
                # 对比模式
                phones = retrieval_service.get_phones_by_model(intent_result.phones_mentioned)

                if len(phones) < 2:
                    # 型号未找到：不回退到全库，不调 compare([])（会致 LLM 幻觉）(ISSUE-039)
                    # 找出未匹配的型号名告知用户
                    # 注意 get_phones_by_model 是模糊匹配（"小米14" 命中 "小米14 Ultra"），
                    # 故 missing 检测也用子串回判，避免模糊命中时误报"未找到" (ISSUE-039)
                    def _is_matched(mentioned: str, phones: list) -> bool:
                        return any(mentioned in p.model or p.model in mentioned for p in phones)
                    missing = [m for m in intent_result.phones_mentioned if not _is_matched(m, phones)]
                    if missing:
                        notice = f"未找到机型：{'、'.join(missing)}。请确认型号名称后重试"
                    else:
                        notice = "未找到可比对的机型，请确认型号名称后重试"
                    yield f"data: {json.dumps({'type': 'notice', 'data': notice}, ensure_ascii=False)}\n\n"
                    full_reply = notice
                    session_service.add_message(session_id, "assistant", full_reply)
                else:
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
                # 使用分级回退检索，避免检索为空时丢弃预算 (ISSUE-036)
                phones, notice = retrieval_service.search_with_fallback(intent_result, limit=5)

                # 发送告警提示（场景放宽或无数据时）
                if notice:
                    yield f"data: {json.dumps({'type': 'notice', 'data': notice}, ensure_ascii=False)}\n\n"

                if not phones:
                    # tier-3 真无数据：不调 LLM，直接结束
                    session_service.add_message(session_id, "assistant", notice or "未找到匹配机型")
                else:
                    # 收集完整回复（cons 后处理已在 recommend_service.recommend() 中完成）
                    full_reply = ""
                    # 流式输出推荐结果
                    async for chunk in recommend_service.recommend(sanitized_message, phones, history):
                        full_reply += chunk
                        yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

                    # 解析推荐的手机型号（使用 ModelParserService）
                    model_parser = ModelParserService()
                    recommended_models = model_parser.extract_recommended_models(full_reply, phones)

                    # 过滤只发送被推荐的手机（使用 ModelParserService 模糊匹配，处理品牌中英文差异）
                    if recommended_models:
                        original_count = len(phones)
                        recommended_phones = []
                        for p in phones:
                            for model_name in recommended_models:
                                if model_parser._fuzzy_match_model(model_name, p):
                                    recommended_phones.append(p)
                                    break
                        if recommended_phones:
                            phones = recommended_phones
                            logger.info(f"Filtered phones: {len(phones)} from {original_count}")
                        else:
                            # 模糊匹配失败时回退到简单子串匹配
                            logger.warning("Fuzzy match failed, falling back to substring match")
                            for p in phones:
                                for model_name in recommended_models:
                                    model_clean = model_name.replace('（推荐指数：⭐⭐⭐⭐⭐）', '').replace('（推荐指数：⭐⭐⭐⭐）', '').strip().lower()
                                    if p.model.lower() in model_clean or model_clean in f"{p.brand} {p.model}".lower():
                                        recommended_phones.append(p)
                                        break
                            if recommended_phones:
                                phones = recommended_phones
                                logger.info(f"Filtered phones (fallback): {len(phones)} from {original_count}")
                            else:
                                logger.warning(f"No phones matched from recommended_models: {recommended_models}")
                    else:
                        logger.info(f"No recommended_models extracted, sending all {len(phones)} phones")

                    # 发送手机信息（在内容之后发送，前端需要处理顺序）
                    phones_data = [p.to_dict() for p in phones]
                    yield f"data: {json.dumps({'type': 'phones', 'data': phones_data}, ensure_ascii=False)}\n\n"

                    # 保存助手回复到会话
                    session_service.add_message(session_id, "assistant", full_reply)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"SSE generator error: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'code': 'INTERNAL_ERROR', 'data': '服务处理异常，请重试'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

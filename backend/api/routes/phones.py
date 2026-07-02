from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from backend.api.dependencies import get_db
from backend.models.domain import Phone
from backend.models.schemas import PhoneBrief, PhoneListResponse
from backend.services.camera_score import camera_scoring_service

router = APIRouter(prefix="/api/phones", tags=["phones"])


@router.get("", response_model=PhoneListResponse)
async def list_phones(
    brand: str = Query(None, description="手机品牌，支持中文如'小米'、'华为'等"),
    min_price: int = Query(None, ge=0),
    max_price: int = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    sort: str = Query(None, description="排序：price_asc / price_desc", pattern="^(price_asc|price_desc)$"),
    db: Session = Depends(get_db)
):
    """获取手机列表"""
    query = db.query(Phone).filter(Phone.price > 0)

    if brand:
        query = query.filter(Phone.brand == brand)
    if min_price is not None:
        query = query.filter(Phone.price >= min_price)
    if max_price is not None:
        query = query.filter(Phone.price <= max_price)

    # 先计算总数，再应用排序和分页
    total = query.count()

    # 排序 (ISSUE-043)：无效 sort 值由 pattern 自动 422
    if sort == "price_asc":
        query = query.order_by(asc(Phone.price))
    elif sort == "price_desc":
        query = query.order_by(desc(Phone.price))

    phones = query.offset(offset).limit(limit).all()

    return PhoneListResponse(
        phones=[PhoneBrief(id=p.id, brand=p.brand, model=p.model, price=p.price, imageUrl=p.image_url) for p in phones],
        total=total
    )


@router.get("/{phone_id}")
async def get_phone(phone_id: int, db: Session = Depends(get_db)):
    """获取手机详情"""
    phone = db.query(Phone).filter(Phone.id == phone_id).first()
    if not phone:
        raise HTTPException(status_code=404, detail="手机不存在")

    # 获取基础信息
    result = phone.to_dict()

    # 计算影像评分明细
    scoring = camera_scoring_service.calc_total_score(phone)
    result["cameraScoring"] = scoring

    return result

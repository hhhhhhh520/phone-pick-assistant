from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.api.dependencies import get_db
from backend.models.domain import Phone
from backend.models.schemas import PhoneBrief, PhoneListResponse

router = APIRouter(prefix="/api/phones", tags=["phones"])


@router.get("", response_model=PhoneListResponse)
async def list_phones(
    brand: str = None,
    min_price: int = None,
    max_price: int = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取手机列表"""
    query = db.query(Phone)

    if brand:
        query = query.filter(Phone.brand == brand)
    if min_price:
        query = query.filter(Phone.price >= min_price)
    if max_price:
        query = query.filter(Phone.price <= max_price)

    phones = query.limit(limit).all()
    total = query.count()

    return PhoneListResponse(
        phones=[PhoneBrief(id=p.id, brand=p.brand, model=p.model, price=p.price) for p in phones],
        total=total
    )


@router.get("/{phone_id}")
async def get_phone(phone_id: int, db: Session = Depends(get_db)):
    """获取手机详情"""
    phone = db.query(Phone).filter(Phone.id == phone_id).first()
    if not phone:
        raise HTTPException(status_code=404, detail="手机不存在")
    return phone.to_dict()

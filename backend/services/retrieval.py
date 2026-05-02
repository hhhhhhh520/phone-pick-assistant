from sqlalchemy.orm import Session
from backend.models.domain import Phone
from typing import List
from sqlalchemy import case


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db

    def get_phones_by_budget(self, min_price: int, max_price: int, limit: int = 10) -> List[Phone]:
        """按预算筛选，优先返回有图片的"""
        return self.db.query(Phone).filter(
            Phone.price > 0,  # 过滤无效价格
            Phone.price >= min_price,
            Phone.price <= max_price
        ).order_by(
            # 有图片的排前面
            case(
                (Phone.image_url.isnot(None), 0),
                else_=1
            ),
            Phone.price
        ).limit(limit).all()

    def get_phones_by_brand(self, brands: List[str], limit: int = 10) -> List[Phone]:
        """按品牌筛选，优先返回有图片的"""
        return self.db.query(Phone).filter(
            Phone.brand.in_(brands)
        ).order_by(
            case(
                (Phone.image_url.isnot(None), 0),
                else_=1
            )
        ).limit(limit).all()

    def get_phones_by_model(self, models: List[str]) -> List[Phone]:
        """按型号查找，优先返回有图片且价格有效的"""
        phones = []
        for model in models:
            # 优先级1: 精确匹配完整型号（如"小米14"）
            phone = self.db.query(Phone).filter(
                Phone.price > 0,
                Phone.model == model
            ).first()

            # 优先级2: 完整型号作为子串匹配（如"小米14"匹配"小米14 Ultra"）
            if not phone:
                phone = self.db.query(Phone).filter(
                    Phone.price > 0,
                    Phone.model.contains(model)
                ).order_by(
                    # 优先匹配最短的型号（避免"小米14"匹配到"小米14 Ultra"）
                    case(
                        (Phone.image_url.isnot(None), 0),
                        else_=1
                    ),
                    Phone.price
                ).first()

            # 优先级3: 提取核心型号匹配（如"小米14" -> "14"，但必须同品牌）
            if not phone:
                # 提取品牌和核心型号
                brand_prefix = None
                model_core = model
                for brand in ["小米", "华为", "苹果", "OPPO", "vivo", "荣耀", "Redmi", "realme"]:
                    if model.startswith(brand):
                        brand_prefix = brand
                        model_core = model[len(brand):].strip()
                        break

                if brand_prefix and model_core:
                    # 必须同时匹配品牌和核心型号
                    phone = self.db.query(Phone).filter(
                        Phone.price > 0,
                        Phone.brand == brand_prefix,
                        Phone.model.contains(model_core)
                    ).order_by(
                        case(
                            (Phone.image_url.isnot(None), 0),
                            else_=1
                        ),
                        Phone.price
                    ).first()

            if phone:
                phones.append(phone)
        return phones

    def search(self, intent_result, limit: int = 10) -> List[Phone]:
        """综合搜索，优先返回有图片的"""
        query = self.db.query(Phone)

        # 过滤掉无效价格（price=0或null）
        query = query.filter(Phone.price > 0)

        # 预算筛选
        if intent_result.budget_min > 0 or intent_result.budget_max < 100000:
            query = query.filter(
                Phone.price >= intent_result.budget_min,
                Phone.price <= intent_result.budget_max
            )

        # 品牌筛选
        if intent_result.brands:
            query = query.filter(Phone.brand.in_(intent_result.brands))

        return query.order_by(
            # 有图片的排前面
            case(
                (Phone.image_url.isnot(None), 0),
                else_=1
            ),
            Phone.price
        ).limit(limit).all()

    def get_all_phones(self, limit: int = 20) -> List[Phone]:
        """获取所有手机，优先返回有图片的"""
        return self.db.query(Phone).filter(
            Phone.price > 0  # 过滤无效价格
        ).order_by(
            case(
                (Phone.image_url.isnot(None), 0),
                else_=1
            )
        ).limit(limit).all()

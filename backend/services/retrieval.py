from sqlalchemy.orm import Session
from backend.models.domain import Phone
from typing import List


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db

    def get_phones_by_budget(self, min_price: int, max_price: int, limit: int = 10) -> List[Phone]:
        """按预算筛选"""
        return self.db.query(Phone).filter(
            Phone.price >= min_price,
            Phone.price <= max_price
        ).order_by(Phone.price).limit(limit).all()

    def get_phones_by_brand(self, brands: List[str], limit: int = 10) -> List[Phone]:
        """按品牌筛选"""
        return self.db.query(Phone).filter(
            Phone.brand.in_(brands)
        ).limit(limit).all()

    def get_phones_by_model(self, models: List[str]) -> List[Phone]:
        """按型号查找"""
        phones = []
        for model in models:
            phone = self.db.query(Phone).filter(
                Phone.model.contains(model)
            ).first()
            if phone:
                phones.append(phone)
        return phones

    def search(self, intent_result, limit: int = 10) -> List[Phone]:
        """综合搜索"""
        query = self.db.query(Phone)

        # 预算筛选
        if intent_result.budget_min > 0 or intent_result.budget_max < 100000:
            query = query.filter(
                Phone.price >= intent_result.budget_min,
                Phone.price <= intent_result.budget_max
            )

        # 品牌筛选
        if intent_result.brands:
            query = query.filter(Phone.brand.in_(intent_result.brands))

        return query.limit(limit).all()

    def get_all_phones(self, limit: int = 20) -> List[Phone]:
        """获取所有手机"""
        return self.db.query(Phone).limit(limit).all()

from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from storage.database.shared.model import IndustryRating

# --- Pydantic Models ---
class IndustryRatingCreate(BaseModel):
    industry_name: str = Field(..., description="行业名称")
    rating: Optional[str] = Field(None, description="评级: A/B/C/D/E")
    category: Optional[str] = Field(None, description="分类: 短期可关注/中期可关注/潜在有上涨趋势/下跌趋势")
    is_hot: bool = Field(False, description="是否为热点行业")

class IndustryRatingUpdate(BaseModel):
    rating: Optional[str] = None
    category: Optional[str] = None
    is_hot: Optional[bool] = None
    rating_history: Optional[dict] = None

# --- Manager Class ---
class IndustryRatingManager:
    """Manager class for IndustryRating operations."""

    def create_or_update(self, db: Session, industry_name: str, rating_in: IndustryRatingCreate) -> IndustryRating:
        """创建或更新行业评级"""
        # 查找是否已存在该行业
        existing = db.query(IndustryRating).filter(IndustryRating.industry_name == industry_name).first()
        
        if existing:
            # 如果存在，更新评级
            update_data = rating_in.model_dump(exclude_unset=True)
            
            # 记录评级历史
            if rating_in.rating and rating_in.rating != existing.rating:
                if not existing.rating_history:
                    existing.rating_history = {}
                
                # 记录旧评级
                existing.rating_history[datetime.now().strftime('%Y-%m-%d')] = {
                    'old_rating': existing.rating,
                    'new_rating': rating_in.rating,
                    'category': rating_in.category
                }
            
            # 更新字段
            for field, value in update_data.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)
            
            existing.rating_date = datetime.now()
            db.add(existing)
            try:
                db.commit()
                db.refresh(existing)
                return existing
            except Exception:
                db.rollback()
                raise
        else:
            # 如果不存在，创建新的
            industry_data = rating_in.model_dump()
            industry_data['rating_date'] = datetime.now()
            
            # 初始化评级历史
            if rating_in.rating:
                industry_data['rating_history'] = {
                    datetime.now().strftime('%Y-%m-%d'): {
                        'new_rating': rating_in.rating,
                        'category': rating_in.category
                    }
                }
            
            db_industry = IndustryRating(**industry_data)
            db.add(db_industry)
            try:
                db.commit()
                db.refresh(db_industry)
                return db_industry
            except Exception:
                db.rollback()
                raise

    def get_by_name(self, db: Session, industry_name: str) -> Optional[IndustryRating]:
        """根据行业名称获取评级"""
        return db.query(IndustryRating).filter(IndustryRating.industry_name == industry_name).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[IndustryRating]:
        """获取所有行业评级"""
        return db.query(IndustryRating).order_by(IndustryRating.rating_date.desc()).offset(skip).limit(limit).all()

    def get_by_category(self, db: Session, category: str) -> List[IndustryRating]:
        """根据分类获取行业"""
        return db.query(IndustryRating).filter(IndustryRating.category == category).all()

    def get_by_rating(self, db: Session, rating: str) -> List[IndustryRating]:
        """根据评级获取行业"""
        return db.query(IndustryRating).filter(IndustryRating.rating == rating).all()

    def get_hot_industries(self, db: Session) -> List[IndustryRating]:
        """获取所有热点行业"""
        return db.query(IndustryRating).filter(IndustryRating.is_hot == True).all()

    def update_rating(self, db: Session, industry_name: str, new_rating: str, new_category: str) -> Optional[IndustryRating]:
        """更新行业评级"""
        industry = self.get_by_name(db, industry_name)
        if not industry:
            return None
        
        # 记录评级变化
        if new_rating != industry.rating:
            if not industry.rating_history:
                industry.rating_history = {}
            
            industry.rating_history[datetime.now().strftime('%Y-%m-%d')] = {
                'old_rating': industry.rating,
                'new_rating': new_rating,
                'category': new_category
            }
        
        industry.rating = new_rating
        industry.category = new_category
        industry.rating_date = datetime.now()
        industry.is_hot = True
        
        db.add(industry)
        try:
            db.commit()
            db.refresh(industry)
            return industry
        except Exception:
            db.rollback()
            raise

    def downgrade_non_hot(self, db: Session) -> int:
        """降级非热点行业（将昨日热点但今日不是热点的行业降一级）"""
        # 获取所有热点行业
        hot_industries = self.get_hot_industries(db)
        hot_names = {ind.industry_name for ind in hot_industries}
        
        # 将所有标记为热点但不在当前热点列表中的行业降级
        all_hot_marked = db.query(IndustryRating).filter(IndustryRating.is_hot == True).all()
        downgraded_count = 0
        
        for industry in all_hot_marked:
            if industry.industry_name not in hot_names:
                # 降级：A->B, B->C, C->D, D->E
                rating_map = {'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'E'}
                old_rating = industry.rating
                new_rating = rating_map.get(old_rating, 'E')
                
                if old_rating != new_rating:
                    if not industry.rating_history:
                        industry.rating_history = {}
                    
                    industry.rating_history[datetime.now().strftime('%Y-%m-%d')] = {
                        'old_rating': old_rating,
                        'new_rating': new_rating,
                        'reason': '非热点降级'
                    }
                    
                    industry.rating = new_rating
                    industry.is_hot = False
                    downgraded_count += 1
                    db.add(industry)
        
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        
        return downgraded_count

    def get_rating_summary(self, db: Session) -> dict:
        """获取评级汇总统计"""
        industries = self.get_all(db, limit=1000)
        
        summary = {
            'total': len(industries),
            'by_rating': {},
            'by_category': {
                '短期可关注': 0,
                '中期可关注': 0,
                '潜在有上涨趋势': 0,
                '下跌趋势': 0,
                '未分类': 0
            },
            'hot_count': 0
        }
        
        for ind in industries:
            # 按评级统计
            if ind.rating:
                summary['by_rating'][ind.rating] = summary['by_rating'].get(ind.rating, 0) + 1
            
            # 按分类统计
            if ind.category:
                if ind.category in summary['by_category']:
                    summary['by_category'][ind.category] += 1
            else:
                summary['by_category']['未分类'] += 1
            
            # 统计热点
            if ind.is_hot:
                summary['hot_count'] += 1
        
        return summary

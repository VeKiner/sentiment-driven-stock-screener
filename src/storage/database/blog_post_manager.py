from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from storage.database.shared.model import BlogPost

# --- Pydantic Models ---
class BlogPostCreate(BaseModel):
    author: str = Field(..., description="作者")
    title: str = Field(..., description="标题")
    content: Optional[str] = Field(None, description="内容")
    publish_date: Optional[datetime] = Field(None, description="发布日期")
    url: str = Field(..., description="文章链接")
    views: Optional[int] = Field(None, description="浏览量")
    comments: Optional[int] = Field(None, description="评论数")
    likes: Optional[int] = Field(None, description="点赞数")
    analysis_result: Optional[dict] = Field(None, description="智能体分析结果")

class BlogPostUpdate(BaseModel):
    content: Optional[str] = None
    analysis_result: Optional[dict] = None

# --- Manager Class ---
class BlogPostManager:
    """Manager class for BlogPost operations."""

    def create_or_update(self, db: Session, post_in: BlogPostCreate) -> BlogPost:
        """创建或更新博客文章"""
        # 查找是否已存在该URL的文章
        existing = db.query(BlogPost).filter(BlogPost.url == post_in.url).first()
        
        if existing:
            # 如果存在，更新内容和分析结果
            update_data = post_in.model_dump(exclude_unset=True, exclude={'author', 'title', 'url', 'publish_date'})
            
            for field, value in update_data.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)
            
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
            post_data = post_in.model_dump()
            db_post = BlogPost(**post_data)
            db.add(db_post)
            try:
                db.commit()
                db.refresh(db_post)
                return db_post
            except Exception:
                db.rollback()
                raise

    def get_by_url(self, db: Session, url: str) -> Optional[BlogPost]:
        """根据URL获取文章"""
        return db.query(BlogPost).filter(BlogPost.url == url).first()

    def get_by_author(self, db: Session, author: str, skip: int = 0, limit: int = 100) -> List[BlogPost]:
        """根据作者获取文章"""
        return db.query(BlogPost).filter(BlogPost.author == author).order_by(BlogPost.publish_date.desc()).offset(skip).limit(limit).all()

    def get_by_date(self, db: Session, date: datetime) -> List[BlogPost]:
        """根据日期获取文章"""
        return db.query(BlogPost).filter(BlogPost.publish_date == date).all()

    def get_today_posts(self, db: Session) -> List[BlogPost]:
        """获取今天的文章"""
        today = datetime.now().date()
        return db.query(BlogPost).filter(
            BlogPost.publish_date >= today
        ).order_by(BlogPost.publish_date.desc()).all()

    def get_recent_posts(self, db: Session, days: int = 7, limit: int = 100) -> List[BlogPost]:
        """获取最近几天的文章"""
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        return db.query(BlogPost).filter(
            BlogPost.publish_date >= start_date
        ).order_by(BlogPost.publish_date.desc()).limit(limit).all()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[BlogPost]:
        """获取所有文章"""
        return db.query(BlogPost).order_by(BlogPost.publish_date.desc()).offset(skip).limit(limit).all()

    def update_analysis(self, db: Session, post_id: int, analysis_result: dict) -> Optional[BlogPost]:
        """更新文章分析结果"""
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if not post:
            return None
        
        post.analysis_result = analysis_result
        db.add(post)
        try:
            db.commit()
            db.refresh(post)
            return post
        except Exception:
            db.rollback()
            raise

    def get_top_viewed(self, db: Session, limit: int = 10) -> List[BlogPost]:
        """获取浏览量最高的文章"""
        return db.query(BlogPost).filter(
            BlogPost.views.isnot(None)
        ).order_by(BlogPost.views.desc()).limit(limit).all()

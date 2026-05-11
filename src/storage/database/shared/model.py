from coze_coding_dev_sdk.database import Base
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime

class IndustryRating(Base):
    """行业评级表"""
    __tablename__ = "industry_rating"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    industry_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="行业名称")
    rating: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="评级: A/B/C/D/E")
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="分类: 短期可关注/中期可关注/潜在有上涨趋势/下跌趋势")
    rating_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="评级日期")
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True, comment="最后更新时间")
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否为热点行业")
    rating_history: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="评级历史记录")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    __table_args__ = (
        Index("ix_industry_rating_name", "industry_name"),
        Index("ix_industry_rating_rating", "rating"),
        Index("ix_industry_rating_category", "category"),
        Index("ix_industry_rating_is_hot", "is_hot"),
    )

class BlogPost(Base):
    """博客文章表"""
    __tablename__ = "blog_post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False, comment="作者")
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="标题")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="内容")
    publish_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="发布日期")
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False, comment="文章链接")
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="浏览量")
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="评论数")
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="点赞数")
    analysis_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="智能体分析结果")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="抓取时间")

    __table_args__ = (
        Index("ix_blog_post_author", "author"),
        Index("ix_blog_post_publish_date", "publish_date"),
        Index("ix_blog_post_url", "url"),
    )



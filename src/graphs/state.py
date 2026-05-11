from typing import Optional, List, Dict
from pydantic import BaseModel, Field

# 全局状态
class GlobalState(BaseModel):
    """全局状态定义"""
    # 模块1：数据抓取模块输出
    guba_topics: List[Dict] = Field(default=[], description="股吧热门话题数据集（字段：标题、时间、内容、标签）")
    economy_reviews: List[Dict] = Field(default=[], description="经济时评数据集（字段：标题、时间、内容、机构）")

    # 模块2：热门可投资行业提炼模块输出
    guba_industries: List[Dict] = Field(default=[], description="股吧热门行业列表（含支撑依据）")
    review_industries: List[Dict] = Field(default=[], description="时评推荐行业列表（含支撑依据）")
    final_industries: List[Dict] = Field(default=[], description="最终热门可投资行业列表")

    # 模块3：行业关联分析模块输出
    industry_network: str = Field(default="", description="行业关联关系分析文档")

    # 模块4：行业情绪分析模块输出
    industry_sentiment: str = Field(default="", description="热门行业情绪分析文档")

    # 模块5：研报&资金流数据抓取模块输出
    industry_reports: List[Dict] = Field(default=[], description="近15天行业研报数据集")
    industry_capital_flow: List[Dict] = Field(default=[], description="行业资金流数据集")

    # 模块6：研报&资金流分析模块输出
    research_capital_analysis: str = Field(default="", description="研报&资金流分析文档")

    # 模块7：综合交易策略生成模块输出
    trading_strategy: str = Field(default="", description="最终交易策略报告")

    # 模块17：PDF报告生成模块输出
    pdf_url: str = Field(default="", description="交易策略PDF报告的公开访问链接（可在浏览器中直接打开阅读，24小时有效）")

    # 模块18：企业微信推送模块输出
    send_status: str = Field(default="", description="企业微信推送状态：成功/失败")
    send_message: str = Field(default="", description="企业微信推送结果消息")

    # 模块8：大V博客抓取模块输出
    blog_posts: List[Dict] = Field(default=[], description="大V博客文章数据集")

    # 模块9：大V智能体分析模块输出
    v_insights_analysis: str = Field(default="", description="大V博客分析文档")

    # 模块10：行业评级管理模块输出
    industry_ratings: List[Dict] = Field(default=[], description="行业评级数据")
    rating_visualization: str = Field(default="", description="评级可视化数据")

# 图输入输出
class GraphInput(BaseModel):
    """工作流的输入（无输入参数）"""
    pass

class GraphOutput(BaseModel):
    """工作流的输出"""
    trading_strategy: str = Field(..., description="最终交易策略报告")
    pdf_url: str = Field(default="", description="交易策略PDF报告的公开访问链接（可在浏览器中直接打开阅读）")

# ==================== 节点1-1：股吧热门话题抓取 ====================
class GubaTopicsCollectInput(BaseModel):
    """股吧热门话题抓取节点输入"""
    pass

class GubaTopicsCollectOutput(BaseModel):
    """股吧热门话题抓取节点输出"""
    guba_topics: List[Dict] = Field(..., description="股吧热门话题数据集（字段：标题、时间、内容、标签）")
    error_message: Optional[str] = Field(default="", description="抓取失败的错误信息")

# ==================== 节点1-2：财经经济时评抓取 ====================
class EconomyReviewCollectInput(BaseModel):
    """财经经济时评抓取节点输入"""
    pass

class EconomyReviewCollectOutput(BaseModel):
    """财经经济时评抓取节点输出"""
    economy_reviews: List[Dict] = Field(..., description="经济时评数据集（字段：标题、时间、内容、机构）")
    error_message: Optional[str] = Field(default="", description="抓取失败的错误信息")

# ==================== 节点2-1：股吧内容分析智能体 ====================
class GubaIndustryAnalysisInput(BaseModel):
    """股吧内容分析智能体输入"""
    guba_topics: List[Dict] = Field(..., description="股吧热门话题数据集")

class GubaIndustryAnalysisOutput(BaseModel):
    """股吧内容分析智能体输出"""
    guba_industries: List[Dict] = Field(..., description="股吧热门行业列表（含支撑依据）")

# ==================== 节点2-2：经济时评分析智能体 ====================
class ReviewIndustryAnalysisInput(BaseModel):
    """经济时评分析智能体输入"""
    economy_reviews: List[Dict] = Field(..., description="经济时评数据集")

class ReviewIndustryAnalysisOutput(BaseModel):
    """经济时评分析智能体输出"""
    review_industries: List[Dict] = Field(..., description="时评推荐行业列表（含支撑依据）")

# ==================== 节点2-3：行业汇总节点 ====================
class IndustryMergeInput(BaseModel):
    """行业汇总节点输入"""
    guba_industries: List[Dict] = Field(..., description="股吧热门行业列表")
    review_industries: List[Dict] = Field(..., description="时评推荐行业列表")

class IndustryMergeOutput(BaseModel):
    """行业汇总节点输出"""
    final_industries: List[Dict] = Field(..., description="最终热门可投资行业列表")

# ==================== 节点3-1：行业关联分析智能体 ====================
class IndustryNetworkAnalysisInput(BaseModel):
    """行业关联分析智能体输入"""
    final_industries: List[Dict] = Field(..., description="最终热门可投资行业列表")
    guba_topics: List[Dict] = Field(..., description="股吧热门话题数据集")
    economy_reviews: List[Dict] = Field(..., description="经济时评数据集")

class IndustryNetworkAnalysisOutput(BaseModel):
    """行业关联分析智能体输出"""
    industry_network: str = Field(..., description="行业关联关系分析文档")

# ==================== 节点4-1：行业情绪分析智能体 ====================
class IndustrySentimentAnalysisInput(BaseModel):
    """行业情绪分析智能体输入"""
    final_industries: List[Dict] = Field(..., description="最终热门可投资行业列表")
    guba_topics: List[Dict] = Field(..., description="股吧热门话题数据集")
    economy_reviews: List[Dict] = Field(..., description="经济时评数据集")

class IndustrySentimentAnalysisOutput(BaseModel):
    """行业情绪分析智能体输出"""
    industry_sentiment: str = Field(..., description="热门行业情绪分析文档")

# ==================== 节点5-1：行业研报抓取 ====================
class IndustryReportCollectInput(BaseModel):
    """行业研报抓取节点输入"""
    final_industries: List[Dict] = Field(..., description="最终热门可投资行业列表（包含行业名称等）")

class IndustryReportCollectOutput(BaseModel):
    """行业研报抓取节点输出"""
    industry_reports: List[Dict] = Field(..., description="近15天行业研报数据集")
    error_message: Optional[str] = Field(default="", description="抓取失败的错误信息")

# ==================== 节点5-2：行业资金流抓取 ====================
class IndustryCapitalFlowCollectInput(BaseModel):
    """行业资金流抓取节点输入"""
    final_industries: List[Dict] = Field(..., description="最终热门可投资行业列表（包含行业名称等）")

class IndustryCapitalFlowCollectOutput(BaseModel):
    """行业资金流抓取节点输出"""
    industry_capital_flow: List[Dict] = Field(..., description="行业资金流数据集")
    error_message: Optional[str] = Field(default="", description="抓取失败的错误信息")

# ==================== 节点6-1：研报&资金流分析智能体 ====================
class ResearchCapitalAnalysisInput(BaseModel):
    """研报&资金流分析智能体输入"""
    industry_reports: List[Dict] = Field(..., description="近15天行业研报数据集")
    industry_capital_flow: List[Dict] = Field(..., description="行业资金流数据集")
    final_industries: List[Dict] = Field(..., description="最终热门可投资行业列表")

class ResearchCapitalAnalysisOutput(BaseModel):
    """研报&资金流分析智能体输出"""
    research_capital_analysis: str = Field(..., description="研报&资金流分析文档")

# ==================== 节点7-1：综合交易策略生成智能体（已废弃，使用EnhancedTradingStrategyGenerateInput） ====================
# ==================== 节点8-1：大V博客抓取 ====================
class VBlogCollectInput(BaseModel):
    """大V博客抓取节点输入"""
    pass

class VBlogCollectOutput(BaseModel):
    """大V博客抓取节点输出"""
    blog_posts: List[Dict] = Field(..., description="大V博客文章数据集（字段：作者、标题、内容、发布日期、URL等）")
    error_message: Optional[str] = Field(default="", description="抓取失败的错误信息")

# ==================== 节点9-1：大V智能体分析 ====================
class VInsightsAnalysisInput(BaseModel):
    """大V智能体分析节点输入"""
    blog_posts: List[Dict] = Field(..., description="大V博客文章数据集")
    final_industries: List[Dict] = Field(..., description="最终热门可投资行业列表")

class VInsightsAnalysisOutput(BaseModel):
    """大V智能体分析节点输出"""
    v_insights_analysis: str = Field(..., description="大V博客分析文档")

# ==================== 节点10-1：行业评级更新 ====================
class IndustryRatingUpdateInput(BaseModel):
    """行业评级更新节点输入"""
    final_industries: List[Dict] = Field(..., description="最终热门可投资行业列表")
    industry_sentiment: str = Field(..., description="热门行业情绪分析文档")
    industry_reports: List[Dict] = Field(..., description="近15天行业研报数据集")
    industry_capital_flow: List[Dict] = Field(..., description="行业资金流数据集")

class IndustryRatingUpdateOutput(BaseModel):
    """行业评级更新节点输出"""
    industry_ratings: List[Dict] = Field(..., description="行业评级数据")
    rating_visualization: str = Field(..., description="评级可视化数据")

# ==================== 节点11-1：综合交易策略生成（融合大V） ====================
class EnhancedTradingStrategyGenerateInput(BaseModel):
    """综合交易策略生成（融合大V）节点输入"""
    industry_network: str = Field(..., description="行业关联关系分析文档")
    industry_sentiment: str = Field(..., description="热门行业情绪分析文档")
    research_capital_analysis: str = Field(..., description="研报&资金流分析文档")
    v_insights_analysis: str = Field(..., description="大V博客分析文档")
    industry_ratings: List[Dict] = Field(..., description="行业评级数据")

class EnhancedTradingStrategyGenerateOutput(BaseModel):
    """综合交易策略生成（融合大V）节点输出"""
    trading_strategy: str = Field(..., description="最终交易策略报告（融合大V分析）")

# 为了兼容性，重命名旧的输入输出类
TradingStrategyGenerateInput = EnhancedTradingStrategyGenerateInput
TradingStrategyGenerateOutput = EnhancedTradingStrategyGenerateOutput

# ==================== 节点17-1：PDF报告生成与上传 ====================
class StrategyPdfUploadInput(BaseModel):
    """PDF报告生成与上传节点输入"""
    trading_strategy: str = Field(..., description="最终交易策略报告（Markdown格式）")

class StrategyPdfUploadOutput(BaseModel):
    """PDF报告生成与上传节点输出"""
    pdf_url: str = Field(..., description="交易策略PDF报告的公开访问链接（可直接在浏览器中打开阅读，分享给他人查看，24小时有效）")
    error_message: Optional[str] = Field(default="", description="生成或上传失败的错误信息")

# ==================== 节点18-1：企业微信推送 ====================
class WeComBotSendInput(BaseModel):
    """企业微信机器人推送节点输入"""
    pdf_url: str = Field(..., description="交易策略PDF报告的公开访问链接")
    trading_strategy: str = Field(..., description="最终交易策略报告（用于提取摘要信息）")

class WeComBotSendOutput(BaseModel):
    """企业微信机器人推送节点输出"""
    send_status: str = Field(..., description="推送状态：成功/失败")
    message: str = Field(..., description="推送结果消息")
    error_message: Optional[str] = Field(default="", description="推送失败的错误信息")


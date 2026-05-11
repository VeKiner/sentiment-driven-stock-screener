from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)
from graphs.node import (
    guba_topics_collect_node,
    economy_review_collect_node,
    guba_industry_analysis_node,
    review_industry_analysis_node,
    industry_merge_node,
    industry_network_analysis_node,
    industry_sentiment_analysis_node,
    industry_report_collect_node,
    industry_capital_flow_collect_node,
    research_capital_analysis_node,
    v_blog_collect_node,
    v_insights_analysis_node,
    industry_rating_update_node,
    trading_strategy_generate_node,
    strategy_pdf_upload_node,
    wecom_bot_send_node
)

# 创建状态图，指定工作流的入参和出参
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# ==================== 模块1：数据抓取模块 ====================
# 节点1-1：股吧热门话题抓取
builder.add_node("guba_topics_collect", guba_topics_collect_node)

# 节点1-2：财经经济时评抓取
builder.add_node("economy_review_collect", economy_review_collect_node)

# ==================== 模块2：热门可投资行业提炼模块 ====================
# 节点2-1：股吧内容分析智能体
builder.add_node(
    "guba_industry_analysis",
    guba_industry_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/guba_industry_analysis_cfg.json"}
)

# 节点2-2：经济时评分析智能体
builder.add_node(
    "review_industry_analysis",
    review_industry_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/review_industry_analysis_cfg.json"}
)

# 节点2-3：行业汇总节点
builder.add_node("industry_merge", industry_merge_node)

# ==================== 模块3：行业关联分析模块 ====================
# 节点3-1：行业关联分析智能体
builder.add_node(
    "industry_network_analysis",
    industry_network_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/industry_network_analysis_cfg.json"}
)

# ==================== 模块4：行业情绪分析模块 ====================
# 节点4-1：行业情绪分析智能体
builder.add_node(
    "industry_sentiment_analysis",
    industry_sentiment_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/industry_sentiment_analysis_cfg.json"}
)

# ==================== 模块5：研报&资金流数据抓取模块 ====================
# 节点5-1：行业研报抓取
builder.add_node("industry_report_collect", industry_report_collect_node)

# 节点5-2：行业资金流抓取
builder.add_node("industry_capital_flow_collect", industry_capital_flow_collect_node)

# ==================== 模块6：研报&资金流分析模块 ====================
# 节点6-1：研报&资金流分析智能体
builder.add_node(
    "research_capital_analysis",
    research_capital_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/research_capital_analysis_cfg.json"}
)

# ==================== 模块8：大V博客抓取模块 ====================
# 节点8-1：大V博客抓取
builder.add_node("v_blog_collect", v_blog_collect_node)

# ==================== 模块9：大V智能体分析模块 ====================
# 节点9-1：大V智能体分析
builder.add_node(
    "v_insights_analysis",
    v_insights_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/v_insights_analysis_cfg.json"}
)

# ==================== 模块10：行业评级管理模块 ====================
# 节点10-1：行业评级更新
builder.add_node(
    "industry_rating_update",
    industry_rating_update_node,
    metadata={"type": "agent", "llm_cfg": "config/industry_rating_cfg.json"}
)

# ==================== 模块7：综合交易策略生成模块（增强版） ====================
# 节点7-1：综合交易策略生成智能体
builder.add_node(
    "trading_strategy_generate",
    trading_strategy_generate_node,
    metadata={"type": "agent", "llm_cfg": "config/trading_strategy_generate_cfg.json"}
)

# ==================== 模块17：PDF报告生成与上传模块 ====================
# 节点17-1：交易策略PDF生成与上传
builder.add_node("strategy_pdf_upload", strategy_pdf_upload_node)

# ==================== 模块18：企业微信推送模块 ====================
# 节点18-1：企业微信机器人推送
builder.add_node("wecom_bot_send", wecom_bot_send_node)

# ==================== 设置工作流执行顺序 ====================
# 正确架构：
# 1. guba_topics_collect 和 economy_review_collect 从开始并行执行（各自独立）
# 2. 这两个节点完成后，分别输入到对应的分析节点
# 3. 后续流程保持不变

# 模块1并行分支：
# 分支1：guba_topics_collect → guba_industry_analysis
# 分支2：economy_review_collect → review_industry_analysis
# 这两个分支从START开始就完全独立，并行执行

# START 同时启动两个抓取节点（并行执行）
builder.add_edge(START, "guba_topics_collect")
builder.add_edge(START, "economy_review_collect")

# 两个抓取节点分别输入到对应的分析节点
builder.add_edge("guba_topics_collect", "guba_industry_analysis")
builder.add_edge("economy_review_collect", "review_industry_analysis")

# 节点2-1和节点2-2 → 节点2-3（汇聚）
builder.add_edge(["guba_industry_analysis", "review_industry_analysis"], "industry_merge")

# 模块2 → 模块3：节点2-3 → 节点3-1
builder.add_edge("industry_merge", "industry_network_analysis")

# 模块3 → 模块4：节点3-1 → 节点4-1
builder.add_edge("industry_network_analysis", "industry_sentiment_analysis")

# 模块4 → 模块5：节点4-1 → 节点5-1 → 节点5-2（并行分支）
# 同时也启动大V博客抓取（并行分支）
builder.add_edge("industry_network_analysis", "industry_sentiment_analysis")
builder.add_edge("industry_network_analysis", "industry_report_collect")
builder.add_edge("industry_network_analysis", "industry_capital_flow_collect")
builder.add_edge("industry_network_analysis", "v_blog_collect")

# 节点4-1和节点5-1、节点5-2 → 节点6-1（汇聚）
builder.add_edge(["industry_sentiment_analysis", "industry_report_collect", "industry_capital_flow_collect"], "research_capital_analysis")

# 节点8-1（大V博客抓取）→ 节点9-1（大V智能体分析）
builder.add_edge("v_blog_collect", "v_insights_analysis")

# 模块6 → 模块10：节点6-1 → 节点10-1（行业评级更新）
builder.add_edge("research_capital_analysis", "industry_rating_update")

# 节点9-1（大V智能体分析）和节点10-1（行业评级更新）→ 节点7-1（汇聚）
# 这里需要确保大V分析和行业评级都完成后再生成交易策略
builder.add_edge(["v_insights_analysis", "industry_rating_update"], "trading_strategy_generate")

# 节点7-1 → 节点17-1（PDF生成与上传）
builder.add_edge("trading_strategy_generate", "strategy_pdf_upload")

# 节点17-1 → 节点18-1（企业微信推送）
builder.add_edge("strategy_pdf_upload", "wecom_bot_send")

# 节点18-1 → 结束
builder.add_edge("wecom_bot_send", END)

# 编译图
main_graph = builder.compile()

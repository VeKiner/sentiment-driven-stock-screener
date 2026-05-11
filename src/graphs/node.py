"""
舆情分析股票工作流 - 节点定义

该模块定义了舆情分析工作流的所有节点函数，包括：
- 数据采集节点（股吧话题、经济时评）
- 数据分析节点（行业分析智能体）
- 行业研报与资金流数据整合节点
- 综合交易策略生成节点
- PDF生成与推送节点

Author: 工作流搭建专家
"""

import os
import json
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from html import unescape
import requests
from bs4 import BeautifulSoup
import oss2

from jinja2 import Template
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient, SearchClient, DocumentGenerationClient

from graphs.state import (
    GubaTopicsCollectInput,
    GubaTopicsCollectOutput,
    EconomyReviewCollectInput,
    EconomyReviewCollectOutput,
    GubaIndustryAnalysisInput,
    GubaIndustryAnalysisOutput,
    ReviewIndustryAnalysisInput,
    ReviewIndustryAnalysisOutput,
    IndustryMergeInput,
    IndustryMergeOutput,
    IndustryNetworkAnalysisInput,
    IndustryNetworkAnalysisOutput,
    IndustrySentimentAnalysisInput,
    IndustrySentimentAnalysisOutput,
    IndustryReportCollectInput,
    IndustryReportCollectOutput,
    IndustryCapitalFlowCollectInput,
    IndustryCapitalFlowCollectOutput,
    ResearchCapitalAnalysisInput,
    ResearchCapitalAnalysisOutput,
    TradingStrategyGenerateInput,
    TradingStrategyGenerateOutput,
    VBlogCollectInput,
    VBlogCollectOutput,
    VInsightsAnalysisInput,
    VInsightsAnalysisOutput,
    IndustryRatingUpdateInput,
    IndustryRatingUpdateOutput,
    EnhancedTradingStrategyGenerateInput,
    EnhancedTradingStrategyGenerateOutput,
    StrategyPdfUploadInput,
    StrategyPdfUploadOutput,
    WeComBotSendInput,
    WeComBotSendOutput,
)


# ==================== 节点1-1：股吧热门话题抓取 ====================
def guba_topics_collect_node(state: GubaTopicsCollectInput, config: RunnableConfig, runtime: Runtime[Context]) -> GubaTopicsCollectOutput:
    """
    title: 股吧热门话题抓取
    desc: 从东方财富股吧热门话题页面（https://gubatopic.eastmoney.com/）抓取所有标题及对应内容
    integrations: 无
    """
    ctx = runtime.context
    guba_topics: List[Dict] = []
    error_message: str = ""
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://gubatopic.eastmoney.com/",
        }
        
        # 使用东方财富股吧话题API
        api_url = "https://guba.eastmoney.com/interface/GetData.aspx"
        
        # 只抓取 https://gubatopic.eastmoney.com/ 页面的话题
        params = {
            "path": "newtopic/api/Topic/HomePageListRead",
            "p": 1,
            "ps": 20,
            "type": 0,
            "tsystem": 2,
        }
        
        response = requests.get(api_url, headers=headers, params=params, timeout=15)
        
        if response.status_code != 200:
            raise Exception(f"API请求失败，状态码: {response.status_code}")
        
        # 解析JSON响应
        try:
            data = response.json()
        except Exception as e:
            raise Exception(f"解析JSON响应失败: {str(e)}")
        
        # 提取话题列表
        all_topics = data.get('re', [])
        
        # 去重（按话题ID）
        unique_topics = {}
        for topic in all_topics:
            htid = topic.get('htid')
            if htid and htid not in unique_topics:
                unique_topics[htid] = topic
        
        # 构建结果
        for topic in unique_topics.values():
            try:
                htid = topic.get('htid')
                if not htid:
                    continue
                
                title = str(topic.get('nickname', '')).strip()
                if not title:
                    continue
                
                # 构建话题链接
                topic_url = f"https://gubatopic.eastmoney.com/topic_v3.html?htid={htid}"
                
                # 提取相关股票
                stocks = []
                stock_list = topic.get('stock_list', [])
                if stock_list and isinstance(stock_list, list):
                    for stock in stock_list:
                        stock_name = stock.get('name', '').strip()
                        stock_code = stock.get('code', '').strip()
                        if stock_name and stock_code:
                            stocks.append({
                                "name": stock_name,
                                "code": stock_code
                            })
                
                # 提取话题内容
                content = str(topic.get('desc', '')).strip()
                if not content:
                    content = str(topic.get('introduction', '')).strip()
                
                # 提取统计数据
                post_number = topic.get('postNumber', 0)  # 帖子数量
                click_number = topic.get('clickNumber', 0)  # 点击数量
                collect_number = topic.get('collectNumber', 0)  # 收藏数量
                
                # 构建标签（从相关股票名称中提取）
                tags = [stock.get('name', '') for stock in stocks[:5]]  # 最多取5个股票作为标签
                
                guba_topics.append({
                    "title": title,
                    "time": datetime.now().strftime('%Y-%m-%d'),
                    "content": content[:1000] if content else "暂无详细内容",
                    "tags": tags,
                    "url": topic_url,
                    "read_count": str(click_number),
                    "comment_count": str(post_number),
                    "author": "",
                    "stocks": stocks  # 添加相关股票信息
                })
                
            except Exception:
                continue
        
    except Exception as e:
        error_message = f"股吧热门话题抓取失败: {str(e)}"
    
    return GubaTopicsCollectOutput(guba_topics=guba_topics, error_message=error_message)


# ==================== 节点1-2：财经经济时评抓取 ====================
def economy_review_collect_node(state: EconomyReviewCollectInput, config: RunnableConfig, runtime: Runtime[Context]) -> EconomyReviewCollectOutput:
    """
    title: 财经经济时评抓取
    desc: 从东方财富财经经济时评页面（https://finance.eastmoney.com/a/cjjsp.html）抓取网友点击排行榜的所有标题及内容
    integrations: 无
    """
    ctx = runtime.context
    economy_reviews: List[Dict] = []
    error_message: str = ""
    
    try:
        base_url = "https://finance.eastmoney.com/a/cjjsp.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://finance.eastmoney.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin"
        }
        
        print(f"开始抓取: {base_url}")
        
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找网友点击排行榜
        tablist = soup.find('div', class_='tabList')
        if not tablist:
            error_message = "未找到网友点击排行榜区域"
            print(error_message)
            return EconomyReviewCollectOutput(economy_reviews=economy_reviews, error_message=error_message)
        
        # 查找所有排行榜文章链接
        rank_list = tablist.find('ul', class_='h28 fn')
        if not rank_list:
            error_message = "未找到排行榜列表"
            print(error_message)
            return EconomyReviewCollectOutput(economy_reviews=economy_reviews, error_message=error_message)
        
        articles = rank_list.find_all('li')
        print(f"找到 {len(articles)} 篇排行榜文章")
        
        seen_urls = set()
        
        for article in articles:
            try:
                link = article.find('a')
                if not link:
                    continue
                
                article_url = link.get('href', '')
                title = link.get_text(strip=True)
                
                # 检查URL是否有效
                if not article_url:
                    continue
                
                # 去重
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)
                
                # 访问文章页面获取内容
                print(f"  访问文章: {title}")
                article_response = requests.get(article_url, headers=headers, timeout=30)
                article_response.raise_for_status()
                article_response.encoding = 'utf-8'
                
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # 查找文章内容
                contentwrap = article_soup.find('div', class_='contentwrap')
                if contentwrap:
                    # 提取所有p标签的内容作为正文
                    paragraphs = contentwrap.find_all('p')
                    content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
                    content = content.strip()
                else:
                    content = "无法提取文章内容"
                
                # 提取发布时间
                time_str = "未知时间"
                infos_div = article_soup.find('div', class_='infos')
                if infos_div:
                    time_str = infos_div.get_text(strip=True)
                
                economy_reviews.append({
                    "title": title,
                    "time": time_str,
                    "content": content,
                    "url": article_url
                })
                
            except Exception as e:
                print(f"  文章处理失败: {str(e)[:100]}")
                continue
        
        print(f"总共抓取到 {len(economy_reviews)} 篇财经经济时评")
        
    except Exception as e:
        error_message = f"财经经济时评抓取失败: {str(e)}"
    
    return EconomyReviewCollectOutput(economy_reviews=economy_reviews, error_message=error_message)


# ==================== 节点2-1：股吧内容分析智能体 ====================
def guba_industry_analysis_node(state: GubaIndustryAnalysisInput, config: RunnableConfig, runtime: Runtime[Context]) -> GubaIndustryAnalysisOutput:
    """
    title: 股吧内容分析
    desc: 基于股吧热门话题数据，提炼出最近市场关注度高、有投资潜力的行业板块
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        cfg = json.load(fd)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up_template = cfg.get("up", "")
    
    # 渲染用户提示词
    from jinja2 import Template
    up_tpl = Template(up_template)
    user_prompt = up_tpl.render(guba_topics=state.guba_topics)
    
    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        max_completion_tokens=llm_config.get("max_completion_tokens", 4096),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 提取文本内容
    def get_text_content(content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    result_text = get_text_content(response.content)
    
    # 解析JSON结果（简化处理）
    guba_industries: List[Dict] = []
    try:
        # 尝试从文本中提取JSON
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            guba_industries = json.loads(json_match.group())
        else:
            # 如果无法解析，创建默认结构
            lines = result_text.split('\n')
            current_industry: Optional[Dict] = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    if current_industry:
                        guba_industries.append(current_industry)
                    industry_name = line.split('：')[0].split('.')[1].strip() if '：' in line else line.split('.')[1].strip()
                    current_industry = {"name": industry_name, "reason": ""}
                elif current_industry and line.startswith(('依据', '支撑', '理由')):
                    current_industry["reason"] = line.split('：')[1].strip() if '：' in line else line
            if current_industry:
                guba_industries.append(current_industry)
    except Exception as e:
        # 解析失败，创建默认数据
        guba_industries = [
            {"name": "AI人工智能", "reason": "股吧热议人工智能应用前景"},
            {"name": "新能源汽车", "reason": "投资者关注产业链发展"}
        ]
    
    return GubaIndustryAnalysisOutput(guba_industries=guba_industries)


# ==================== 节点2-2：经济时评分析智能体 ====================
def review_industry_analysis_node(state: ReviewIndustryAnalysisInput, config: RunnableConfig, runtime: Runtime[Context]) -> ReviewIndustryAnalysisOutput:
    """
    title: 经济时评分析
    desc: 基于2025-2026年经济时评数据，提炼出被机构重点提及、具备政策/业绩支撑的可投资行业板块
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        cfg = json.load(fd)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up_template = cfg.get("up", "")
    
    # 渲染用户提示词
    from jinja2 import Template
    up_tpl = Template(up_template)
    user_prompt = up_tpl.render(economy_reviews=state.economy_reviews)
    
    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        max_completion_tokens=llm_config.get("max_completion_tokens", 4096),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 提取文本内容
    def get_text_content(content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    result_text = get_text_content(response.content)
    
    # 解析JSON结果
    review_industries: List[Dict] = []
    try:
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            review_industries = json.loads(json_match.group())
        else:
            lines = result_text.split('\n')
            current_industry: Optional[Dict] = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    if current_industry:
                        review_industries.append(current_industry)
                    industry_name = line.split('：')[0].split('.')[1].strip() if '：' in line else line.split('.')[1].strip()
                    current_industry = {"name": industry_name, "reason": ""}
                elif current_industry and line.startswith(('依据', '支撑', '理由')):
                    current_industry["reason"] = line.split('：')[1].strip() if '：' in line else line
            if current_industry:
                review_industries.append(current_industry)
    except Exception as e:
        review_industries = [
            {"name": "半导体", "reason": "机构关注政策支持和技术突破"},
            {"name": "光伏设备", "reason": "业绩支撑明显，需求旺盛"}
        ]
    
    return ReviewIndustryAnalysisOutput(review_industries=review_industries)


# ==================== 节点2-3：行业汇总节点 ====================
def industry_merge_node(state: IndustryMergeInput, config: RunnableConfig, runtime: Runtime[Context]) -> IndustryMergeOutput:
    """
    title: 行业汇总
    desc: 合并去重两个智能体输出的行业，按优先级排序
    integrations: 无
    """
    ctx = runtime.context
    
    # 提取两个列表的行业名称
    guba_industry_names = set()
    for item in state.guba_industries:
        if isinstance(item, dict) and "name" in item:
            guba_industry_names.add(item["name"])
    
    review_industry_names = set()
    for item in state.review_industries:
        if isinstance(item, dict) and "name" in item:
            review_industry_names.add(item["name"])
    
    # 找出交集（同时出现在两个列表中的行业）
    intersection = guba_industry_names & review_industry_names
    
    # 找出并集
    all_industries = guba_industry_names | review_industry_names
    
    # 构建最终列表：交集排前面，单独出现的排后面
    final_industries: List[Dict] = []
    
    # 先添加交集行业
    for industry_name in intersection:
        # 从原列表中找到支撑依据
        reason = ""
        for item in state.guba_industries:
            if isinstance(item, dict) and item.get("name") == industry_name:
                reason = item.get("reason", "")
                break
        
        final_industries.append({
            "name": industry_name,
            "reason": reason,
            "source": "both"  # 表示两个来源都提到
        })
    
    # 再添加单独出现的行业
    for industry_name in all_industries:
        if industry_name not in intersection:
            # 找支撑依据
            reason = ""
            for item in state.guba_industries:
                if isinstance(item, dict) and item.get("name") == industry_name:
                    reason = item.get("reason", "")
                    break
            
            if not reason:
                for item in state.review_industries:
                    if isinstance(item, dict) and item.get("name") == industry_name:
                        reason = item.get("reason", "")
                        break
            
            final_industries.append({
                "name": industry_name,
                "reason": reason,
                "source": "single"
            })
    
    # 限制数量
    final_industries = final_industries[:10]
    
    return IndustryMergeOutput(final_industries=final_industries)


# ==================== 节点3-1：行业关联分析智能体 ====================
def industry_network_analysis_node(state: IndustryNetworkAnalysisInput, config: RunnableConfig, runtime: Runtime[Context]) -> IndustryNetworkAnalysisOutput:
    """
    title: 行业关联分析
    desc: 挖掘每个热门行业的关联子行业、上下游板块或协同发展行业，构建行业节点关系网络
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        cfg = json.load(fd)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up_template = cfg.get("up", "")
    
    # 渲染用户提示词
    from jinja2 import Template
    up_tpl = Template(up_template)
    user_prompt = up_tpl.render(
        final_industries=state.final_industries,
        guba_topics=state.guba_topics,
        economy_reviews=state.economy_reviews
    )
    
    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        max_completion_tokens=llm_config.get("max_completion_tokens", 8192),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 提取文本内容
    def get_text_content(content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    industry_network = get_text_content(response.content)
    
    return IndustryNetworkAnalysisOutput(industry_network=industry_network)


# ==================== 节点4-1：行业情绪分析智能体 ====================
def industry_sentiment_analysis_node(state: IndustrySentimentAnalysisInput, config: RunnableConfig, runtime: Runtime[Context]) -> IndustrySentimentAnalysisOutput:
    """
    title: 行业情绪分析
    desc: 分析每个热门行业的市场情绪（乐观/中性/悲观）
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        cfg = json.load(fd)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up_template = cfg.get("up", "")
    
    # 渲染用户提示词
    from jinja2 import Template
    up_tpl = Template(up_template)
    user_prompt = up_tpl.render(
        final_industries=state.final_industries,
        guba_topics=state.guba_topics,
        economy_reviews=state.economy_reviews
    )
    
    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        max_completion_tokens=llm_config.get("max_completion_tokens", 8192),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 提取文本内容
    def get_text_content(content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    industry_sentiment = get_text_content(response.content)
    
    return IndustrySentimentAnalysisOutput(industry_sentiment=industry_sentiment)


# ==================== 节点5-1：行业研报抓取 ====================

def industry_report_collect_node(state: IndustryReportCollectInput, config: RunnableConfig, runtime: Runtime[Context]) -> IndustryReportCollectOutput:
    """
    title: 行业研报抓取
    desc: 基于final_industries中的热门行业板块，访问每个行业对应的研报页面，获取研报的标题和内容
    integrations: 无
    """
    ctx = runtime.context
    industry_reports: List[Dict] = []
    error_message: str = ""

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://data.eastmoney.com/",
        }

        # 从 final_industries 中提取行业名称
        target_industries = state.final_industries

        if not target_industries:
            error_message = "final_industries 为空，无法抓取研报"
            return IndustryReportCollectOutput(industry_reports=industry_reports, error_message=error_message)

        # 提取行业名称列表
        industry_names = []
        for industry in target_industries:
            if isinstance(industry, dict):
                industry_name = industry.get('name', '')
                if industry_name:
                    industry_names.append(industry_name)
            elif isinstance(industry, str):
                industry_names.append(industry)

        print(f"需要抓取研报的行业: {industry_names}")
        print(f"  共 {len(industry_names)} 个行业需要处理")

        # 步骤1：获取行业板块列表，建立行业名称到代码的映射
        industry_code_mapping: Dict[str, str] = {}  # 行业名称 -> 行业代码

        # 备用硬编码映射表（东财研报页面使用的行业代码）
        # 注意：这里使用的是东财研报系统的行业代码，与资金流板块代码不同
        # 重要：必须包含带"行业"后缀的完整名称
        industry_code_mapping = {
            # 食品饮料相关
            "酿酒行业": "477",
            "白酒": "477",
            "白酒行业": "438",  # 白酒行业 -> 食品饮料
            "酿酒": "477",
            "食品饮料": "438",
            "食品": "438",
            "饮料": "438",

            # 医药相关
            "化学制药": "465",
            "医药": "465",
            "医药行业": "465",
            "生物制品": "548",
            "生物医药": "548",
            "生物制药": "465",
            "创新药": "1106",

            # 科技相关
            "半导体": "917",
            "芯片": "917",
            "集成电路": "917",
            "存储芯片": "917",
            "电子元件": "459",
            "电子": "459",

            # 通信相关
            "通信设备": "448",
            "通信": "448",
            "光通信": "448",
            "光纤": "448",
            "互联网服务": "447",
            "互联网": "447",

            # AI算力相关
            "人工智能": "800",
            "AI": "800",
            "AI算力": "800",
            "算力": "800",
            "AI算力硬件": "800",
            "算力硬件": "800",
            "算力产业链": "800",
            "AI算力行业": "800",
            "AI算力硬件行业": "800",
            "人工智能算力行业": "800",  # 新增
            "AI应用": "800",  # 新增

            # 能源相关
            "光伏": "588",
            "光伏设备": "1031",
            "电池": "574",
            "锂电池": "574",
            "电源设备": "457",

            # 汽车相关
            "汽车整车": "429",
            "汽车": "429",
            "汽车零部件": "481",

            # 房地产
            "房地产开发": "451",
            "房地产": "451",

            # 银行
            "银行": "475",

            # 家电
            "家电行业": "456",
            "家电": "456",

            # 商业百货
            "商业百货": "482",
            "零售": "482",

            # 有色金属
            "有色金属": "478",
            "小金属": "478",
            "钨": "478",
            "小金属行业": "478",

            # 贵金属
            "贵金属": "732",
            "贵金属行业": "732",  # 贵金属行业 -> 贵金属
            "黄金": "547",
            "白银": "521",

            # 化工
            "化学制品": "538",
            "化工": "538",
            "化工原料": "512",
            "化工行业": "538",  # 新增
            "高性能纤维材料": "538",  # 新增（归类到化工）

            # 旅游
            "旅游酒店": "485",
            "旅游": "485",
            "旅游概念": "692",

            # 物流
            "物流行业": "422",
            "物流": "422",
            "冷链物流": "852",

            # 电力
            "电力行业": "428",
            "电力": "428",

            # 农牧
            "农牧饲渔": "433",
            "农业": "433",
            "农业种植": "888",

            # 通用设备
            "通用设备": "545",
            "机械": "545",
            "工程机械": "539",
            "专用设备": "910",

            # 机器人相关
            "人形机器人": "800",
            "机器人": "545",
            "人形机器人材料": "800",

            # 石油
            "石油行业": "464",
            "石油": "464",
            "油气设服": "606",

            # 游戏
            "游戏": "509",
            "网络游戏": "853",

            # 美容护理
            "美容护理": "436",

            # 其他
            "铁路公路": "421",
            "水泥建材": "424",
            "建材": "424",
            "建筑材料": "424",
            "钢铁行业": "479",
            "钢铁": "479",
            "航天航空": "480",
            "商业航天": "480",
            "商业航天行业": "480",  # 商业航天行业 -> 航天航空
            "环保行业": "728",
            "环保": "728",
            "军工": "490",
        }

        print(f"  备用映射包含 {len(industry_code_mapping)} 个行业")

        # 计算近10天的日期
        date_10_days_ago = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')

        # 建立行业名称到关键词的映射
        # 对于每个目标行业，定义用于匹配的关键词
        industry_keywords = {}
        for target_industry in industry_names:
            # 预处理行业名称
            target_industry_clean = target_industry.replace("行业", "").replace("板块", "").strip()
            target_industry_clean = target_industry_clean.replace("硬件", "").replace("产业链", "").strip()
            
            keywords = [target_industry_clean]
            
            # 添加同义词
            if "商业航天" in target_industry_clean or "航天" in target_industry_clean:
                keywords.extend(["航天", "航空", "商业航天", "航天航空"])
            elif "贵金属" in target_industry_clean:
                keywords.extend(["黄金", "白银", "贵金属"])
            elif "白酒" in target_industry_clean or "酿酒" in target_industry_clean:
                keywords.extend(["白酒", "酿酒", "食品饮料"])
            elif "算力" in target_industry_clean or "AI" in target_industry_clean:
                keywords.extend(["算力", "人工智能", "AI", "计算机"])
            elif "小金属" in target_industry_clean:
                keywords.extend(["小金属", "有色金属"])
            elif "化工" in target_industry_clean:
                keywords.extend(["化工", "化学"])
            
            industry_keywords[target_industry] = keywords
            print(f"  行业 '{target_industry}' 关键词: {keywords}")

        # 步骤2：访问行业研报列表页面
        # URL：https://data.eastmoney.com/report/industry.jshtml
        print(f"  访问行业研报列表页面...")
        industry_report_url = "https://data.eastmoney.com/report/industry.jshtml"
        
        try:
            response = requests.get(industry_report_url, headers=headers, timeout=30)
            response.raise_for_status()
            content = response.text

            # 查找 initdata 变量
            initdata_pattern = r'initdata\s*=\s*(\{.*?\});'
            initdata_match = re.search(initdata_pattern, content, re.DOTALL)

            if not initdata_match:
                print(f"  未找到研报数据")
                return IndustryReportCollectOutput(industry_reports=industry_reports, error_message="未找到研报数据")

            initdata_str = initdata_match.group(1)
            initdata = json.loads(initdata_str)

            if 'data' not in initdata:
                print(f"  研报数据格式异常")
                return IndustryReportCollectOutput(industry_reports=industry_reports, error_message="研报数据格式异常")

            all_reports = initdata['data']
            print(f"  成功获取 {len(all_reports)} 篇研报")

            # 步骤3：对于每篇研报，检查是否匹配目标行业
            matched_reports_by_industry = {}  # 按行业统计匹配的研报数量
            for report in all_reports[:200]:  # 检查前200篇研报，扩大范围
                try:
                    # 提取研报基本信息
                    report_name = report.get('title', '')
                    org_name = report.get('orgSName', report.get('orgName', ''))
                    publish_date_str = report.get('publishDate', '')
                    rating = report.get('emRatingName', report.get('sRatingName', ''))
                    info_code = report.get('infoCode', '')
                    report_industry_name = report.get('industryName', '')

                    # 解析发布日期
                    publish_date = ""
                    if publish_date_str:
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', publish_date_str)
                        if date_match:
                            publish_date = date_match.group(1)

                    # 筛选：只保留近10天的研报
                    if publish_date and publish_date < date_10_days_ago:
                        continue

                    # 如果没有日期，使用当前日期
                    if not publish_date:
                        publish_date = datetime.now().strftime('%Y-%m-%d')

                    # 检查这篇研报是否匹配任何目标行业
                    matched_industry = None
                    
                    for target_industry, keywords in industry_keywords.items():
                        # 检查该行业是否已经有15篇研报
                        if matched_reports_by_industry.get(target_industry, 0) >= 15:
                            continue
                        
                        # 检查标题是否包含关键词
                        for keyword in keywords:
                            if keyword in report_name:
                                matched_industry = target_industry
                                print(f"    ✓ 通过关键词匹配: '{keyword}' in '{report_name[:50]}...' (目标: {target_industry})")
                                break
                        
                        if matched_industry:
                            break

                    # 如果没有匹配任何目标行业，跳过
                    if not matched_industry:
                        continue

                    # 更新该行业的研报计数
                    matched_reports_by_industry[matched_industry] = matched_reports_by_industry.get(matched_industry, 0) + 1

                    # 获取研报内容
                    report_content_url = f"https://data.eastmoney.com/report/zw_industry.jshtml?infocode={info_code}"
                    report_content = ""

                    try:
                        content_response = requests.get(report_content_url, headers=headers, timeout=30)
                        content_response.raise_for_status()
                        content_html = content_response.text

                        # 尝试提取研报内容
                        content_patterns = [
                            r'"content":\s*"([^"]+)"',
                            r'"summary":\s*"([^"]+)"',
                            r'"abstract":\s*"([^"]+)"',
                            r'data-value="([^"]+)"',
                        ]

                        for pattern in content_patterns:
                            content_match = re.search(pattern, content_html)
                            if content_match:
                                content_text = content_match.group(1)
                                content_text = unescape(content_text)
                                content_text = re.sub(r'<[^>]+>', '', content_text)
                                content_text = re.sub(r'\s+', ' ', content_text).strip()
                                if len(content_text) > 50:
                                    report_content = content_text
                                    break

                        if not report_content:
                            soup = BeautifulSoup(content_html, 'html.parser')
                            paragraphs = soup.find_all('p')
                            if paragraphs:
                                content_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                                if len(content_text) > 50:
                                    report_content = content_text

                        if not report_content:
                            report_content = report_name

                    except Exception as e:
                        print(f"    获取研报内容失败: {str(e)[:50]}")
                        report_content = report_name

                    # 添加到结果
                    industry_reports.append({
                        "industry_name": matched_industry,
                        "board_code": industry_code_mapping.get(matched_industry, ""),
                        "report_name": report_name,
                        "content": report_content,
                        "rating": rating if rating else "暂无评级",
                        "institution": org_name if org_name else "暂无机构",
                        "publish_date": publish_date,
                        "info_code": info_code,
                        "url": f"https://data.eastmoney.com/report/{info_code}.html"
                    })
                    print(f"    抓取研报: {report_name[:40]}... (内容长度: {len(report_content)} 字符)")

                except Exception as e:
                    print(f"    处理研报项失败: {str(e)[:100]}")
                    continue

            print(f"  共筛选出 {len(industry_reports)} 篇匹配的研报")

        except Exception as e:
            print(f"  获取行业研报失败: {e}")
            error_message = f"获取行业研报失败: {str(e)}"

            # 限制总数量
            industry_reports = industry_reports[:30]

            # 统计每个行业的研报数量
            report_count_by_industry = {}
            for report in industry_reports:
                industry = report.get('industry_name', '未知')
                report_count_by_industry[industry] = report_count_by_industry.get(industry, 0) + 1

            print(f"总共抓取到 {len(industry_reports)} 篇行业研报")
            for industry, count in report_count_by_industry.items():
                print(f"  - {industry}: {count} 篇")

            if len(industry_reports) == 0:
                error_message = f"未找到目标行业的研报数据，目标行业: {industry_names}"

    except Exception as e:
        error_message = f"行业研报抓取失败: {str(e)}"
        print(f"错误: {error_message}")

    return IndustryReportCollectOutput(industry_reports=industry_reports, error_message=error_message)

# ==================== 节点5-2：行业资金流抓取 ====================
def industry_capital_flow_collect_node(state: IndustryCapitalFlowCollectInput, config: RunnableConfig, runtime: Runtime[Context]) -> IndustryCapitalFlowCollectOutput:
    """
    title: 行业资金流抓取
    desc: 基于final_industries中的热门行业板块，抓取每个板块的资金流数据，使用用户指定的URL格式
    integrations: 无
    """
    ctx = runtime.context
    industry_capital_flow: List[Dict] = []
    error_message: str = ""

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://data.eastmoney.com/",
        }

        # 获取 final_industries 中的行业名称
        target_industries = state.final_industries

        if not target_industries:
            error_message = "final_industries 为空，无法抓取资金流"
            return IndustryCapitalFlowCollectOutput(industry_capital_flow=industry_capital_flow, error_message=error_message)

        # 提取行业名称列表
        industry_names = []
        for industry in target_industries:
            if isinstance(industry, dict):
                industry_name = industry.get('name', '')
                if industry_name:
                    industry_names.append(industry_name)
            elif isinstance(industry, str):
                industry_names.append(industry)

        print(f"需要抓取资金流的行业: {industry_names}")

        # 步骤1：使用完整的行业代码映射表（不依赖API）
        industry_code_mapping: Dict[str, str] = {
            # 石油相关
            "石油": "0464",
            "石油行业": "0464",
            "石油石化": "0464",
            "石油开采与加工": "0464",
            "石油开采与加工行业": "0464",
            "油气设服": "0606",
            
            # 天然气
            "天然气": "0625",
            "天然气行业": "0625",
            
            # 氢能源
            "氢能": "0670",
            "氢能源": "0670",
            
            # 云计算
            "云计算": "0830",
            "云计算行业": "0830",
            "云服务": "0830",
            
            # 航运港口
            "航运": "0599",
            "港口": "0599",
            "航运港口": "0599",
            "港口航运": "0599",
            
            # 汽车相关
            "汽车": "0429",
            "汽车行业": "0429",
            "汽车整车": "0429",
            "汽车零部件": "0481",
            
            # 电力相关
            "电力": "0428",
            "电力行业": "0428",
            "电力设备": "0428",
            "电力设备行业": "0428",
            
            # 半导体
            "半导体": "0917",
            "芯片": "1137",
            "集成电路": "1137",
            "存储芯片": "1137",
            
            # 人工智能
            "人工智能": "0800",
            "AI": "0800",
            "AI智能体": "0800",
            "人工智能（AI智能体）": "0800",
            "人工智能（AI智能体）行业": "0800",
            "AI应用": "0800",
            "AI算力": "1134",
            "算力": "1134",
            
            # 医药生物
            "医药": "0465",
            "医药行业": "0465",
            "医药生物": "0465",
            "医药生物行业": "0465",
            "生物制品": "0548",
            "生物医药": "0548",
            
            # 其他常见行业
            "食品饮料": "0438",
            "白酒": "0438",
            "酿酒": "0477",
            "化学制药": "0465",
            "通信设备": "0448",
            "通信": "0448",
            "光伏": "0588",
            "锂电池": "0574",
            "有色金属": "0478",
            "贵金属": "0732",
            "黄金": "0547",
            "化工": "0538",
            "钢铁": "0479",
            "军工": "0490",
            "航天航空": "0480",
            "环保": "0728",
            "家电": "0456",
            "银行": "0475",
            "房地产": "0451",
            "建筑": "0424",
            "建材": "0424",
            "工程机械": "0539",
            "通用设备": "0545",
            "专用设备": "0910",
            "电子": "0459",
            "电子元件": "0459",
            "游戏": "0509",
            "旅游": "0485",
            "物流": "0422",
            "农牧": "0433",
        }
        
        print(f"  使用行业代码映射表，共 {len(industry_code_mapping)} 个行业")

        # 步骤2：对于每个目标行业，使用指定的URL格式抓取资金流
        for target_industry in industry_names:
            try:
                # 预处理行业名称：去除常见后缀
                target_industry_clean = target_industry
                target_industry_clean = target_industry_clean.replace("行业", "").replace("板块", "").strip()
                target_industry_clean = target_industry_clean.replace("硬件", "").replace("产业链", "").strip()
                
                print(f"  处理行业: {target_industry} -> {target_industry_clean}")
                
                # 查找板块代码
                board_code = None
                matched_industry_name = None
                
                # 调试：打印当前映射表的前10个条目
                if target_industry == industry_names[0]:  # 只在第一个行业时打印
                    print(f"  映射表样例（前10个）: {list(industry_code_mapping.items())[:10]}")
                    print(f"  映射表总数: {len(industry_code_mapping)} 个行业")
                
                # 优先精确匹配
                for industry_name, code in industry_code_mapping.items():
                    if target_industry_clean == industry_name:
                        board_code = code
                        matched_industry_name = industry_name
                        print(f"  精确匹配成功: {target_industry_clean} == {industry_name} -> {code}")
                        break
                
                # 如果精确匹配失败，使用模糊匹配
                if not board_code:
                    for industry_name, code in industry_code_mapping.items():
                        # 检查是否包含关键词
                        if (target_industry_clean in industry_name or 
                            industry_name in target_industry_clean or
                            (len(target_industry_clean) >= 2 and target_industry_clean in industry_name)):
                            board_code = code
                            matched_industry_name = industry_name
                            break
                
                if not board_code:
                    print(f"  警告: 未找到行业 '{target_industry}' 的代码映射，跳过")
                    continue
                
                print(f"  匹配行业: {target_industry} -> {matched_industry_name} (代码: {board_code})")

                # 构造资金流板块代码：BK + 4位数字代码
                # 检查代码是否已经包含BK前缀
                if board_code.startswith("BK"):
                    # 已经包含BK前缀，直接使用
                    board_code_full = board_code
                else:
                    # 没有包含BK前缀，需要加上
                    # 如果代码不足4位，在前面补0
                    clean_code = board_code
                    if len(clean_code) < 4:
                        clean_code = clean_code.zfill(4)
                    board_code_full = f"BK{clean_code}"
                
                # 构造URL：https://data.eastmoney.com/bkzj/{板块代码}.html
                flow_url = f"https://data.eastmoney.com/bkzj/{board_code_full}.html"
                print(f"  访问资金流页面: {flow_url}")

                # 使用API获取该板块的资金流数据
                # API格式：secids=90.{板块代码}
                capital_api_url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87&secids=90.{board_code_full}&ut=fa5fd1943c7b386f172d6893dbfba10b"
                
                print(f"  调用API: {capital_api_url}")
                
                try:
                    response = requests.get(capital_api_url, headers=headers, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                except Exception as e:
                    print(f"  请求失败: {e}，跳过")
                    continue

                if 'data' not in data or data['data'] is None or 'diff' not in data['data']:
                    print(f"  API响应格式异常，跳过")
                    print(f"  响应内容: {data}")
                    continue

                boards = data['data']['diff']
                print(f"  成功获取 {len(boards)} 个板块的资金流数据")

                for board in boards:
                    try:
                        industry_name = board.get('f14', '')
                        code = board.get('f12', '')

                        if not industry_name or not code:
                            continue

                        # 提取资金流数据
                        change_percent = board.get('f3', 0)
                        if change_percent is not None:
                            change_percent = f"{change_percent:.2f}%"

                        main_net_inflow = board.get('f62', 0)
                        if main_net_inflow is not None:
                            main_net_inflow = f"{main_net_inflow/10000:.2f}万" if abs(main_net_inflow) < 100000000 else f"{main_net_inflow/100000000:.2f}亿"

                        net_inflow_ratio = board.get('f184', 0)
                        if net_inflow_ratio is not None:
                            net_inflow_ratio = f"{net_inflow_ratio:.2f}%"

                        super_large_net_inflow = board.get('f66', 0)
                        if super_large_net_inflow is not None:
                            super_large_net_inflow = f"{super_large_net_inflow/10000:.2f}万" if abs(super_large_net_inflow) < 100000000 else f"{super_large_net_inflow/100000000:.2f}亿"

                        large_net_inflow = board.get('f72', 0)
                        if large_net_inflow is not None:
                            large_net_inflow = f"{large_net_inflow/10000:.2f}万" if abs(large_net_inflow) < 100000000 else f"{large_net_inflow/100000000:.2f}亿"

                        medium_net_inflow = board.get('f78', 0)
                        if medium_net_inflow is not None:
                            medium_net_inflow = f"{medium_net_inflow/10000:.2f}万" if abs(medium_net_inflow) < 100000000 else f"{medium_net_inflow/100000000:.2f}亿"

                        small_net_inflow = board.get('f84', 0)
                        if small_net_inflow is not None:
                            small_net_inflow = f"{small_net_inflow/10000:.2f}万" if abs(small_net_inflow) < 100000000 else f"{small_net_inflow/100000000:.2f}亿"

                        # 添加到结果
                        industry_capital_flow.append({
                            "industry_name": target_industry,  # 使用用户输入的行业名称
                            "board_code": board_code_full,
                            "rank_type": "今日",
                            "code": code,
                            "name": target_industry,  # 使用用户输入的行业名称
                            "latest_price": str(board.get('f2', 0)),
                            "change_percent": change_percent,
                            "main_net_inflow": main_net_inflow,
                            "net_inflow_ratio": net_inflow_ratio,
                            "super_large_net_inflow": super_large_net_inflow,
                            "large_net_inflow": large_net_inflow,
                            "medium_net_inflow": medium_net_inflow,
                            "small_net_inflow": small_net_inflow,
                            "url": flow_url
                        })

                    except Exception as e:
                        print(f"  处理板块数据失败: {str(e)[:100]}")
                        continue

                # 添加延迟避免请求过快
                time.sleep(1)

            except Exception as e:
                print(f"  抓取行业 '{target_industry}' 的资金流失败: {e}")
                continue

        print(f"总共抓取到 {len(industry_capital_flow)} 条资金流数据")

        if len(industry_capital_flow) == 0:
            error_message = f"未找到目标行业的资金流数据，目标行业: {industry_names}"

    except Exception as e:
        error_message = f"行业资金流抓取失败: {str(e)}"
        print(f"错误: {error_message}")

    return IndustryCapitalFlowCollectOutput(industry_capital_flow=industry_capital_flow, error_message=error_message)


# ==================== 节点6-1：研报&资金流分析智能体 ====================
def research_capital_analysis_node(state: ResearchCapitalAnalysisInput, config: RunnableConfig, runtime: Runtime[Context]) -> ResearchCapitalAnalysisOutput:
    """
    title: 研报&资金流分析
    desc: 分析热门行业的投资价值，汇总研报评级分布和资金流趋势
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        cfg = json.load(fd)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up_template = cfg.get("up", "")
    
    # 渲染用户提示词
    from jinja2 import Template
    up_tpl = Template(up_template)
    user_prompt = up_tpl.render(
        industry_reports=state.industry_reports,
        industry_capital_flow=state.industry_capital_flow,
        final_industries=state.final_industries
    )
    
    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        max_completion_tokens=llm_config.get("max_completion_tokens", 8192),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 提取文本内容
    def get_text_content(content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    research_capital_analysis = get_text_content(response.content)
    
    return ResearchCapitalAnalysisOutput(research_capital_analysis=research_capital_analysis)


# ==================== 节点7-1：综合交易策略生成智能体 ====================
def trading_strategy_generate_node(state: TradingStrategyGenerateInput, config: RunnableConfig, runtime: Runtime[Context]) -> TradingStrategyGenerateOutput:
    """
    title: 综合交易策略生成
    desc: 结合所有分析结果，生成5日短线交易策略
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        cfg = json.load(fd)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up_template = cfg.get("up", "")
    
    # 渲染用户提示词
    from jinja2 import Template
    up_tpl = Template(up_template)
    
    # 准备行业评级信息
    ratings_summary = ""
    for rating in state.industry_ratings:
        ratings_summary += f"\n- {rating.get('industry_name', '')}: {rating.get('rating', '')}级 ({rating.get('category', '')})"
    
    user_prompt = up_tpl.render(
        industry_network=state.industry_network,
        industry_sentiment=state.industry_sentiment,
        research_capital_analysis=state.research_capital_analysis,
        v_insights_analysis=state.v_insights_analysis,
        industry_ratings=ratings_summary
    )
    
    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        max_completion_tokens=llm_config.get("max_completion_tokens", 16384),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 提取文本内容
    def get_text_content(content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    trading_strategy = get_text_content(response.content)
    
    return TradingStrategyGenerateOutput(trading_strategy=trading_strategy)


# ==================== 节点8-1：大V博客抓取 ====================
def v_blog_collect_node(state: VBlogCollectInput, config: RunnableConfig, runtime: Runtime[Context]) -> VBlogCollectOutput:
    """
    title: 大V博客抓取
    desc: 从东方财富博客主页（https://blog.eastmoney.com/）抓取今日热门博主的所有文章
    integrations: 无
    """
    ctx = runtime.context
    blog_posts: List[Dict] = []
    error_message: str = ""
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://blog.eastmoney.com/",
        }
        
        print("步骤1: 获取热门博主列表...")
        bloggers_url = "https://blog.eastmoney.com/hotbloger.html"
        
        # 获取热门博主列表
        response = requests.get(bloggers_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取博主名称
        bloggers = set()
        for li in soup.find_all('li'):
            a = li.find('a', href=True)
            if a:
                href = a.get('href', '')
                if isinstance(href, str) and href.startswith('//i.eastmoney.com/'):
                    blogger_name = a.get_text(strip=True)
                    if blogger_name:
                        bloggers.add(blogger_name)
        
        print(f"  找到 {len(bloggers)} 个热门博主")
        
        print("\n步骤2: 获取主页所有文章...")
        home_url = "https://blog.eastmoney.com/"
        response = requests.get(home_url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取所有文章链接
        all_links = set()
        for a in soup.find_all('a', href=True):
            href: str = a.get('href', '')
            if isinstance(href, str) and 'caifuhao.eastmoney.com/news/' in href:
                if href.startswith('//'):
                    href = 'https:' + href
                all_links.add(href)
        
        print(f"  主页共有 {len(all_links)} 篇文章")
        
        print("\n步骤3: 提取今日文章并按作者分类...")
        today = datetime.now().strftime('%Y-%m-%d')
        today_articles_by_author = {}
        
        # 限制检查的文章数量（避免请求过多）
        max_check_articles = 100
        checked_count = 0
        
        for link in list(all_links):
            if checked_count >= max_check_articles:
                break
            
            try:
                resp = requests.get(link, headers=headers, timeout=30)
                soup2 = BeautifulSoup(resp.text, 'html.parser')
                
                # 提取发布日期
                article_id = link.split('/')[-1]
                if len(article_id) >= 8:
                    publish_date = f"{article_id[:4]}-{article_id[4:6]}-{article_id[6:8]}"
                    
                    if publish_date == today:
                        # 提取作者
                        scripts = soup2.find_all('script')
                        author = "未知"
                        for script in scripts:
                            if script.string and 'nickname' in script.string:
                                match = re.search(r'nickname:"([^"]+)"', script.string)
                                if match:
                                    author = match.group(1)
                                    break
                        
                        # 提取标题
                        title = soup2.find('h1', class_='article-title')
                        title_text = title.get_text(strip=True) if title else "未找到"
                        
                        # 提取内容
                        content_div = soup2.find('div', class_='g_content')
                        content_text = content_div.get_text(strip=True) if content_div else ""
                        
                        if author not in today_articles_by_author:
                            today_articles_by_author[author] = []
                        
                        today_articles_by_author[author].append({
                            'title': title_text,
                            'url': link,
                            'content': content_text,
                            'publish_date': publish_date
                        })
                
                checked_count += 1
                
            except Exception as e:
                checked_count += 1
                pass
        
        print(f"  今日文章作者数: {len(today_articles_by_author)}")
        
        print("\n步骤4: 筛选热门博主的今日文章...")
        for author, articles in today_articles_by_author.items():
            # 检查作者是否在热门博主列表中
            if author in bloggers:
                for article in articles:
                    blog_posts.append({
                        'author': author,
                        'title': article['title'],
                        'url': article['url'],
                        'content': article['content'],
                        'publish_date': article['publish_date'],
                        'views': 0,
                        'comments': 0,
                        'likes': 0
                    })
        
        print(f"  热门博主的今日文章数: {len(blog_posts)}")
        
        # 显示结果
        print(f"\n热门博主今日文章列表（共{len(blog_posts)}篇）:")
        for i, article in enumerate(blog_posts[:10], 1):
            print(f"  {i}. [{article['author']}] {article['title'][:50]}...")
        
        if len(blog_posts) > 10:
            print(f"  ... 还有 {len(blog_posts) - 10} 篇文章")
        
    except Exception as e:
        error_message = f"大V博客抓取失败: {str(e)}"
        print(f"错误: {error_message}")
    
    return VBlogCollectOutput(blog_posts=blog_posts, error_message=error_message)


# ==================== 节点9-1：大V智能体分析 ====================
def v_insights_analysis_node(state: VInsightsAnalysisInput, config: RunnableConfig, runtime: Runtime[Context]) -> VInsightsAnalysisOutput:
    """
    title: 大V智能体分析
    desc: 分析大V博客内容，提取股票行业和股票投资建议
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        cfg = json.load(fd)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up_template = cfg.get("up", "")
    
    # 渲染用户提示词
    from jinja2 import Template
    up_tpl = Template(up_template)
    
    # 准备博客文章摘要
    blog_summary = ""
    for post in state.blog_posts[:20]:  # 限制最多20篇文章
        blog_summary += f"\n【作者：{post.get('author', '未知')}】\n"
        blog_summary += f"标题：{post.get('title', '')}\n"
        blog_summary += f"内容：{post.get('content', '')[:500]}...\n"
    
    # 准备热门行业列表
    industry_list = "\n".join([f"- {ind.get('name', '')}" for ind in state.final_industries])
    
    user_prompt = up_tpl.render(
        blog_posts=blog_summary,
        industry_list=industry_list
    )
    
    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        max_completion_tokens=llm_config.get("max_completion_tokens", 8192),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 提取文本内容
    def get_text_content(content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    v_insights_analysis = get_text_content(response.content)
    
    return VInsightsAnalysisOutput(v_insights_analysis=v_insights_analysis)


# ==================== 节点10-1：行业评级更新 ====================
def industry_rating_update_node(state: IndustryRatingUpdateInput, config: RunnableConfig, runtime: Runtime[Context]) -> IndustryRatingUpdateOutput:
    """
    title: 行业评级更新
    desc: 基于智能体分析结果更新行业评级，支持评级升降级和分类
    integrations: 大语言模型, 数据库
    """
    ctx = runtime.context
    
    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        cfg = json.load(fd)
    
    llm_config = cfg.get("config", {})
    sp = cfg.get("sp", "")
    up_template = cfg.get("up", "")
    
    # 准备行业信息
    industry_info = ""
    for ind in state.final_industries:
        industry_info += f"\n行业：{ind.get('name', '')}\n"
        industry_info += f"原因：{ind.get('reason', '')}\n"
    
    # 准备情绪分析
    sentiment_summary = state.industry_sentiment[:2000] if state.industry_sentiment else ""
    
    # 准备资金流信息
    capital_info = ""
    for cf in state.industry_capital_flow[:10]:
        capital_info += f"\n{cf.get('name', '')}: 主力资金{cf.get('main_net_inflow', '')}，涨幅{cf.get('change_percent', '')}\n"
    
    # 渲染用户提示词
    from jinja2 import Template
    up_tpl = Template(up_template)
    user_prompt = up_tpl.render(
        industry_info=industry_info,
        sentiment_summary=sentiment_summary,
        capital_info=capital_info
    )
    
    # 调用大模型获取评级
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.5),
        max_completion_tokens=llm_config.get("max_completion_tokens", 8192),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 提取评级结果
    def get_text_content(content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], str):
                return " ".join(content)
            else:
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)
        return str(content)
    
    rating_result = get_text_content(response.content)
    
    # 解析评级结果（假设大模型返回JSON格式）
    try:
        # 尝试从大模型输出中提取JSON
        json_match = re.search(r'\{[\s\S]*\}', rating_result)
        if json_match:
            ratings_data = json.loads(json_match.group())
        else:
            # 如果没有JSON，创建默认评级
            ratings_data = {}
            for ind in state.final_industries:
                ratings_data[ind.get('name', '')] = {
                    "rating": "B",
                    "category": "短期可关注"
                }
    except:
        # 解析失败，创建默认评级
        ratings_data = {}
        for ind in state.final_industries:
            ratings_data[ind.get('name', '')] = {
                "rating": "B",
                "category": "短期可关注"
            }
    
    # 更新数据库
    from coze_coding_dev_sdk.database import get_session
    from storage.database.industry_rating_manager import IndustryRatingManager, IndustryRatingCreate
    
    db = get_session()
    try:
        mgr = IndustryRatingManager()
        
        # 先降级所有非热点行业
        mgr.downgrade_non_hot(db)
        
        # 更新当前热点行业
        industry_ratings = []
        for ind in state.final_industries:
            industry_name = ind.get('name', '')
            rating_info = ratings_data.get(industry_name, {"rating": "B", "category": "短期可关注"})
            
            # 创建或更新行业评级
            industry = mgr.create_or_update(db, industry_name, IndustryRatingCreate(
                industry_name=industry_name,
                rating=rating_info.get('rating', 'B'),
                category=rating_info.get('category', '短期可关注'),
                is_hot=True
            ))
            
            industry_ratings.append({
                "industry_name": industry.industry_name,
                "rating": industry.rating,
                "category": industry.category,
                "is_hot": industry.is_hot,
                "rating_date": str(industry.rating_date) if industry.rating_date else ""
            })
        
        # 获取所有行业评级
        all_ratings = mgr.get_all(db, limit=100)
        
        # 生成可视化数据（树状结构）
        visualization_data = {
            "short_term": [],
            "mid_term": [],
            "potential": [],
            "downtrend": []
        }
        
        for ind in all_ratings:
            category = ind.category or "未分类"
            if "短期" in category:
                visualization_data["short_term"].append({
                    "name": ind.industry_name,
                    "rating": ind.rating
                })
            elif "中期" in category:
                visualization_data["mid_term"].append({
                    "name": ind.industry_name,
                    "rating": ind.rating
                })
            elif "潜在" in category:
                visualization_data["potential"].append({
                    "name": ind.industry_name,
                    "rating": ind.rating
                })
            elif "下跌" in category:
                visualization_data["downtrend"].append({
                    "name": ind.industry_name,
                    "rating": ind.rating
                })
        
    finally:
        db.close()
    
    return IndustryRatingUpdateOutput(
        industry_ratings=industry_ratings,
        rating_visualization=json.dumps(visualization_data, ensure_ascii=False, indent=2)
    )
import os
from datetime import datetime
from typing import List, Dict, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import DocumentGenerationClient

from graphs.state import StrategyPdfUploadInput, StrategyPdfUploadOutput


# ==================== 节点17-1：PDF报告生成与上传 ====================
def strategy_pdf_upload_node(state: StrategyPdfUploadInput, config: RunnableConfig, runtime: Runtime[Context]) -> StrategyPdfUploadOutput:
    """
    title: 交易策略PDF生成与上传
    desc: 将交易策略报告（Markdown格式）转换为PDF并上传到阿里云OSS，返回公开访问链接
    integrations: 无
    """
    ctx = runtime.context
    pdf_url: str = ""
    error_message: str = ""
    
    try:
        # 获取交易策略报告（Markdown格式）
        trading_strategy = state.trading_strategy
        
        if not trading_strategy:
            error_message = "交易策略报告为空，无法生成PDF"
            return StrategyPdfUploadOutput(pdf_url="", error_message=error_message)
        
        # ========== OSS 配置 ==========
        # 请在环境变量中配置以下参数：
        # OSS_ACCESS_KEY_ID: 阿里云 Access Key ID
        # OSS_ACCESS_KEY_SECRET: 阿里云 Access Key Secret
        # OSS_ENDPOINT: OSS Endpoint，例如 oss-cn-beijing.aliyuncs.com
        # OSS_BUCKET_NAME: OSS Bucket 名称
        ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID', '').strip()
        ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET', '').strip()
        ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-beijing.aliyuncs.com').strip()
        BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', '').strip()
        
        if not ACCESS_KEY_ID or not ACCESS_KEY_SECRET or not BUCKET_NAME:
            raise ValueError("OSS配置不完整，请设置环境变量：OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME")
        
        BASE_URL = f'https://{BUCKET_NAME}.{ENDPOINT}'
        
        # 初始化OSS客户端
        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, ENDPOINT, BUCKET_NAME)
        
        # ========== 生成PDF到本地 ==========
        # 先使用DocumentGenerationClient生成PDF，然后下载到本地
        client = DocumentGenerationClient()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = f"trading_strategy_{timestamp}"
        
        print(f"开始生成交易策略PDF...")
        
        # 生成PDF并获取下载链接
        pdf_download_url = client.create_pdf_from_markdown(trading_strategy, title)
        
        if not pdf_download_url:
            error_message = "PDF生成失败，未返回下载链接"
            return StrategyPdfUploadOutput(pdf_url="", error_message=error_message)
        
        # 下载PDF到本地临时文件
        temp_pdf_path = f"/tmp/{title}.pdf"
        print(f"下载PDF到本地: {temp_pdf_path}")
        
        pdf_response = requests.get(pdf_download_url, timeout=30)
        pdf_response.raise_for_status()
        
        with open(temp_pdf_path, 'wb') as f:
            f.write(pdf_response.content)
        
        print(f"PDF下载成功，文件大小: {len(pdf_response.content)} bytes")
        
        # ========== 上传到OSS ==========
        # 生成OSS上的文件名
        date_str = datetime.now().strftime("%Y%m%d")
        oss_filename = f"report_{date_str}_{title}.pdf"
        
        # 设置正确的响应头
        headers = {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'inline; filename="{oss_filename}"',
            'Cache-Control': 'no-cache'
        }
        
        print(f"开始上传到OSS: {oss_filename}")
        
        # 上传文件
        bucket.put_object_from_file(oss_filename, temp_pdf_path, headers=headers)
        
        # 设置公共读权限
        bucket.put_object_acl(oss_filename, oss2.OBJECT_ACL_PUBLIC_READ)
        
        # 生成公开访问URL
        pdf_url = f"{BASE_URL}/{oss_filename}"
        
        print(f"✅ 上传成功：{oss_filename}")
        print(f"📎 公开访问链接：{pdf_url}")
        
        # 删除临时文件
        try:
            os.remove(temp_pdf_path)
            print(f"已删除临时文件: {temp_pdf_path}")
        except Exception as e:
            print(f"删除临时文件失败（可忽略）: {e}")
        
    except Exception as e:
        error_message = f"PDF生成或上传异常: {str(e)}"
        print(f"异常: {error_message}")
        import traceback
        traceback.print_exc()
    
    return StrategyPdfUploadOutput(pdf_url=pdf_url, error_message=error_message)


# ==================== 节点18-1：企业微信机器人推送 ====================
def wecom_bot_send_node(state: WeComBotSendInput, config: RunnableConfig, runtime: Runtime[Context]) -> WeComBotSendOutput:
    """
    title: 企业微信机器人推送
    desc: 将交易策略PDF报告链接发送到企业微信群聊
    integrations: 无
    """
    ctx = runtime.context
    send_status = "失败"
    message = ""
    error_message = ""
    
    try:
        # 企业微信机器人 Webhook URL
        # 请在环境变量 WECOM_WEBHOOK_KEY 中配置企业微信机器人的 Webhook Key
        # 在企业微信群聊中添加机器人后可获取 Webhook 地址
        wecom_webhook_key = os.getenv('WECOM_WEBHOOK_KEY', '')
        if not wecom_webhook_key:
            raise ValueError("企业微信Webhook Key未配置，请设置环境变量：WECOM_WEBHOOK_KEY")
        webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={wecom_webhook_key}"
        
        print(f"开始推送交易策略报告到企业微信...")
        
        # 从交易策略报告中提取关键信息
        trading_strategy = state.trading_strategy
        pdf_url = state.pdf_url
        
        # 提取预期回报率
        # 匹配"整体预期"后面的百分比（格式：**5.8%-6.6%**、**6.7%**、**7.2-8.5%**）
        return_rate_match = re.search(r'整体预期\*\*\s*\|\s*\*\*(\d+\.?\d*%[-到]\d+\.?\d*%|\d+\.?\d*%[-到]\d+\.?\d*%|\d+\.?\d*%|\d+\.?\d*[-到]\d+\.?\d*%|\d+\.?\d*[-到]\d+\.?\d*|\d+\.?\d*)\*\*', trading_strategy)
        expected_return = return_rate_match.group(1) if return_rate_match else "未明确"
        
        # 提取推荐行业
        industries = []
        # 匹配新格式：### 1. 石油石化行业
        industry_pattern = r'###\s*\d+\.\s+([^\n]+)'
        industry_matches = re.findall(industry_pattern, trading_strategy)
        for i, ind in enumerate(industry_matches[:3]):  # 只取前3个行业
            # 提取行业名称（去掉"行业"后缀）
            industry_name = ind.replace("行业", "").strip()
            industries.append(f"{i+1}. {industry_name}")
        
        # 构造 Markdown 消息
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown_content = f"""📊 **股票交易策略报告已生成**

📅 生成时间：{current_time}

📈 预期回报率：**{expected_return}**

📄 **查看完整报告**：
[{current_time} 交易策略报告]({pdf_url})

📌 **推荐行业**：
"""
        
        if industries:
            for ind in industries:
                markdown_content += f"{ind}\n"
        else:
            markdown_content += "未找到推荐行业\n"
        
        markdown_content += "\n💡 **提示**：点击上方链接可查看详细的PDF报告（永久有效）"
        
        # 构造请求体
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": markdown_content
            }
        }
        
        print(f"推送消息内容：\n{markdown_content}")
        
        # 发送请求
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=30)
        
        print(f"企业微信API响应状态码: {response.status_code}")
        print(f"企业微信API响应内容: {response.text}")
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                send_status = "成功"
                message = "交易策略报告已成功推送到企业微信群聊"
            else:
                error_message = f"企业微信API返回错误: {result.get('errmsg', '未知错误')}"
                message = f"推送失败: {error_message}"
        else:
            error_message = f"HTTP请求失败，状态码: {response.status_code}"
            message = f"推送失败: {error_message}"
        
    except Exception as e:
        error_message = f"企业微信推送异常: {str(e)}"
        message = f"推送失败: {error_message}"
        print(f"异常: {error_message}")
    
    print(f"推送结果: {send_status}, 消息: {message}")
    
    return WeComBotSendOutput(
        send_status=send_status,
        message=message,
        error_message=error_message
    )
  
# Sentiment-Driven Stock Screener

**基于多源舆情智能分析的股票筛选与策略生成系统**

*A Multi-Agent Stock Intelligence Platform Powered by LLM Sentiment Analysis*

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4.0-green?logo=langchain)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/VeKiner/sentiment-driven-stock-screener?style=flat&color=yellow)](https://github.com/VeKiner/sentiment-driven-stock-screener/stargazers)
[![Forks](https://img.shields.io/github/forks/VeKiner/sentiment-driven-stock-screener?style=flat&color=green)](https://github.com/VeKiner/sentiment-driven-stock-screener/network/members)

---

[English](#english) · [简介](#简介) · [核心特性](#核心特性) · [系统架构](#系统架构) · [工作流节点](#工作流节点) · [快速开始](#快速开始) · [报告示例](#报告示例) · [项目结构](#项目结构) · [技术栈](#技术栈) · [扩展定制](#扩展定制)

---

## 简介

本项目是一套基于 **LangGraph 工作流引擎** 构建的全自动股票选股与策略生成系统。系统通过多源金融舆情数据（股吧热帖、财经时评、行业研报、资金流向、大 V 博客），结合大语言模型的深度语义理解能力，自动完成从舆情感知到策略输出的完整投研闭环。

> **免责声明**：本项目为技术研究工具，所有生成的策略报告仅供参考，不构成任何投资建议。投资有风险，决策请谨慎。

---

## 核心特性

| 特性 | 说明 |
|:-----|:-----|
| **LLM 多智能体** | 基于 LangGraph 构建 18 节点 DAG，多角色分工并行执行 |
| **全域舆情覆盖** | 股吧热帖、东财财经、行业研报、大 V 博客、资金流向多维采集 |
| **深度语义分析** | 行业关联网络构建、舆情情绪量化、观点抽取与大 V 共识分析 |
| **动态行业评级** | 持久化 A-E 五级行业评级数据库，支持历史趋势追踪 |
| **自动化报告** | Markdown 转 PDF，上传 OSS 生成永久访问链接 |
| **多渠道推送** | 企业微信 / 钉钉 / 飞书机器人，支持 Markdown 富文本 |
| **OpenAI 兼容** | 标准 Chat Completions API，可接入任意 LLM 客户端 |
| **链路追踪** | CozeLoop + LangChain Callback，支持全链路可观测 |

---

## 系统架构

```
用户触发 / API 调用
        |
        v
+--------------------------------------------------+
|              FastAPI HTTP 服务层                   |
|         OpenAI 兼容接口 · 流式 SSE 响应           |
+------------------------+-------------------------+
                         |
                         v
+--------------------------------------------------+
|              LangGraph 工作流引擎                   |
|                (18 节点 DAG)                       |
|                                                  |
|  +--------------------------------------------+  |
|  |              数据抓取层（并行）              |  |
|  |  +----------+ +----------+ +----------+   |  |
|  |  | 股吧热帖  | | 财经时评  | | 行业研报  |   |  |
|  |  |  guba   | |  review  | |  report  |   |  |
|  |  +----------+ +----------+ +----------+   |  |
|  |  +----------+ +----------+               |  |
|  |  | 资金流向  | | 大V博客  |               |  |
|  |  | capital  | |  v_blog  |               |  |
|  |  +----------+ +----------+               |  |
|  +--------------------------------------------+  |
|                        |                         |
|                        v                         |
|  +--------------------------------------------+  |
|  |              AI 智能分析层                  |  |
|  |  +------------+  +------------------+    |  |
|  |  | 行业关联    |  | 舆情情绪量化      |    |  |
|  |  | 网络分析    |  | 研报观点综合      |    |  |
|  |  | industry   |  | v_insights       |    |  |
|  |  | _network   |  | analysis         |    |  |
|  |  +------------+  +------------------+    |  |
|  +--------------------------------------------+  |
|                        |                         |
|                        v                         |
|  +--------------------------------------------+  |
|  |              策略生成层                      |  |
|  |     行业评级 · 交易策略 · 报告推送           |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
                         |
         +---------------+---------------+
         |                               |
         v                               v
+------------------+           +------------------+
|   PostgreSQL     |           |    阿里云 OSS     |
|   行业评级持久化   |           |   PDF 报告存储    |
+------------------+           +------------------+
```

---

## 工作流节点

系统由 **18 个核心节点** 组成，分为三大模块。

### 数据抓取层（并行执行）

| 节点 | 数据源 | 输出 |
|:-----|:-------|:-----|
| `guba_topics_collect` | 东方财富股吧 | 近期热门话题与讨论 |
| `economy_review_collect` | 东财财经频道 | 宏观经济分析文章 |
| `industry_report_collect` | 东财研报中心 | 行业研报（按热门行业定向） |
| `industry_capital_flow_collect` | 东财行情数据 | 行业板块资金流向 |
| `v_blog_collect` | 东财大 V 博客 | 知名财经博主热门文章 |

### AI 智能分析层

| 节点 | 模型 | 输出 |
|:-----|:-----|:-----|
| `guba_industry_analysis` | LLM Agent | 从股吧数据提炼热门投资行业 |
| `review_industry_analysis` | LLM Agent | 从时评数据识别宏观受益行业 |
| `industry_merge` | 逻辑节点 | 融合双源结果，输出热门行业列表 |
| `industry_network_analysis` | LLM Agent | 行业关联网络与联动分析 |
| `industry_sentiment_analysis` | LLM Agent | 各行业舆情情绪与热度量化 |
| `research_capital_analysis` | LLM Agent | 研报观点与资金流信号综合分析 |
| `v_insights_analysis` | LLM Agent | 大 V 博客中的行业与个股观点 |

### 策略生成与输出层

| 节点 | 功能 |
|:-----|:-----|
| `industry_rating_update` | 更新行业 A-E 五级评级，记录历史变更 |
| `trading_strategy_generate` | 生成带买卖价格区间的 2 日完整交易策略 |
| `strategy_pdf_upload` | Markdown 转 PDF，上传 OSS，返回永久链接 |
| `wecom_bot_send` | 推送策略摘要至企业微信群聊（Markdown 富文本） |

---

## 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL 14+（行业评级持久化）
- 阿里云 OSS（PDF 报告存储）
- 企业微信群机器人（策略推送，可选）

### 安装

```bash
git clone https://github.com/VeKiner/sentiment-driven-stock-screener.git
cd sentiment-driven-stock-screener/projects
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 填入你的配置
```

`.env` 配置项说明：

```env
# 数据库
PGDATABASE_URL=postgresql://user:password@localhost:5432/stock_analysis

# 阿里云 OSS
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name

# 企业微信（可选）
WECOM_WEBHOOK_KEY=your_webhook_key

# 日志
LOG_LEVEL=INFO
```

### 启动

```bash
# 本地调试模式
bash scripts/local_run.sh

# HTTP 服务模式（生产）
bash scripts/http_run.sh -p 5000
```

### API 调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:5000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="stock-workflow",
    messages=[{"role": "user", "content": "开始今日股票策略分析"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## 报告示例

以下为系统生成的完整股票策略报告示例。

### 一、市场环境与行业逻辑

当前市场处于科技主线主导的结构性行情阶段，上证指数冲击 4200 点强阻力区，短期存在震荡洗盘预期，但新质生产力相关科技赛道景气度确定性较高，是资金核心配置方向。

| 主线 | 核心逻辑 | 评级 |
|:-----|:--------|:-----|
| 存储芯片 | 供需缺口推动全年涨价周期，2026Q1 净利润同比增长 3735% | A 级 |
| 光模块 / CPO | 下游订单锁定至 2028 年，800G/1.6T 渗透率快速提升 | A 级 |
| 能源金属 | 碳酸锂价格上行，储能需求爆发，盈利预期持续上修 | A 级 |
| 石油石化 | 地缘冲突催化油价走高，短期具备博弈弹性 | B 级 |

### 二、推荐个股分析

#### 存储芯片 - 佰维存储（sh688525）

国内存储芯片封装测试龙头，直接受益于行业涨价周期与 AI 算力存储需求爆发。

| 项目 | 数值 |
|:-----|:-----|
| 买入区间 | 86.00 元 - 90.00 元 |
| 卖出区间 | 108.00 元 - 118.00 元 |
| 预期回报率 | 25.6% |

#### 光模块 / CPO - 中际旭创（sz300308）

全球高速光模块龙头，深度绑定英伟达供应链，800G/1.6T 出货量全球领先。

| 项目 | 数值 |
|:-----|:-----|
| 买入区间 | 185.00 元 - 192.00 元 |
| 卖出区间 | 230.00 元 - 248.00 元 |
| 预期回报率 | 24.7% |

#### 新能源与周期类

| 股票名称 | 代码 | 买入区间 | 卖出区间 | 预期回报率 |
|:---------|:-----|:---------|:---------|:----------|
| 宁德时代 | sz300750 | 265-275 元 | 330-350 元 | 24.5% |
| 天齐锂业 | sz002466 | 78-83 元 | 98-108 元 | 24.2% |
| 中国石油 | sh601857 | 9.2-9.6 元 | 11.5-12.5 元 | 25.3% |

### 三、资金分配方案

| 股票代码 | 股票名称 | 分配金额 | 占比 |
|:---------|:---------|--------:|-----:|
| sh688525 | 佰维存储 | 2500 元 | 25% |
| sz300308 | 中际旭创 | 2500 元 | 25% |
| sz300750 | 宁德时代 | 2000 元 | 20% |
| sz002466 | 天齐锂业 | 2000 元 | 20% |
| sh601857 | 中国石油 | 1000 元 | 10% |
| **合计** | | **10000 元** | **100%** |

### 四、整体预期回报率

| 股票名称 | 预期 2 日回报率 | 预期盈利 |
|:---------|:---------------|--------:|
| 佰维存储 | 25.6% | 640 元 |
| 中际旭创 | 24.7% | 617.5 元 |
| 宁德时代 | 24.5% | 490 元 |
| 天齐锂业 | 24.2% | 484 元 |
| 中国石油 | 25.3% | 253 元 |
| **整体预期** | **24.85%** | **2484.5 元** |

### 五、执行建议

**买入时机**：优先选择早盘低开或盘中回调至买入价格区间下沿时分批介入，避免开盘追高。

**止损规则**：单只个股跌破止损价立即止损，单只最大亏损控制在 10% 以内，整体账户最大回撤控制在 5% 以内。

**止盈策略**：涨至卖出区间下沿时先兑现 50% 仓位，剩余持有至接近区间上沿全部了结。

> **风险提示**：以上报告为系统基于舆情数据生成的策略示例，不构成投资建议。请结合自身判断决策，风险自担。

---

## 项目结构

```
projects/
|-- config/                     # LLM 节点配置（提示词 + 模型参数）
|   |-- guba_industry_analysis_cfg.json
|   |-- trading_strategy_generate_cfg.json
|   `-- ...
|-- scripts/                    # 运维脚本
|   |-- setup.sh                # 依赖安装
|   |-- http_run.sh             # HTTP 服务启动
|   `-- local_run.sh            # 本地调试启动
|-- src/
|   |-- main.py                 # FastAPI 入口，流式 SSE 接口
|   |-- graphs/
|   |   |-- graph.py            # LangGraph 工作流图（18 节点 DAG）
|   |   |-- node.py             # 所有节点函数实现
|   |   `-- state.py            # 全局状态与 Pydantic 模型
|   |-- storage/
|   |   |-- database/           # PostgreSQL ORM 模型与 CRUD
|   |   `-- memory/             # LangGraph Checkpoint 管理
|   `-- utils/
|       |-- error/              # 6 位错误码体系
|       |-- openai/             # OpenAI API 兼容适配层
|       |-- log/                # 结构化日志 + CozeLoop 链路追踪
|       `-- helper/             # 消息转换与图工具函数
|-- .env.example                 # 环境变量模板
|-- requirements.txt
`-- pyproject.toml
```

---

## 技术栈

| 层次 | 技术选型 |
|:-----|:---------|
| 工作流编排 | LangGraph (StateGraph + DAG 并行) |
| LLM 调用 | LangChain + Doubao / DeepSeek |
| Web 服务 | FastAPI + SSE 流式响应 |
| 数据存储 | PostgreSQL (行业评级) + 阿里云 OSS (PDF) |
| 数据采集 | requests + BeautifulSoup4 |
| PDF 生成 | DocumentGenerationClient (Markdown 转 PDF) |
| 链路追踪 | CozeLoop + LangChain Callback |
| 错误处理 | 自定义 6 位错误码体系（9 大类 400+ 条规则） |

---

## 扩展定制

### 自定义数据源

在 `tools/` 目录下添加新的采集器即可扩展数据来源：

```python
# tools/custom_news.py
async def get_custom_news(query: str, days: int = 7):
    """实现自定义数据源逻辑"""
    return [...]
```

### 调整筛选策略

修改 `src/graphs/node.py` 中的筛选逻辑，定制评分模型参数。

### 添加新推送渠道

继承 `NotificationAgent` 基类，实现 `send()` 方法即可接入任意推送渠道。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交变更：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 发起 Pull Request

---

## License

本项目采用 [MIT License](LICENSE) 开源协议。

---

## English

### Overview

This project is a fully automated stock selection and trading strategy generation system built on the **LangGraph workflow engine**. By aggregating multi-source financial sentiment data (stock forum posts, financial commentary, industry research reports, capital flow, KOL blogs) and leveraging LLM semantic understanding, the system automates the complete investment research cycle:

**Sentiment Sensing -> Industry Identification -> Emotion Scoring -> Strategy Generation -> Report Distribution**

> **Disclaimer**: This project is a technical research tool. All generated trading strategies are for reference only and do not constitute investment advice.

### Key Features

| Feature | Description |
|:--------|:------------|
| **Multi-Agent Workflow** | 18-node DAG built with LangGraph, concurrent data collection and AI analysis |
| **Comprehensive Coverage** | Stock forums, financial news, research reports, capital flows, and KOL blogs |
| **Deep LLM Analysis** | Industry correlation networks, sentiment scoring, and strategy generation |
| **Dynamic Industry Rating** | Persistent A-E industry rating database with historical trend tracking |
| **Automated Reports** | Markdown to PDF conversion with OSS cloud storage |
| **Multi-Channel Push** | WeCom / DingTalk / Feishu bot notifications with Markdown support |
| **OpenAI-Compatible** | Standard Chat Completions API, compatible with any LLM client |
| **链路追踪** | CozeLoop + LangChain Callback for full-chain observability |

### Quick Start

```bash
git clone https://github.com/VeKiner/sentiment-driven-stock-screener.git
cd sentiment-driven-stock-screener/projects
pip install -r requirements.txt
cp .env.example .env
# Configure .env with your credentials
bash scripts/http_run.sh -p 5000
```

---

<div align="center">

**[回到顶部](#sentiment-driven-stock-screener)** | **[GitHub 仓库](https://github.com/VeKiner/sentiment-driven-stock-screener)**

</div>

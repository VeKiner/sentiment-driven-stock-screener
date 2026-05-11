<div align="center">

# 📊 Public Opinion Analysis Stock Workflow

**基于多源舆情数据的智能股票选股与交易策略生成系统**

*An Intelligent Stock Selection System Powered by Multi-Source Sentiment Analysis & LangGraph Orchestration*

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green?logo=langchain)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](#english) | [中文](#中文)

</div>

---

## 中文

### 🎯 项目简介

本项目是一套基于 **LangGraph 工作流引擎**构建的全自动股票选股与交易策略生成系统。系统通过抓取多源金融舆情数据（股吧热帖、财经时评、行业研报、资金流向、大V博客），结合大语言模型（LLM）的深度语义理解能力，自动完成从**舆情感知 → 行业识别 → 情绪评估 → 策略生成 → 报告推送**的完整投研闭环。

> ⚠️ **投资风险提示**：本项目为技术研究工具，所有生成的交易策略仅供参考，不构成投资建议。投资有风险，决策请谨慎。

---

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🕸️ **多节点并行工作流** | 基于 LangGraph 构建 18 节点 DAG，数据抓取、AI 分析并行执行，高效协同 |
| 📰 **全域舆情覆盖** | 同步监控股吧热帖、东财财经时评、行业研报、大V博客等多维数据源 |
| 🧠 **LLM 深度分析** | 调用 Doubao/DeepSeek 等主流大模型，完成行业关联网络分析、情绪评分、策略生成 |
| 📈 **动态行业评级** | 持久化行业评级数据库（A-E 五级），支持历史趋势追踪与跨轮次评级对比 |
| 📄 **PDF 报告生成** | 自动将 Markdown 格式策略报告转换为 PDF，上传云存储生成永久访问链接 |
| 📱 **企业微信推送** | 策略报告自动推送企业微信群聊，支持 Markdown 富文本格式 |
| 🔌 **OpenAI 兼容接口** | 提供标准 OpenAI Chat Completions API，可接入任意 LLM 客户端 |

---

### 🏗️ 系统架构

```
用户触发
   │
   ▼
┌─────────────────────────────────────────────────┐
│           FastAPI HTTP 服务层                    │
│  (OpenAI 兼容接口 / 流式 SSE 响应)               │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│          LangGraph 工作流引擎                    │
│                                                 │
│  ┌───────────┐    ┌────────────────┐            │
│  │ 数据抓取层 │    │   AI 分析层     │            │
│  │           │    │                │            │
│  │ 股吧热帖  │──▶│ 行业关联分析   │            │
│  │ 财经时评  │    │ 情绪评估       │            │
│  │ 行业研报  │──▶│ 大V观点分析   │            │
│  │ 资金流向  │    │ 综合策略生成   │            │
│  │ 大V博客   │    │                │            │
│  └───────────┘    └────────────────┘            │
│                          │                      │
│                   ┌──────▼──────┐               │
│                   │  输出层      │               │
│                   │             │               │
│                   │ PDF报告生成 │               │
│                   │ OSS云存储   │               │
│                   │ 企业微信推送│               │
│                   └─────────────┘               │
└─────────────────────────────────────────────────┘
                   │
       ┌───────────┴──────────┐
       │                      │
┌──────▼──────┐        ┌──────▼──────┐
│ PostgreSQL   │        │  阿里云 OSS  │
│ 行业评级DB  │        │  PDF 存储   │
└─────────────┘        └─────────────┘
```

---

### 🔄 工作流节点详解

系统由 **18 个核心节点**组成，按模块划分如下：

#### 模块一：数据抓取层（并行执行）
| 节点 | 数据源 | 说明 |
|------|--------|------|
| `guba_topics_collect` | 东方财富股吧 | 抓取近期热门话题与讨论 |
| `economy_review_collect` | 东财财经频道 | 抓取宏观经济分析文章 |
| `industry_report_collect` | 东财研报中心 | 基于热门行业定向抓取行业研报 |
| `industry_capital_flow_collect` | 东财行情数据 | 抓取行业板块资金流向数据 |
| `v_blog_collect` | 东财大V博客 | 抓取知名财经博主热门文章 |

#### 模块二：AI 智能分析层
| 节点 | 模型 | 输出 |
|------|------|------|
| `guba_industry_analysis` | LLM Agent | 从股吧数据提炼热门投资行业 |
| `review_industry_analysis` | LLM Agent | 从时评数据识别宏观受益行业 |
| `industry_merge` | 逻辑节点 | 融合双源结果，输出最终热门行业列表 |
| `industry_network_analysis` | LLM Agent | 构建行业关联网络与联动分析 |
| `industry_sentiment_analysis` | LLM Agent | 量化各行业舆情情绪与热度 |
| `research_capital_analysis` | LLM Agent | 综合分析研报观点与资金流信号 |
| `v_insights_analysis` | LLM Agent | 解析大V博客中的行业与个股观点 |

#### 模块三：策略生成与持久化层
| 节点 | 功能 |
|------|------|
| `industry_rating_update` | 更新 PostgreSQL 中的行业 A-E 五级评级，记录历史变更 |
| `trading_strategy_generate` | 综合所有分析维度，生成带买卖价格区间的完整 2 日交易策略 |
| `strategy_pdf_upload` | Markdown → PDF 转换，上传阿里云 OSS，返回永久访问链接 |
| `wecom_bot_send` | 推送策略摘要至企业微信群聊（Markdown 富文本格式） |

---

### 🚀 快速开始

#### 环境要求

- Python 3.12+
- PostgreSQL 14+（用于行业评级持久化）
- 阿里云 OSS（用于 PDF 报告存储）
- 企业微信群机器人（用于策略推送）

#### 安装依赖

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/public-opinion-analysis-stock-workflow.git
cd public-opinion-analysis-stock-workflow/projects

# 使用 pip 安装
pip install -r requirements.txt

# 或使用 uv（推荐，更快）
uv sync
```

#### 配置环境变量

复制环境变量模板并填写您的配置：

```bash
cp .env.example .env
```

在 `.env` 文件中填入以下配置：

```env
# ===== 数据库配置 =====
PGDATABASE_URL=postgresql://user:password@localhost:5432/stock_analysis

# ===== 阿里云 OSS 配置 =====
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name

# ===== 企业微信配置 =====
# 在企业微信群聊中添加机器人，获取 Webhook Key
WECOM_WEBHOOK_KEY=your_webhook_key

# ===== CozeLoop 链路追踪（可选）=====
COZE_PROJECT_SPACE_ID=your_space_id
COZE_LOOP_API_TOKEN=your_api_token
COZE_LOOP_BASE_URL=https://api.coze.cn

# ===== 日志配置 =====
LOG_LEVEL=INFO
```

#### 启动服务

```bash
# 本地开发模式
bash scripts/local_run.sh

# HTTP 服务模式（生产）
bash scripts/http_run.sh -p 5000
```

#### API 调用示例

服务启动后，通过标准 OpenAI 兼容接口触发分析：

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

### 📁 项目结构

```
projects/
├── config/                      # LLM 节点配置（提示词 + 模型参数）
│   ├── guba_industry_analysis_cfg.json
│   ├── trading_strategy_generate_cfg.json
│   └── ...
├── scripts/                     # 运维脚本
│   ├── setup.sh                 # 依赖安装
│   ├── http_run.sh              # HTTP 服务启动
│   └── local_run.sh             # 本地调试启动
├── src/
│   ├── main.py                  # FastAPI 入口，流式 SSE 接口
│   ├── graphs/
│   │   ├── graph.py             # LangGraph 工作流图定义（18节点 DAG）
│   │   ├── node.py              # 所有节点函数实现
│   │   └── state.py             # 全局状态与 Pydantic 模型定义
│   ├── storage/
│   │   ├── database/            # PostgreSQL ORM 模型与 CRUD
│   │   └── memory/              # LangGraph Checkpoint 管理
│   └── utils/
│       ├── error/               # 6位错误码体系与分类器
│       ├── openai/              # OpenAI API 兼容适配层
│       ├── log/                 # 结构化日志 + CozeLoop 链路追踪
│       └── helper/              # 消息转换与图工具函数
├── requirements.txt
└── pyproject.toml
```

---

### ⚙️ 技术栈

| 层次 | 技术选型 |
|------|---------|
| **工作流编排** | LangGraph (StateGraph + DAG 并行) |
| **LLM 调用** | LangChain + Doubao / DeepSeek |
| **Web 服务** | FastAPI + SSE 流式响应 |
| **数据存储** | PostgreSQL (行业评级) + 阿里云 OSS (PDF) |
| **数据采集** | requests + BeautifulSoup4 |
| **PDF 生成** | DocumentGenerationClient (Markdown → PDF) |
| **链路追踪** | CozeLoop + LangChain Callback |
| **错误处理** | 自定义 6位错误码体系（9大类 400+条规则）|

---

### 📋 报告示例

以下为系统生成的完整股票策略报告示例：

---

#### 一、观点看法（市场环境 + 行业逻辑）

当前市场处于科技主线主导的结构性行情阶段，上证指数冲击 4200 点强阻力区，短期存在震荡洗盘预期，但新质生产力相关科技赛道景气度确定性较高，是资金核心配置方向。

从行业逻辑来看，AI 算力需求爆发是本轮行情的核心驱动主线：
- **存储芯片**：作为算力核心硬件，供需缺口推动行业进入全年涨价周期，业绩兑现能力突出
- **光模块/CPO**：作为算力网络的核心连接环节，下游订单已锁定至 2028 年，增长确定性极强
- **能源金属**：受益于储能需求爆发与碳酸锂价格上行，盈利预期持续上修

---

#### 二、推荐行业及个股分析

##### 1. 存储芯片

- **行业评级**：A 级
- **数据支撑**：2026Q1 存储细分板块净利润同比增长 3735%，高盛预测 2026 年全球 DRAM 供需缺口 4.9%、HBM 缺口 5.1%，涨价将贯穿全年

**推荐个股：佰维存储（sh688525）**

| 项目 | 数值 |
|------|------|
| 买入价格区间 | 86.00 元 - 90.00 元 |
| 卖出价格区间 | 108.00 元 - 118.00 元 |
| 预期 2 日回报率 | 25.6% |

##### 2. 光模块 / CPO

- **行业评级**：A 级
- **数据支撑**：英伟达 32 亿美元投资康宁提升光连接产能 10 倍，800G/1.6T 光模块渗透率快速提升，订单已锁定至 2028 年

**推荐个股：中际旭创（sz300308）**

| 项目 | 数值 |
|------|------|
| 买入价格区间 | 185.00 元 - 192.00 元 |
| 卖出价格区间 | 230.00 元 - 248.00 元 |
| 预期 2 日回报率 | 24.7% |

##### 3. 新能源与周期类

**推荐个股：**

| 股票名称 | 代码 | 买入区间 | 卖出区间 | 预期回报率 |
|----------|------|----------|----------|------------|
| 宁德时代 | sz300750 | 265-275 元 | 330-350 元 | 24.5% |
| 天齐锂业 | sz002466 | 78-83 元 | 98-108 元 | 24.2% |
| 中国石油 | sh601857 | 9.2-9.6 元 | 11.5-12.5 元 | 25.3% |

---

#### 三、资金分配方案

| 股票代码 | 股票名称 | 分配金额 | 占比 |
|----------|----------|----------|------|
| sh688525 | 佰维存储 | 2500 元 | 25% |
| sz300308 | 中际旭创 | 2500 元 | 25% |
| sz300750 | 宁德时代 | 2000 元 | 20% |
| sz002466 | 天齐锂业 | 2000 元 | 20% |
| sh601857 | 中国石油 | 1000 元 | 10% |
| **合计** | | **10000 元** | **100%** |

---

#### 四、整体预期回报率

| 股票名称 | 预期 2 日回报率 | 预期盈利金额 |
|----------|----------------|--------------|
| 佰维存储 | 25.6% | 640 元 |
| 中际旭创 | 24.7% | 617.5 元 |
| 宁德时代 | 24.5% | 490 元 |
| 天齐锂业 | 24.2% | 484 元 |
| 中国石油 | 25.3% | 253 元 |
| **整体预期** | **24.85%** | **2484.5 元** |

---

#### 五、执行建议

**买入时机**：优先选择早盘低开或盘中回调至买入价格区间下沿时分批介入，避免开盘追高。

**止损规则**：单只个股跌破止损价立即止损，单只最大亏损控制在 10% 以内，整体账户最大回撤控制在 5% 以内。

**止盈策略**：个股涨至卖出价格区间下沿时可先卖出 50% 仓位，剩余仓位持有至接近区间上沿时全部兑现。

---

> ⚠️ **投资风险提示**：以上报告仅为系统基于舆情数据生成的策略示例，不构成投资建议。投资有风险，决策请谨慎。

---

### 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交变更：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 发起 Pull Request

---

### 📄 License

本项目采用 [MIT License](LICENSE) 开源协议。

---

## English

### 🎯 Overview

This project is a fully automated stock selection and trading strategy generation system built on the **LangGraph workflow engine**. By aggregating multi-source financial sentiment data (stock forum posts, financial commentary, industry research reports, capital flow, KOL blogs) and leveraging LLM semantic understanding, the system automates the complete investment research cycle: **Sentiment Sensing → Industry Identification → Emotion Scoring → Strategy Generation → Report Distribution**.

> ⚠️ **Investment Risk Disclaimer**: This project is a technical research tool. All generated trading strategies are for reference only and do not constitute investment advice.

### ✨ Key Features

- **Multi-node Parallel Workflow**: 18-node DAG built with LangGraph, concurrent data collection and AI analysis
- **Comprehensive Sentiment Coverage**: Monitors stock forums, financial news, research reports, capital flows, and KOL blogs
- **Deep LLM Analysis**: Industry correlation networks, sentiment scoring, and strategy generation via mainstream LLMs
- **Dynamic Industry Rating**: Persistent A-E industry rating database with historical trend tracking
- **Automated PDF Reports**: Markdown → PDF conversion with cloud storage (Aliyun OSS) permanent URL
- **WeCom Bot Notifications**: Auto-push strategy summaries to enterprise WeChat groups
- **OpenAI-Compatible API**: Standard Chat Completions interface compatible with any LLM client

### 🚀 Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/public-opinion-analysis-stock-workflow.git
cd public-opinion-analysis-stock-workflow/projects
pip install -r requirements.txt
# Configure .env with your credentials
bash scripts/http_run.sh -p 5000
```

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

*If this project helps you, please give it a ⭐ Star!*

</div>

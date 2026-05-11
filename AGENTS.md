## 项目概述
- **名称**: 舆情分析股票工作流
- **功能**: 通过舆情分析和数据抓取，自动分析股票市场并生成5日短线交易策略

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| guba_topic_collect | `node.py` | task | 抓取股吧热门话题 | - | - |
| finance_commentary_collect | `node.py` | task | 抓取财经经济时评 | - | - |
| popular_industry_analysis | `node.py` | agent | 识别热门行业 | - | `config/popular_industry_analysis_cfg.json` |
| industry_network_build | `node.py` | agent | 构建行业关联网络 | - | `config/industry_network_build_cfg.json` |
| industry_sentiment_analysis | `node.py` | agent | 分析行业情绪 | - | `config/industry_sentiment_analysis_cfg.json` |
| industry_report_collect | `node.py` | task | 抓取行业研报 | - | - |
| industry_capital_flow_collect | `node.py` | task | 抓取行业资金流 | - | - |
| research_capital_analysis | `node.py` | agent | 研报&资金流分析 | - | `config/research_capital_analysis_cfg.json` |
| v_blog_collect | `node.py` | task | 抓取大V博客 | - | - |
| v_insights_analysis | `node.py` | agent | 分析大V博客内容 | - | `config/v_insights_analysis_cfg.json` |
| industry_rating_update | `node.py` | task | 更新行业评级 | - | `config/industry_rating_cfg.json` |
| trading_strategy_generate | `node.py` | agent | 综合生成交易策略 | - | `config/trading_strategy_generate_cfg.json` |
| strategy_pdf_upload | `node.py` | task | 交易策略PDF生成与上传 | - | - | 将交易策略报告（Markdown格式）转换为PDF并上传到阿里云OSS，生成永久公开访问链接
| wecom_bot_send | `node.py` | task | 企业微信机器人推送 | - | - | 将交易策略PDF报告链接推送到企业微信群聊（支持Markdown格式，包含报告摘要和推荐行业）

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
无

## 数据库表清单
| 表名 | 文件位置 | 用途 | 关联节点 |
|-----|---------|------|---------|
| IndustryRating | `src/storage/database/shared/model.py` | 存储行业评级和历史 | industry_rating_update, trading_strategy_generate |
| BlogPost | `src/storage/database/shared/model.py` | 存储大V博客文章 | v_blog_collect, v_insights_analysis |

## 集成使用
- 所有 agent 节点使用大语言模型集成（integration-doubao-seed）
- 数据抓取节点使用 requests + BeautifulSoup4 直接抓取指定网页
- PDF生成节点使用 document-generation 集成（将Markdown转换为PDF）
- PDF文件上传到阿里云OSS，生成永久公开访问链接
- OSS配置：
  - Access Key ID: 通过环境变量 `OSS_ACCESS_KEY_ID` 配置
  - Access Key Secret: 通过环境变量 `OSS_ACCESS_KEY_SECRET` 配置
  - Endpoint: 通过环境变量 `OSS_ENDPOINT` 配置，例如 `oss-cn-beijing.aliyuncs.com`
  - Bucket Name: 通过环境变量 `OSS_BUCKET_NAME` 配置

## 数据流说明
1. **步骤1-2（并行）**: 同时抓取股吧热门话题和财经经济时评
2. **步骤3**: 识别热门行业板块，输出 `final_industries`
3. **步骤4**: 构建行业关联网络
4. **步骤5**: 分析行业情绪
6. **步骤6（并行）**:
   - 基于 `final_industries` 抓取行业研报
   - 基于 `final_industries` 抓取行业资金流数据
   - 抓取大V博客热门文章
7. **步骤7**: 分析大V博客内容，提取行业和个股投资建议
8. **步骤8**: 基于分析结果更新行业评级
9. **步骤9**: 综合分析研报、资金流、大V观点和行业评级，生成最终交易策略
10. **步骤10**: 将交易策略转换为PDF，上传到阿里云OSS，生成永久公开访问链接
11. **步骤11**: 将PDF报告链接推送到企业微信群聊，支持Markdown格式展示报告摘要和推荐行业

## 关键URL
- 股吧热门话题: https://gubatopic.eastmoney.com/
- 财经经济时评: https://finance.eastmoney.com/a/cjjsp.html
- 大V博客热门: https://blog.eastmoney.com/hot_1.html
- 行业研报中心API: https://data.eastmoney.com/report/reportApi.jshtml
- 行业研报列表: https://data.eastmoney.com/report/industry.jshtml
- 行业资金流API: https://push2.eastmoney.com/api/qt/ulist.np/get
- 行业资金流页面: https://data.eastmoney.com/bkzj/{板块代码}.html

## 修改记录
- 2025-01-XX: 修改行业研报和资金流抓取节点，基于 `final_industries` 进行定向抓取
- 2025-01-XX: 优化研报抓取，使用页面JavaScript变量获取数据
- 2025-01-XX: 更新行业代码映射表，使用东财API真实数据
- 2025-01-XX: 修复资金流板块代码构造逻辑，避免重复添加BK前缀
- 2025-01-XX: 优化研报匹配逻辑，使用行业名称匹配替代代码匹配
- 2025-01-XX: 扩展同义词映射表，提高行业名称匹配成功率
- 2025-01-XX: 移除所有模拟数据，确保所有数据基于真实网页抓取
- 2025-01-XX: 重构行业研报抓取逻辑，改为访问 `industry.jshtml` 获取最新研报列表，通过标题关键词匹配目标行业
- 2025-01-XX: 修复代码缩进和try-except结构问题，确保语法正确
- 2025-01-XX: 优化研报抓取，改为按行业统计匹配数量（每个行业最多15篇），检查范围从50篇增加到200篇
- 2025-01-XX: 移除资金流抓取的总数量限制（原限制50条），确保所有目标行业的资金流数据都能被抓取
- 2025-01-XX: **回退研报抓取策略**：保持使用通用研报列表页（`industry.jshtml`），通过关键词匹配筛选研报，确保行业名称匹配准确
- 2025-01-XX: **新增行业评级系统**：创建行业评级表，支持A/B/C/D/E五个等级和四种分类（短期可关注/中期可关注/潜在有上涨趋势/下跌趋势），记录评级历史
- 2025-01-XX: **新增大V博客分析**：抓取东方财富大V博客热门文章，通过智能体分析行业和个股投资建议，融合到交易策略生成
- 2025-01-XX: **优化综合策略生成**：融合大V分析结果和行业评级数据，提升策略可信度
- 2025-03-04: **新增PDF报告生成与上传**：将交易策略报告（Markdown格式）转换为PDF并上传到对象存储，返回公开访问链接，可直接在浏览器中打开阅读和分享（24小时有效）
- 2025-03-05: **新增企业微信机器人推送**：自动将交易策略PDF报告链接推送到企业微信群聊，支持Markdown格式，包含报告摘要和推荐行业
- 2025-03-09: **修改PDF上传到阿里云OSS**：将PDF报告上传到阿里云OSS存储，生成永久公开访问链接（替代临时S3存储）
- 2025-03-12: **优化综合交易策略生成格式**：修改输出格式，按行业分组展示，每个行业标题下先列出行业分析（数据支撑+观点支撑+大V观点），再列出该行业对应的推荐股票及分析，避免内容分散。从推荐3个行业6只股票调整为推荐2-3个行业5只股票。
- 2025-03-12: **修复企业微信推送问题**：
  - 修复推荐行业提取失败问题（正则表达式无法匹配新的行业标题格式 `### 1. 行业名称`）
  - 更新PDF报告有效期说明，从"24小时有效"改为"永久有效"
  - 确认所有排序使用有序符号（1. 2. 3.）
- 2025-03-12: **进一步优化PDF排版和企业微信推送**：
  - 规范PDF输出格式，所有列表项使用有序符号（1. 2. 3.），禁止使用无序符号（-）
  - 优化段落间距，每个章节之间空一行，每个行业之间空两行，提高可读性
  - 修复企业微信推送预期回报率提取错误（之前提取到股票代码，现在正确提取百分比范围）
- 2025-03-12: **清理项目冗余文件**：
  - 删除项目根目录下的临时测试文件：fix_node.py、test_capital_page.py、test_required_pages.py、test_user_specified_urls.py
  - 删除 tmp 目录下的所有临时测试文件
  - 删除冗余的节点文件：src/graphs/nodes/industry_report_collect_node_new.py
  - 删除未使用的测试文件：src/utils/error/test_classifier.py
  - 删除未使用的S3存储相关文件：src/storage/s3/（已改用阿里云OSS）
  - 删除空的目录：tmp/、src/graphs/nodes/、assets/（空）
- 2025-03-24: **修复画布转换错误**：
  - 修复 "No module named 'oss2'" 错误
  - 重新安装 oss2==2.19.1 及其所有依赖包
  - 验证工作流正常运行，PDF生成、OSS上传、企业微信推送功能正常
- 2025-05-11: **优化代码格式规范美观**：
  - 优化导入部分，添加完整的模块文档字符串
  - 统一导入顺序（标准库、第三方库、本地库）
  - 添加更规范的注释和文档字符串
  - 移除未使用的导入（移除 playwright 依赖，节省约 120M 空间）
  - 保持所有功能不变，代码更规范、更易维护

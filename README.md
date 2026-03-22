# A股智能选股与分析工具

[![Python版本](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![数据源](https://img.shields.io/badge/数据源-新浪%2F腾讯财经-green.svg)](https://finance.sina.com.cn/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A股智能选股与分析工具**是一个基于免费行情API的量化投资辅助工具，支持一键智能选股、个股深度分析、实时热点资讯聚合等功能。

## 核心特性

- **一键智能选股**：基于技术面、基本面、资金面多维度评分，筛选潜力个股 Top10
- **个股深度分析**：技术指标（MACD/RSI/均线）+ 资金流向 + 操作建议
- **热点资讯聚合**：实时市场动态、板块涨跌、资金流向
- **完全免费**：使用新浪/腾讯公开行情API，无需API Key
- **轻量高效**：纯Python实现，无重型依赖

## 项目结构

```
stock-god-gt/
├── scripts/
│   ├── one_click_select.py    # 一键智能选股
│   ├── stock_analysis.py      # 个股深度分析
│   ├── get_hot_news.py        # 热点资讯聚合
│   └── stock_cli.py           # AkShare命令行工具
├── SKILL.md                   # Skill定义文档
└── README.md                  # 项目说明文档
```

## 快速开始

### 环境要求

- Python 3.7+
- requests 库

### 安装依赖

```bash
pip install requests akshare
```

### 使用示例

#### 1. 一键选股

```python
import subprocess
import json

result = subprocess.run(
    ["python", "scripts/one_click_select.py"],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)

print("🔥 Top 10 潜力股：")
for stock in data["data"][:10]:
    print(f"{stock['rank']}. {stock['name']} ({stock['code']}) - 评分: {stock['total_score']}")
```

**返回字段：**
- `rank` - 排名
- `code` - 股票代码
- `name` - 股票名称
- `price` - 当前价格
- `change_pct` - 涨跌幅
- `total_score` - 综合评分
- `tech_score` - 技术面评分
- `money_score` - 资金面评分
- `reason` - 推荐理由
- `risk_tip` - 风险提示

#### 2. 个股分析

```python
result = subprocess.run(
    ["python", "scripts/stock_analysis.py", "600519"],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)["data"]

print(f"股票：{data['basic']['name']}")
print(f"评分：{data['overall_score']}/100")
print(f"建议：{data['advice']}")
```

**返回字段：**
- `basic` - 基本信息（代码/名称/价格/涨跌幅）
- `technical` - 技术指标（MACD/RSI/均线/量价）
- `money_flow` - 资金流向
- `overall_score` - 综合评分
- `advice` - 操作建议
- `price_levels` - 价格区间（建仓/止盈/止损）

#### 3. 热点资讯

```python
result = subprocess.run(
    ["python", "scripts/get_hot_news.py", ""],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)

print("📈 热点板块：")
for sector in data["data"]["hot_sectors"]:
    print(f"{sector['name']}: {sector['change']}")
```

**返回字段：**
- `news_list` - 新闻列表
- `by_category` - 分类新闻
- `hot_sectors` - 热点板块

## 评分体系

| 维度 | 权重 | 评分指标 |
|------|------|----------|
| 技术面 | 40% | 均线多头、MACD金叉死叉、RSI超买超卖 |
| 基本面 | 30% | 趋势判断、量价关系 |
| 资金面 | 30% | 成交量变化、资金流向估算 |

## 数据来源

本工具使用以下免费公开数据源：

- **新浪财经API**：`hq.sinajs.cn` - 实时行情
- **腾讯行情API**：`qt.gtimg.cn` - 实时行情
- **新浪K线API**：`money.finance.sina.com.cn` - 历史K线
- **AkShare库**（可选）：`akshare` - 增强数据获取能力

## 使用限制

- 所有数据来源于公开行情接口，存在一定延迟（通常<1秒）
- 请勿将本工具用于实盘交易操作
- 评分系统仅供参考，不构成投资建议

## 风险提示

⚠️ **重要声明**：

1. 本工具所有数据来源于新浪/腾讯公开行情数据
2. 评分和建议仅供参考，不构成任何投资建议
3. 股市有风险，投资需谨慎
4. 请根据自身风险承受能力做出投资决策

## 技术栈

- **Python 3.7+** - 核心编程语言
- **requests** - HTTP请求库
- **re** - 正则表达式处理
- **json** - 数据序列化
- **akshare**（可选）- 金融数据接口

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 免责声明

本项目仅供学习和研究使用，作者不对使用本工具产生的任何损失负责。使用本工具即表示您同意承担相应风险。

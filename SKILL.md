---
name: stock-god-gt
description: A股智能选股与分析Skill。基于新浪/腾讯免费行情API（无需API Key），支持一键选股（Top10潜力股）、个股深度分析（技术面+资金面）、实时热点资讯聚合。当用户查询以下内容时触发：(1) 选股/帮我选股票/哪些股票值得买；(2) 分析某只股票/某代码股票怎么样；(3) 今日热点/市场要闻/行业动态；(4) 股票代码相关分析。调用三个核心函数：one_click_select()、stock_analysis(代码)、get_hot_news(关键词)。注意：本Skill仅提供数据参考，不构成投资建议，股市有风险。
---

# A股智能选股与分析 (akshare-stock)

## 数据来源

本 Skill 使用新浪财经 + 腾讯行情 API，**无需 API Key**，完全免费。

## 核心函数

### 1. one_click_select()

一键选股，返回 Top10 潜力股。

```python
# 在 OpenClaw Agent 中调用
import subprocess, json
result = subprocess.run(["python", "scripts/one_click_select.py"], capture_output=True, text=True)
data = json.loads(result.stdout)
for s in data["data"][:10]:
    print(f"{s['rank']}. {s['name']} ({s['code']}) - 评分:{s['total_score']}")
```

**返回字段：** rank, code, name, price, change_pct, total_score, tech_score, money_score, ma_trend, macd, rsi, reason, risk_tip

---

### 2. stock_analysis(代码)

个股深度分析。

```python
result = subprocess.run(["python", "scripts/stock_analysis.py", "600519"], capture_output=True, text=True)
data = json.loads(result.stdout)["data"]
print(f"评分: {data['overall_score']}/100 | 建议: {data['advice']}")
```

**返回字段：** basic(代码/名称/价格/涨跌幅), technical(MACD/RSI/均线/量价), money_flow(资金), overall_score, advice, price_levels(建仓/止盈/止损), short_outlook, mid_outlook

---

### 3. get_hot_news(关键词)

实时热点资讯。

```python
result = subprocess.run(["python", "scripts/get_hot_news.py", ""], capture_output=True, text=True)
data = json.loads(result.stdout)
for sector in data["data"]["hot_sectors"]:
    print(f"{sector['name']}: {sector['change']}")
```

**返回字段：** news_list, by_category, hot_sectors

---

## 评分体系

| 维度 | 权重 | 指标 |
|------|------|------|
| 技术面 | 40% | 均线、MACD、RSI |
| 基本面 | 30% | 趋势粗估 |
| 资金面 | 30% | 量价关系估算 |

---

## 风险提示

⚠️ 本 Skill 所有数据来源于新浪/腾讯公开行情数据，**仅供参考，不构成任何投资建议**。股市有风险，投资需谨慎。

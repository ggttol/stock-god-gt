#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_hot_news.py - A股热点资讯聚合
数据来源：新浪/腾讯免费行情API（无需Key）
"""

import sys
import json
import re
import warnings
import datetime
from typing import Dict, List, Any, Optional

warnings.filterwarnings("ignore")
import requests


def sina_quote(codes: List[str]) -> List[Dict]:
    if not codes:
        return []
    symbols = ",".join(codes)
    try:
        r = requests.get(
            f"https://hq.sinajs.cn/list={symbols}",
            headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        r.encoding = "gbk"
        results = []
        for line in r.text.strip().split("\n"):
            m = re.match(r'var hq_str_(.+?)="(.+)"', line.strip())
            if m:
                fields = m.group(2).split(",")
                results.append({"code": m.group(1), "fields": fields})
        return results
    except Exception as e:
        print(f"[WARN] 新浪API失败: {e}", file=sys.stderr)
        return []


def get_hot_news(keyword: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    print(f"[astock-selector] 获取热点, keyword={keyword}", file=sys.stderr)

    # 探测：批量获取候选股票实时行情作为资讯来源
    # 选取代表性股票池用于判断市场热点
    candidates = [
        "sh600519", "sh600036", "sh600028", "sh601318",  # 消费金融能源
        "sh600900", "sh601012", "sh601166", "sh600050",  # 电力光伏银行通信
        "sz002594", "sz002230", "sz300750", "sz300274",  # 汽车AI新能源
        "sh688012", "sh688041", "sz300760", "sh600104",  # 芯片医药汽车
    ]

    quotes = sina_quote(candidates)
    news_list = []
    sector_data = {
        "AI科技": ["sz002230", "sh688012", "sh688041"],
        "新能源": ["sz300750", "sh601012", "sz300274"],
        "消费金融": ["sh600519", "sh600036", "sh601318"],
        "能源电力": ["sh600028", "sh600900", "sh601166"]
    }
    
    sector_sums = {k: [] for k in sector_data.keys()}

    for q in quotes:
        try:
            code = q["code"]
            fields = q["fields"]
            if len(fields) < 10:
                continue
            name = fields[0]
            price = float(fields[3]) if fields[3] else 0
            prev = float(fields[2]) if fields[2] else price
            change = round((price / prev - 1) * 100, 2) if prev > 0 else 0.0
            volume = int(fields[8]) if fields[8] else 0

            # 归类板块
            for s_name, s_codes in sector_data.items():
                if code in s_codes:
                    sector_sums[s_name].append(change)

            # 作为资讯条目
            direction = "上涨" if change > 0 else ("持平" if change == 0 else "下跌")
            news_list.append({
                "title": f"【{name}】现报{price:.2f}元，今日{direction}{abs(change)}%",
                "time": datetime.datetime.now().strftime("%H:%M"),
                "source": "新浪财经",
                "category": "实时行情",
                "related_stocks": [code.replace("sh", "").replace("sz", "")],
                "summary": f"最新价{price:.2f}，涨跌幅{change}%，成交量{volume}股。市场活跃度{'高' if volume > 1000000 else '中'}。"
            })
        except Exception:
            continue

    # 计算热点板块
    hot_sectors = []
    for s_name, changes in sector_sums.items():
        if changes:
            avg_change = round(sum(changes) / len(changes), 2)
            hot_sectors.append({
                "name": s_name,
                "change": f"{'+' if avg_change > 0 else ''}{avg_change}%",
                "status": "领涨" if avg_change > 1 else "活跃" if avg_change > 0 else "波段"
            })
    hot_sectors.sort(key=lambda x: float(x["change"].replace("%", "")), reverse=True)

    # 资讯排序
    news_list.sort(key=lambda x: abs(float(x["summary"].split("涨跌幅")[1].split("%")[0])), reverse=True)

    # 过滤关键词
    if keyword:
        news_list = [n for n in news_list if keyword in n["title"] or keyword in n.get("summary", "")]

    # 取前limit条
    news_list = news_list[:limit]

    by_category: Dict[str, List] = {}
    for n in news_list:
        cat = n.get("category", "其他")
        by_category.setdefault(cat, []).append(n)

    return {
        "success": True,
        "data": {
            "news_list": news_list,
            "by_category": by_category,
            "hot_sectors": hot_sectors
        },
        "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "keyword": keyword if keyword else "全市场",
        "total": len(news_list),
        "disclaimer": "⚠️ 资讯内容仅供参考，不构成投资建议。股市有风险，投资需谨慎。"
    }


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        result = get_hot_news(keyword=keyword)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e), "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False, indent=2))
        sys.exit(1)

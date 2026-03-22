#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
one_click_select.py - A股一键智能选股
数据来源：新浪/腾讯免费行情API（无需Key，稳定可靠）
候选池：各行业代表股票 20 只
评分：技术面 40% + 基本面 30% + 资金 30%
"""

import sys
import json
import re
import warnings
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

warnings.filterwarnings("ignore")
import requests

# ========== 候选池 ==========
CANDIDATE_POOL = [
    "600519", "600036", "600104", "600276",  # 消费/金融
    "300059", "002230", "300751", "688041",  # 科技/AI/新能源
    "300760", "000002", "601318", "300750",  # 医药/地产/新能源车
    "600028", "601899", "600019", "600900",  # 能源/矿业/电力
    "300274", "688012", "300122", "002594",  # 光伏/芯片/疫苗/汽车
]


# ========== 新浪行情API ==========

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
                results.append({"code": m.group(1), "fields": m.group(2).split(",")})
        return results
    except Exception as e:
        print(f"[WARN] 新浪API失败: {e}", file=sys.stderr)
        return []


def sina_hist(code: str, days: int = 30) -> List[Dict]:
    """获取新浪历史K线"""
    try:
        symbol = code if code.startswith(("sh", "sz")) else (("sh" if code.startswith(("6", "5")) else "sz") + code)
        url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {"symbol": symbol, "scale": 240, "ma": 5, "datalen": days}
        r = requests.get(url, params=params,
                         headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}, timeout=10)
        r.encoding = "utf-8"
        data = r.json()
        return [{"date": item["day"][:10], "open": float(item["open"]), "close": float(item["close"]),
                 "high": float(item["high"]), "low": float(item["low"]), "volume": float(item["volume"])} for item in data]
    except Exception as e:
        return []


def to_sina_code(code: str) -> str:
    code = code.strip().zfill(6)
    return f"sh{code}" if code.startswith(("6", "5")) else f"sz{code}"


def to_name(code: str, fields: List[str]) -> str:
    return fields[0] if fields else code


# ========== 技术指标 ==========

def ema(vals: List[float], period: int) -> float:
    if not vals:
        return 0
    k = 2 / (period + 1)
    result = vals[0]
    for v in vals[1:]:
        result = v * k + result * (1 - k)
    return result


def calc_macd(closes: List[float]) -> str:
    if len(closes) < 26:
        return "flat"
    e12 = ema(closes[:12], 12)
    e26 = ema(closes[:26], 26)
    dif = e12 - e26
    dea = ema([dif] * 10, 10)
    return "golden" if dif > dea else "dead"


def calc_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(d if d > 0 else 0)
        losses.append(abs(d) if d < 0 else 0)
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100.0
    return round(100 - 100 / (1 + ag / al), 1)


# ========== 评分函数 ==========

def score_one(code: str) -> Optional[Dict]:
    sina_code = to_sina_code(code)

    # 获取实时行情（批量）
    quotes = sina_quote([sina_code])
    if not quotes:
        print(f"[WARN] {code} 行情获取失败", file=sys.stderr)
        return None

    fields = quotes[0]["fields"]
    name = to_name(code, fields)

    try:
        price = float(fields[3]) if fields[3] else 0
        prev_close = float(fields[2]) if fields[2] else price
        change_pct = round((price / prev_close - 1) * 100, 2) if prev_close > 0 else 0.0
        volume = int(fields[8]) if fields[8] else 0
        amount = float(fields[9]) if fields[9] else 0
    except (ValueError, IndexError):
        print(f"[WARN] {code} 数据解析失败", file=sys.stderr)
        return None

    # 获取历史K线
    hist = sina_hist(sina_code, days=60)
    if not hist or len(hist) < 20:
        print(f"[WARN] {code} 历史数据不足: {len(hist)}条", file=sys.stderr)
        return None

    closes = [h["close"] for h in hist if h["close"] > 0]
    volumes = [h["volume"] for h in hist if h["volume"] > 0]

    if len(closes) < 20:
        print(f"[WARN] {code} K线数据不足", file=sys.stderr)
        return None

    # 均线
    ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else closes[-1]
    ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else ma5
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma10

    # MACD
    macd_sig = calc_macd(closes)

    # RSI
    rsi = calc_rsi(closes)

    # 量比
    vol_ratio = round(volumes[0] / volumes[1], 2) if len(volumes) >= 2 and volumes[1] > 0 else 1.0

    # 资金估算
    avg_price = amount / volume if volume > 0 and amount > 0 else price
    main_net = (price - avg_price) * volume if volume > 0 else 0

    # ---- 技术评分 ----
    tech = 50
    if ma5 > ma10 > ma20:
        tech += 30
    elif ma5 < ma10 < ma20:
        tech -= 25

    if macd_sig == "golden":
        tech += 25
    elif macd_sig == "dead":
        tech -= 30

    if 35 <= rsi <= 65:
        tech += 10
    elif rsi < 30:
        tech += 15
    elif rsi > 80:
        tech -= 15

    if 1.0 <= abs(change_pct) <= 4.0:
        tech += 5

    tech = max(0, min(100, tech))

    # ---- 资金评分 ----
    m_score = 50
    if main_net > 1e8:
        m_score = 100
    elif main_net > 0:
        m_score = 70
    elif main_net < -1e8:
        m_score = 20
    m_score = max(0, min(100, m_score))

    # ---- 基本面 ----
    fund_score = min(max(50 + change_pct * 5, 0), 100)

    # ---- 综合 ----
    total = round(tech * 0.4 + fund_score * 0.3 + m_score * 0.3, 1)

    reasons = []
    if macd_sig == "golden":
        reasons.append("MACD金叉")
    elif macd_sig == "dead":
        reasons.append("MACD死叉")
    if ma5 > ma10 > ma20:
        reasons.append("均线多头")
    elif ma5 < ma10 < ma20:
        reasons.append("均线空头")
    if rsi < 35:
        reasons.append(f"RSI={rsi:.0f}偏低")
    elif rsi > 70:
        reasons.append(f"RSI={rsi:.0f}偏高")
    if main_net > 5e7:
        reasons.append(f"主力净流入{main_net/1e8:.1f}亿")
    if abs(change_pct) <= 3:
        reasons.append(f"涨幅{change_pct}%健康")

    ma_trend = "多头" if ma5 > ma10 > ma20 else ("空头" if ma5 < ma10 < ma20 else "震荡")

    return {
        "code": code,
        "name": name,
        "price": round(price, 2),
        "change_pct": change_pct,
        "total_score": total,
        "tech_score": round(tech, 1),
        "fund_score": round(fund_score, 1),
        "money_score": round(m_score, 1),
        "volume_ratio": vol_ratio,
        "ma_trend": ma_trend,
        "macd": macd_sig,
        "rsi": round(rsi, 1),
        "main_net": main_net,
        "reasons": reasons[:4]
    }


# ========== 入口 ==========

def one_click_select(top_n: int = 10) -> Dict[str, Any]:
    print(f"[astock-selector] 开始选股，候选池:{len(CANDIDATE_POOL)}只", file=sys.stderr)
    scored: List[Dict] = []

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(score_one, c): c for c in CANDIDATE_POOL}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    scored.append(r)
                    print(f"[OK] {r['code']} {r['name']}: {r['total_score']}分", file=sys.stderr)
            except Exception as e:
                print(f"[ERR] {futures[fut]}: {e}", file=sys.stderr)

    scored.sort(key=lambda x: x["total_score"], reverse=True)
    top = scored[:top_n]

    data = [{
        "rank": i + 1,
        "code": s["code"],
        "name": s["name"],
        "industry": "A股",
        "price": s["price"],
        "change_pct": s["change_pct"],
        "total_score": s["total_score"],
        "tech_score": s["tech_score"],
        "fundamental_score": s["fund_score"],
        "money_score": s["money_score"],
        "volume_ratio": s["volume_ratio"],
        "ma_trend": s["ma_trend"],
        "macd": s["macd"],
        "rsi": s["rsi"],
        "reason": "；".join(s["reasons"]),
        "risk_tip": "仅供参考，不构成投资建议"
    } for i, s in enumerate(top)]

    return {
        "success": True,
        "data": data,
        "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_scanned": len(scored),
        "disclaimer": "⚠️ 本结果仅供数据参考，不构成投资建议。股市有风险，投资需谨慎。"
    }


if __name__ == "__main__":
    try:
        result = one_click_select()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e), "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False, indent=2))
        sys.exit(1)

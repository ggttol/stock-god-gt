#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stock_analysis.py - A股个股深度分析
数据来源：新浪/腾讯免费行情API（无需Key，稳定可靠）
"""

import sys
import json
import re
import warnings
import datetime
from typing import Dict, Any, Optional, List, Tuple

warnings.filterwarnings("ignore")
import requests

# ========== 新浪行情API ==========

def sina_quote(codes: List[str]) -> List[Dict]:
    """
    获取新浪实时行情，支持多股票批量查询
    codes: ["sh600519", "sz000001"] 格式
    """
    if not codes:
        return []
    symbols = ",".join(codes)
    url = f"https://hq.sinajs.cn/list={symbols}"
    try:
        r = requests.get(url, headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}, timeout=10)
        r.encoding = "gbk"
        text = r.text.strip()
        results = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            m = re.match(r'var hq_str_(.+?)="(.+)"', line)
            if not m:
                continue
            code = m.group(1)
            fields = m.group(2).split(",")
            results.append({"code": code, "fields": fields})
        return results
    except Exception as e:
        print(f"[WARN] 新浪API失败: {e}", file=sys.stderr)
        return []


def sina_hist(code: str, days: int = 60) -> List[Dict]:
    """
    获取新浪历史K线数据
    code: "sh600519" 或 "sz000001" 格式
    """
    try:
        symbol = code if code.startswith(("sh", "sz")) else (("sh" if code.startswith(("6", "5")) else "sz") + code)
        url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {
            "symbol": symbol,
            "scale": 240,  # 日K
            "ma": 5,
            "datalen": days
        }
        r = requests.get(url, params=params, headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}, timeout=10)
        r.encoding = "utf-8"
        data = r.json()
        result = []
        for item in data:
            result.append({
                "date": item.get("day", "")[:10],
                "open": float(item.get("open", 0)),
                "close": float(item.get("close", 0)),
                "high": float(item.get("high", 0)),
                "low": float(item.get("low", 0)),
                "volume": float(item.get("volume", 0))
            })
        return result
    except Exception as e:
        print(f"[WARN] 新浪历史K线失败: {e}", file=sys.stderr)
        return []


# ========== 腾讯行情API ==========

def tencent_quote(codes: List[str]) -> List[Dict]:
    """
    获取腾讯实时行情
    codes: ["sh600519", "sz000001"] 格式
    """
    if not codes:
        return []
    symbols = ",".join(codes)
    url = f"https://qt.gtimg.cn/q={symbols}"
    try:
        r = requests.get(url, headers={"Referer": "https://gu.qq.com", "User-Agent": "Mozilla/5.0"}, timeout=10)
        r.encoding = "gbk"
        text = r.text.strip()
        results = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            m = re.match(r'v_(.+?)="(.+)"', line)
            if not m:
                continue
            code = m.group(1)
            fields = m.group(2).split("~")
            results.append({"code": code, "fields": fields})
        return results
    except Exception as e:
        print(f"[WARN] 腾讯API失败: {e}", file=sys.stderr)
        return []


# ========== 工具函数 ==========

def to_sina_code(code_input: str) -> str:
    """转换为新浪格式 sh600519 / sz000001"""
    code = code_input.strip().zfill(6)
    if code.startswith(("6", "5")):
        return f"sh{code}"
    else:
        return f"sz{code}"


def to_tencent_code(code_input: str) -> str:
    """转换为腾讯格式"""
    code = code_input.strip().zfill(6)
    if code.startswith(("6", "5")):
        return f"sh{code}"
    else:
        return f"sz{code}"


def parse_sina_quote(code: str, fields: List[str]) -> Dict[str, Any]:
    """解析新浪实时行情字段"""
    # fields: [0]名称 [1]今开 [2]昨收 [3]当前价 [4]最高 [5]最低 [6]买一价 [7]卖一价 ... 
    try:
        return {
            "name": fields[0] if len(fields) > 0 else code,
            "open": float(fields[1]) if len(fields) > 1 and fields[1] else 0,
            "prev_close": float(fields[2]) if len(fields) > 2 and fields[2] else 0,
            "price": float(fields[3]) if len(fields) > 3 and fields[3] else 0,
            "high": float(fields[4]) if len(fields) > 4 and fields[4] else 0,
            "low": float(fields[5]) if len(fields) > 5 and fields[5] else 0,
            "buy1": float(fields[6]) if len(fields) > 6 and fields[6] else 0,
            "sell1": float(fields[7]) if len(fields) > 7 and fields[7] else 0,
            "volume": int(fields[8]) if len(fields) > 8 and fields[8] else 0,
            "amount": float(fields[9]) if len(fields) > 9 and fields[9] else 0,
            "date": fields[30] if len(fields) > 30 else "",
            "time": fields[31] if len(fields) > 31 else "",
        }
    except:
        return {}


def parse_tencent_quote(fields: List[str]) -> Dict[str, Any]:
    """解析腾讯实时行情字段"""
    # fields[0]名称 [1]代码 [2]当前价 [3]昨收 [4]今开 [5]成交量 ...
    try:
        return {
            "name": fields[1] if len(fields) > 1 else "",
            "code": fields[2] if len(fields) > 2 else "",
            "price": float(fields[3]) if len(fields) > 3 and fields[3] else 0,
            "prev_close": float(fields[4]) if len(fields) > 4 and fields[4] else 0,
            "open": float(fields[5]) if len(fields) > 5 and fields[5] else 0,
            "volume": int(fields[6]) if len(fields) > 6 and fields[6] else 0,
        }
    except:
        return {}


# ========== 技术指标计算 ==========

def calc_ma(closes: List[float], periods: List[int] = [5, 10, 20, 60]) -> Dict[str, float]:
    result = {}
    for p in periods:
        if len(closes) >= p:
            result[f"ma{p}"] = round(sum(closes[-p:]) / p, 2)
        else:
            result[f"ma{p}"] = round(sum(closes) / len(closes), 2) if closes else 0
    return result


def calc_macd(closes: List[float]) -> Dict[str, Any]:
    if len(closes) < 26:
        return {"signal": "unknown", "dif": 0, "dea": 0, "description": "数据不足"}
    # EMA
    def ema(vals, period):
        k = 2 / (period + 1)
        result = vals[0]
        for v in vals[1:]:
            result = v * k + result * (1 - k)
        return result
    e12 = ema(closes[:12], 12)
    e26 = ema(closes[:26], 26)
    dif = e12 - e26
    dea = ema([dif] * 10, 10)
    hist = (dif - dea) * 2
    sig = "golden_cross" if dif > dea else "dead_cross"
    return {
        "signal": sig,
        "dif": round(dif, 4),
        "dea": round(dea, 4),
        "histogram": round(hist, 4),
        "description": "MACD金叉，短线强势" if sig == "golden_cross" else "MACD死叉，短线弱势"
    }


def calc_rsi(closes: List[float], period: int = 14) -> Dict[str, Any]:
    if len(closes) < period + 1:
        return {"value": 50.0, "signal": "中性"}
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(d if d > 0 else 0)
        losses.append(abs(d) if d < 0 else 0)
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return {"value": 100.0, "signal": "超买"}
    rs = ag / al
    rsi = round(100 - 100 / (1 + rs), 1)
    if rsi > 75: sig = "超买"
    elif rsi < 30: sig = "超卖"
    elif rsi > 60: sig = "强势"
    elif rsi < 40: sig = "弱势"
    else: sig = "中性"
    return {"value": rsi, "signal": sig}


# ========== 主函数 ==========

def stock_analysis(code_input: str) -> Dict[str, Any]:
    code = code_input.strip().zfill(6)
    sina_code = to_sina_code(code)
    tencent_code = to_tencent_code(code)
    print(f"[astock-selector] 分析股票: {code}", file=sys.stderr)

    # 1. 获取实时行情
    sina_data = sina_quote([sina_code])
    tencent_data = tencent_quote([tencent_code])

    if not sina_data and not tencent_data:
        return {"success": False, "error": f"无法获取 {code} 的行情数据", "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    # 解析实时数据
    sina_q = parse_sina_quote(sina_code, sina_data[0]["fields"]) if sina_data else {}
    tencent_q = parse_tencent_quote(tencent_data[0]["fields"]) if tencent_data else {}

    current_price = sina_q.get("price") or tencent_q.get("price", 0)
    prev_close = sina_q.get("prev_close") or tencent_q.get("prev_close", current_price)
    open_price = sina_q.get("open") or tencent_q.get("open", 0)
    high = sina_q.get("high") or tencent_q.get("price", 0)
    low = sina_q.get("low") or 0
    stock_name = sina_q.get("name") or tencent_q.get("name") or code

    change_pct = round((current_price / prev_close - 1) * 100, 2) if prev_close > 0 else 0

    # 2. 获取历史K线（用于技术分析）
    hist = sina_hist(sina_code, days=60)
    if not hist:
        # 备用：使用今日数据估算
        hist = [{
            "date": sina_q.get("date", ""),
            "open": open_price,
            "close": current_price,
            "high": high,
            "low": low,
            "volume": sina_q.get("volume", 0)
        }]

    closes = [h["close"] for h in hist if h["close"] > 0]
    volumes = [h["volume"] for h in hist if h["volume"] > 0]

    # 均线
    ma = calc_ma(closes, [5, 10, 20, 60])
    if ma["ma5"] > ma["ma10"] > ma["ma20"]:
        ma_trend = "多头排列"
    elif ma["ma5"] < ma["ma10"] < ma["ma20"]:
        ma_trend = "空头排列"
    else:
        ma_trend = "震荡整理"

    # MACD
    macd = calc_macd(closes)

    # RSI
    rsi = calc_rsi(closes)

    # 量比（今日成交量/昨日成交量）
    vol_ratio = 1.0
    if len(volumes) >= 2 and volumes[1] > 0:
        vol_ratio = round(volumes[0] / volumes[1], 2)

    price_up = closes[0] > closes[1] if len(closes) > 1 else (change_pct > 0)
    if price_up and vol_ratio > 1.2:
        vol_signal = "放量上涨"
    elif not price_up and vol_ratio > 1.2:
        vol_signal = "放量下跌"
    elif price_up:
        vol_signal = "缩量上涨"
    else:
        vol_signal = "缩量下跌"

    # 3. 资金流向（通过腾讯数据估算）
    amount = sina_q.get("amount") or 0
    volume = sina_q.get("volume") or 0
    if amount > 0 and volume > 0:
        avg_price = amount / volume
    else:
        avg_price = current_price

    main_net = 0.0
    if volume > 0 and avg_price > 0:
        # 粗略估算主力净流入（简化计算）
        main_net = (current_price - avg_price) * volume
    money_signal = f"主力净流入{main_net/1e8:.2f}亿" if main_net > 0 else f"主力净流出{abs(main_net)/1e8:.2f}亿" if main_net < 0 else "资金面平稳"

    # 4. 综合评分
    tech = 50
    if ma_trend == "多头排列": tech += 30
    elif ma_trend == "空头排列": tech -= 25
    if macd["signal"] == "golden_cross": tech += 25
    elif macd["signal"] == "dead_cross": tech -= 30
    if 35 <= rsi["value"] <= 65: tech += 10
    elif rsi["value"] < 30: tech += 15
    elif rsi["value"] > 80: tech -= 15
    tech = max(0, min(100, tech))

    money_score = 50
    if main_net > 1e8: money_score = 100
    elif main_net > 0: money_score = 70
    elif main_net < -1e8: money_score = 20
    money_score = max(0, min(100, money_score))

    # 基本面粗估（通过涨跌幅趋势）
    fund_score = 50 + min(max(change_pct * 5, -20), 20)

    total = round(tech * 0.4 + fund_score * 0.3 + money_score * 0.3, 1)

    # 5. 操作建议
    if total >= 75 and macd["signal"] == "golden_cross":
        advice = "建议买入"; risk_level = "中等"
    elif total >= 70:
        advice = "建议关注"; risk_level = "中等偏低"
    elif total >= 55:
        advice = "持有观望"; risk_level = "中等"
    elif total >= 40:
        advice = "建议减仓"; risk_level = "较高"
    else:
        advice = "建议离场"; risk_level = "高"

    if rsi["value"] < 30: advice = "RSI超卖，短中期可关注"
    elif rsi["value"] > 80: advice = "RSI超买，注意回调风险"

    # 6. 价格区间
    if current_price > 0:
        if ma_trend == "多头排列":
            entry_min = round(current_price * 0.97, 2)
            entry_max = round(current_price * 1.01, 2)
            target = round(current_price * 1.20, 2)
            stop = round(current_price * 0.93, 2)
        else:
            entry_min = round(current_price * 0.95, 2)
            entry_max = round(current_price * 1.02, 2)
            target = round(current_price * 1.12, 2)
            stop = round(current_price * 0.92, 2)
    else:
        entry_min = entry_max = target = stop = 0

    return {
        "success": True,
        "data": {
            "basic": {
                "code": code,
                "name": stock_name,
                "current_price": round(current_price, 2),
                "change_pct": change_pct,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "prev_close": round(prev_close, 2),
                "volume_ratio": vol_ratio,
            },
            "technical": {
                "macd": macd,
                "rsi": rsi,
                "ma": ma,
                "ma_trend": ma_trend,
                "volume": {"ratio": vol_ratio, "signal": vol_signal}
            },
            "money_flow": {
                "main_net_inflow": f"{main_net/1e8:.2f}亿",
                "signal": money_signal,
                "money_score": round(money_score, 1)
            },
            "overall_score": total,
            "tech_score": round(tech, 1),
            "fundamental_score": round(fund_score, 1),
            "advice": advice,
            "risk_level": risk_level,
            "price_levels": {
                "entry_min": entry_min,
                "entry_max": entry_max,
                "target_profit": target,
                "stop_loss": stop
            },
            "short_outlook": f"短线{'关注' if macd['signal']=='golden_cross' else '等待'}，均线{'支撑强' if ma_trend=='多头排列' else '需观察'}",
            "mid_outlook": f"中期{'偏多' if ma_trend=='多头排列' and total>60 else '偏中性'}，结合量能判断"
        },
        "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "disclaimer": "⚠️ 本分析仅供数据参考，不构成投资建议。股市有风险，投资需谨慎。"
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "用法: python stock_analysis.py <股票代码或名称>"}, ensure_ascii=False, indent=2))
        sys.exit(1)
    try:
        result = stock_analysis(sys.argv[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e), "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False, indent=2))
        sys.exit(1)

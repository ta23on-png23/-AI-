import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import os

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

# --- 1. 公式サイトから詳細な数値データを取得 ---
def fetch_detailed_data(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    
    res_data = {"players": [], "error": False}
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=7)
        soup = BeautifulSoup(res.content, "html.parser")
        rows = soup.select('tbody.is-p_top10')
        
        for i, row in enumerate(rows[:6]):
            # 選手名
            name = row.select_one('div.is-fs18 a').get_text(strip=True) if row.select_one('div.is-fs18 a') else f"{i+1}号艇"
            
            # 勝率データの取得（クラス名 is-lineH24 内の数値を想定）
            stats = row.select('td.is-lineH24')
            # [全国勝率, 全国2連対率, 当地勝率, 当地2連対率] の順で並んでいることが多い
            win_rate = float(stats[0].get_text(strip=True)) if len(stats) > 0 else 0.0
            motor_rate = float(stats[2].get_text(strip=True)) if len(stats) > 2 else 0.0
            
            res_data["players"].append({
                "no": i+1,
                "name": name,
                "win_rate": win_rate,     # 全国勝率
                "motor_rate": motor_rate  # モーター連対率
            })
        
        if not res_data["players"]: res_data["error"] = True
    except:
        res_data["error"] = True
    return res_data

# --- 2. スコアリング予測エンジン ---
def ai_score_prediction(players):
    # 各艇のスコアを計算（例：勝率×10 + モーター率×0.5 + 枠番補正）
    # 枠番補正：1号艇に大きなアドバンテージ、外にいくほどマイナス
    lane_bonus = [15.0, 5.0, 3.0, 2.0, 1.0, 0.0]
    
    scored_list = []
    for i, p in enumerate(players):
        # ここがAIの判断基準（アルゴリズム）になります
        score = (p["win_rate"] * 10) + (p["motor_rate"] * 0.8) + lane_bonus[i]
        scored_list.append({"no": p["no"], "score": score})
    
    # スコア順に並び替え
    ranked = sorted(scored_list, key=lambda x: x["score"], reverse=True)
    
    # 上位3艇を抽出
    top1 = ranked[0]["no"]
    top2 = ranked[1]["no"]
    top3 = ranked[2]["no"]
    top4 = ranked[3]["no"]
    
    # 買い目の生成（3連単）
    prediction = [
        f"{top1}-{top2}-{top3}",
        f"{top1}-{top2}-{top4}",
        f"{top1}-{top3}-{top2}",
        f"{top1}-{top3}-{top4}",
        f"{top2}-{top1}-{top3}"
    ]
    return prediction

# --- 3. UI ---
st.set_page_config(page_title="データ解析型AI予測", layout="wide")
st.title("📊 競艇データ解析・自動予測システム")

jcd = st.sidebar.selectbox("会場", list(STADIUMS.keys()), format_func=lambda x: STADIUMS[x])
rno = st.sidebar.number_input("レース番号", 1, 12, 1)

if st.sidebar.button("🚀 データを解析して予測"):
    data = fetch_detailed_data(jcd, rno)
    
    if data["error"]:
        st.error("データ取得エラー。公式サイトの構造が変わったか、アクセス制限の可能性があります。")
    else:
        # スコア計算による予測
        predictions = ai_score_prediction(data["players"])
        
        st.subheader(f"分析：{STADIUMS[jcd]} {rno}R")
        
        # 数値データの表示
        df = pd.DataFrame(data["players"])
        st.table(df)
        
        st.divider()
        st.header("🎯 AI 推奨買い目（3連単）")
        cols = st.columns(len(predictions))
        for i, p in enumerate(predictions):
            cols[i].metric(f"{i+1}位", p)

        st.caption("※この予測は、各艇の全国勝率、モーター連対率、および枠番有利度を独自アルゴリズムでスコア化した結果です。")

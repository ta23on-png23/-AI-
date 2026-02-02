import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import os

# --- 設定 ---
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

# --- 1. 公式サイトから「生の数値データ」を根こそぎ取る ---
def fetch_raw_stats(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    
    res_data = {"players": [], "error": False}
    try:
        res = requests.get(url, headers=HEADERS, timeout=7)
        soup = BeautifulSoup(res.content, "html.parser")
        rows = soup.select('tbody.is-p_top10')
        
        for i, row in enumerate(rows[:6]):
            # 選手基本情報
            name = row.select_one('div.is-fs18 a').get_text(strip=True) if row.select_one('div.is-fs18 a') else f"艇{i+1}"
            
            # 数値データの抽出 (勝率、2連対率などが入っているセル)
            # 公式サイトの構造上、td.is-lineH24 に勝率などの数値が並ぶ
            stats = row.select('td.is-lineH24')
            
            # 数値が取れない場合のガードを入れつつ、浮動小数点に変換
            try:
                win_rate_all   = float(stats[0].get_text(strip=True)) # 全国勝率
                win_rate_local = float(stats[2].get_text(strip=True)) # 当地勝率
                motor_rate     = float(stats[6].get_text(strip=True)) # モーター連対率
            except:
                win_rate_all, win_rate_local, motor_rate = 0.0, 0.0, 0.0

            res_data["players"].append({
                "no": i+1,
                "name": name,
                "win_all": win_rate_all,
                "win_local": win_rate_local,
                "motor": motor_rate
            })
        if not res_data["players"]: res_data["error"] = True
    except:
        res_data["error"] = True
    return res_data

# --- 2. 予測ロジック：能力値スコアリング ---
def calculate_ai_rank(players):
    # ここが「ソフト」の核となる計算式です。
    # 枠番(lane)の有利さと、選手の勝率、モーターの良さを点数化します。
    lane_weights = [20.0, 10.0, 7.0, 5.0, 2.0, 0.0] # 1号艇が圧倒的に有利な配点
    
    scored_players = []
    for i, p in enumerate(players):
        # スコア = (全国勝率 * 10) + (当地勝率 * 5) + (モーター率 * 0.5) + 枠番ボーナス
        total_score = (p["win_all"] * 10) + (p["win_local"] * 5) + (p["motor"] * 0.5) + lane_weights[i]
        scored_players.append({"no": p["no"], "score": total_score})
    
    # スコアが高い順に並び替え
    ranked = sorted(scored_players, key=lambda x: x["score"], reverse=True)
    return [r["no"] for r in ranked]

# --- 3. UI ---
st.set_page_config(page_title="データ解析予測ソフト", layout="wide")
st.title("🚤 競艇データ解析・全自動予測エンジン")

st.sidebar.header("設定")
jcd = st.sidebar.selectbox("会場", list(STADIUMS.keys()), format_func=lambda x: STADIUMS[x])
rno = st.sidebar.number_input("レース番号", 1, 12, 1)

if st.sidebar.button("📊 解析を実行", use_container_width=True):
    with st.spinner('公式データを解析中...'):
        data = fetch_raw_stats(jcd, rno)
    
    if data["error"]:
        st.error("データ取得に失敗しました。")
    else:
        # スコア計算
        rank_order = calculate_ai_rank(data["players"])
        top = rank_order # 1位から6位までの艇番リスト
        
        # 買い目の自動生成 (上位艇を組み合わせる)
        # 例：1位を軸に、2〜4位を相手にする
        forecasts = [
            f"{top[0]}-{top[1]}-{top[2]}",
            f"{top[0]}-{top[1]}-{top[3]}",
            f"{top[0]}-{top[2]}-{top[1]}",
            f"{top[0]}-{top[2]}-{top[3]}",
            f"{top[1]}-{top[0]}-{top[2]}"
        ]

        # 表示
        st.subheader(f"📍 {STADIUMS[jcd]} 第{rno}R 分析データ")
        st.table(pd.DataFrame(data["players"])) # 取得した生の数値を表で出す
        
        st.divider()
        st.header("🎯 AI解析による推奨買い目")
        c1, c2, c3, c4, c5 = st.columns(5)
        for i, f in enumerate(forecasts):
            st.columns(5)[i].metric(f"{i+1}位", f)
        
        st.info(f"【分析の根拠】現在の1位予想は{top[0]}号艇です。全国勝率と枠番の優位性から算出しました。")

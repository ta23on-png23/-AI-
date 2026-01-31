import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# ==========================================
# 1. ロジック部 (本来の logic.py)
# ==========================================
def judge_prediction(t1, t4, is_women_race):
    diff = t1 - t4
    if diff >= 0.10:
        return "4-5-1", f"⚠️ 中穴アラート！(タイム差:{diff:.2f})"
    else:
        return "1-2-3", "✅ 本命展開"

# ==========================================
# 2. スクレイピング部 (本来の scraper.py)
# ==========================================
def get_live_times(jcd, rno, date):
    # テスト用ダミーデータ（後ほど本番スクレイピングに書き換え）
    return 6.85, 6.74

# ==========================================
# 3. 画面表示部 (app.py)
# ==========================================
st.set_page_config(page_title="競艇予測AI", layout="wide")
st.title("🚤 競艇予測AI (完全合体版)")

STADIUMS = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

st.header("会場選択")
cols = st.columns(6)
selected_jcd = None

for i, (jcd, name) in enumerate(STADIUMS.items()):
    with cols[i % 6]:
        if st.button(f"{jcd} {name}", key=jcd, use_container_width=True):
            selected_jcd = jcd

if selected_jcd:
    st.divider()
    st.subheader(f"📍 {STADIUMS[selected_jcd]} のレース選択")
    r_cols = st.columns(12)
    selected_r = None
    for r in range(1, 13):
        with r_cols[r-1]:
            if st.button(f"{r}R", key=f"r{r}"):
                selected_r = r

    if selected_r:
        st.write(f"### {selected_r}R の予測分析")
        
        # 予測実行
        t1, t4 = get_live_times(selected_jcd, selected_r, "20260201")
        eye, msg = judge_prediction(t1, t4, is_women_race=False)
        
        st.info(msg)
        st.success(f"推奨買い目: {eye}")

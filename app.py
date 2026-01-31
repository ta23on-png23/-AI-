import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# --- 設定 ---
STADIUMS = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

st.set_page_config(page_title="競艇予測AI", layout="wide")
st.title("🚤 競艇予測AI プロトタイプ")

# --- 1. 会場選択エリア ---
st.header("会場選択")
# G級レース（SG/G1/G2/G3）を常時表示するためのエリア
st.info("💡 本日のG級レース開催場（仮）: 桐生(G1), 大村(G3)")

# 24場をエリアごとに並べる（簡略化のため4列×6行）
cols = st.columns(6)
selected_jcd = None

for i, (jcd, name) in enumerate(STADIUMS.items()):
    with cols[i % 6]:
        if st.button(f"{jcd} {name}", key=jcd, use_container_width=True):
            selected_jcd = jcd

# --- 2. レース選択と情報表示 ---
if selected_jcd:
    st.divider()
    st.subheader(f"📍 {STADIUMS[selected_jcd]} のレース選択")
    
    # 1〜12Rのボタン
    r_cols = st.columns(12)
    selected_r = None
    for r in range(1, 13):
        with r_cols[r-1]:
            if st.button(f"{r}R", key=f"r{r}"):
                selected_r = r

    if selected_r:
        st.write(f"### {selected_r}R の予測分析")
        # ここにスクレイピング関数（get_race_data, get_live_data）を呼び出すコードを合流させます
        st.warning("⚠️ 展示タイム取得中...（締切20分前に更新されます）")

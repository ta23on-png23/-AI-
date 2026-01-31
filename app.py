# app.py
import streamlit as st
from logic import judge_prediction  # logic.pyから読み込み
from scraper import get_live_times # scraper.pyから読み込み

st.title("競艇予測AI")

# 会場とレース選択のコード（以前のものを流用）
# ...

if st.button("予測実行"):
    # 1. データを取ってくる
    t1, t4 = get_live_times("04", "1", "20260201")
    
    # 2. ロジックで判定する
    eye, msg = judge_prediction(t1, t4, is_women_race=False)
    
    # 3. 表示する
    st.subheader(msg)
    st.write(f"推奨買い目: {eye}")

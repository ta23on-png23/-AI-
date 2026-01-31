import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime  # ← これが抜けているのが原因です
    
    # 1. 本物のデータを取得（取れない場合はNoneが返る）
    t1, t4, t_min = get_live_times(jcd, rno)
    
    # --- ステータス表示 ---
    if t1 is None:
        st.markdown("### <span style='color:red;'>⚠️ 展示タイム非反映（番組表データのみで算出）</span>", unsafe_allow_html=True)
        # 展示がない時の仮の数値（判定に影響しない同等の値）
        t1, t4, diff = 6.80, 6.80, 0.0
    else:
        diff = t1 - t4
        st.success(f"✅ 展示タイム反映済み (1号艇: {t1} / 4号艇: {t4} / 差: {diff:.2f})")

    # --- 2. 予測の生成 ---
    # 本命：1号艇頭の5点
    honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2"]
    # 穴目：4号艇頭の3点
    aname = ["4-5-1", "4-5-6", "4-1-5"]

    # --- 3. 画面表示エリア ---
    col_h, col_a = st.columns(2)
    
    with col_h:
        st.subheader("🎯 本命予想")
        for i, kumi in enumerate(honmei, 1):
            st.write(f"{i}位： **{kumi}**")
    
    with col_a:
        # 展示タイム差が0.10秒以上の時だけ特別に強調
        if t1 is not None and diff >= 0.10:
            st.error("🔥 穴目予想（タイム差による高配当アラート！）")
            for i, kumi in enumerate(aname, 1):
                st.write(f"{i}位： **{kumi}**")
        else:
            st.info("💡 穴目予想（展開・筋目）")
            for i, kumi in enumerate(aname, 1):
                st.write(f"{i}位： **{kumi}**")


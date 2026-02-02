import streamlit as st
import pandas as pd
import datetime
import os

# --- 設定データ ---
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

st.set_page_config(page_title="競艇的中率分析AI", layout="wide")

tab1, tab2 = st.tabs(["📝 予想入力・保存", "📊 成績分析ダッシュボード"])

with tab1:
    st.title("🚤 艇番入力・記録")
    
    with st.expander("📌 レース基本設定", expanded=True):
        c_st, c_rn, c_co = st.columns(3)
        with c_st: jcd = st.selectbox("会場", list(STADIUMS.keys()), format_func=lambda x: STADIUMS[x])
        with c_rn: rno = st.number_input("レース番号", 1, 12, 1)
        with c_co: condition = st.radio("水面/環境", ["通常", "満潮", "干潮", "強風"], horizontal=True)

    st.subheader("👤 選手データ（確認用）")
    col_names = st.columns(6)
    players_info = []
    for i in range(1, 7):
        with col_names[i-1]:
            name = st.text_input(f"{i}号艇 選手名", key=f"nm{i}")
            rank = st.selectbox(f"級別", ["A1", "A2", "B1", "B2"], key=f"rk{i}")
            players_info.append({"name": name, "rank": rank})

    st.divider()

    st.subheader("✍️ あなたの予想")
    y1, y2, y3 = st.columns(3)
    with y1: my_1 = st.number_input("1着", 1, 6, 1, key="y1")
    with y2: my_2 = st.number_input("2着", 1, 6, 2, key="y2")
    with y3: my_3 = st.number_input("3着", 1, 6, 3, key="y3")
    
    # ★ Excel対策：頭に ' をつけて文字列として扱う
    my_comb = f"'{my_1}-{my_2}-{my_3}"

    if st.button("💾 予想をCSVに保存", use_container_width=True):
        now_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        
        history_dict = {
            "日時": now_str,
            "会場": STADIUMS[jcd],
            "レース": f"{rno}R",
            "状況": condition,
            "1号艇": f"{players_info[0]['name']}({players_info[0]['rank']})",
            "あなたの予想": my_comb,
            "結果": "" 
        }
        df = pd.DataFrame([history_dict])
        csv_file = "race_history.csv"
        
        df.to_csv(csv_file, mode='a', index=False, header=not os.path.exists(csv_file), encoding="utf-8-sig")
        st.success(f"✅ 予想 {my_comb.replace(\"'\", \"\")} を保存しました。")

with tab2:
    st.title("📊 的中率分析")
    
    if os.path.exists("race_history.csv"):
        df_analysis = pd.read_csv("race_history.csv", dtype=str)
        # 分析時に ' を取り除いて比較する
        df_analysis["あなたの予想"] = df_analysis["あなたの予想"].str.replace("'", "")
        df_analysis["結果"] = df_analysis["結果"].str.replace("'", "")
        
        df_judged = df_analysis[df_analysis["結果"].notna() & (df_analysis["結果"] != "")]
        
        if not df_judged.empty:
            df_judged["的中"] = df_judged["あなたの予想"] == df_judged["結果"]
            hit_count = df_judged["的中"].sum()
            total_count = len(df_judged)
            hit_rate = (hit_count / total_count) * 100
            
            m1, m2, m3 = st.columns(3)
            m1.metric("総勝負数", f"{total_count} レース")
            m2.metric("的中数", f"{hit_count} 回")
            m3.metric("的中率", f"{hit_rate:.1f} %")
            
            st.divider()
            st.subheader("🔎 的中・不的中リスト")
            st.dataframe(df_judged, use_container_width=True)
        else:
            st.info("💡 CSVの『結果』列に正解を記入して保存してください。")
            st.dataframe(df_analysis)

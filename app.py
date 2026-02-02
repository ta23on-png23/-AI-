import streamlit as st
import pandas as pd
import datetime
import os

# --- 設定データ ---
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

st.set_page_config(page_title="競艇ハイブリッド予想", layout="wide")
st.title("🚤 艇番入力型・予想記録ツール")

# --- サイドバー：基本設定 ---
with st.sidebar:
    st.header("📌 レース設定")
    jcd = st.selectbox("会場", list(STADIUMS.keys()), format_func=lambda x: STADIUMS[x])
    rno = st.number_input("レース番号", 1, 12, 1)
    condition = st.radio("水面/環境", ["通常", "満潮", "干潮", "強風"])

# --- メインエリア：入力 ---
st.header(f"📍 {STADIUMS[jcd]} 第{rno}R")

# 選手情報は手動入力（またはメモ）として利用
col_names = st.columns(6)
players_info = []
for i in range(1, 7):
    with col_names[i-1]:
        name = st.text_input(f"{i}号艇 選手名", key=f"nm{i}", placeholder="苗字")
        rank = st.selectbox(f"級別", ["A1", "A2", "B1", "B2"], key=f"rk{i}")
        players_info.append({"name": name, "rank": rank})

st.divider()

# --- あなたの予想入力（数値） ---
st.subheader("✍️ あなたの予想（艇番を数値で入力）")
c1, c2, c3 = st.columns(3)
with c1:
    my_1st = st.number_input("1着（艇番）", 1, 6, 1)
with c2:
    my_2nd = st.number_input("2着（艇番）", 1, 6, 2)
with c3:
    my_3rd = st.number_input("3着（艇番）", 1, 6, 3)

my_combination = f"{my_1st}-{my_2nd}-{my_3rd}"

# --- 保存と実行 ---
if st.button("💾 予想を確定してCSVに保存", use_container_width=True):
    # AIによる簡易補足（例：1号艇のランクによる信頼度）
    target_rank = players_info[my_1st-1]["rank"]
    if my_1st == 1 and target_rank == "A1":
        ai_comment = "本命信頼度は高いです。"
    else:
        ai_comment = f"{my_1st}号艇の逆転展開を想定。"

    # CSVデータ作成
    history_dict = {
        "日時": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "会場": STADIUMS[jcd],
        "レース": f"{rno}R",
        "水面": condition,
        "1号艇": f"{players_info[0]['name']}({players_info[0]['rank']})",
        "あなたの予想": my_combination,
        "AIコメント": ai_comment,
        "結果": ""
    }
    
    # CSV保存
    df = pd.DataFrame([history_dict])
    csv_file = "race_history.csv"
    df.to_csv(csv_file, mode='a', index=False, header=not os.path.exists(csv_file), encoding="utf-8-sig")
    
    st.success(f"✅ 予想「{my_combination}」を保存しました！")
    st.info(f"🤖 AI分析: {ai_comment}")

# --- 履歴表示 ---
if os.path.exists("race_history.csv"):
    st.divider()
    st.subheader("📊 記録された予想履歴")
    history_df = pd.read_csv("race_history.csv")
    st.dataframe(history_df.tail(10), use_container_width=True)

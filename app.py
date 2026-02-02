import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import os

# --- 設定・定数 ---
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

# --- 1. 公式サイトから出走表・タイムを自動取得 ---
def fetch_race_data(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    idx_url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    bef_url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    
    res_data = {"players": [], "times": [], "title": "", "error": False}
    
    try:
        # 【出走表スキャン】
        r_idx = requests.get(idx_url, headers=HEADERS, timeout=7)
        soup_idx = BeautifulSoup(r_idx.content, "html.parser")
        
        boxes = soup_idx.select('tbody.is-p_top10')
        for box in boxes[:6]:
            name = box.select_one('div.is-fs18 a').get_text(strip=True).split(' ')[0] if box.select_one('div.is-fs18 a') else "？"
            # 級別をテキストから直接抽出
            txt = box.get_text()
            rank = "B1"
            for r in ["A1", "A2", "B2"]:
                if r in txt: rank = r; break
            res_data["players"].append({"name": name, "rank": rank})

        # 【展示タイムスキャン】
        r_bef = requests.get(bef_url, headers=HEADERS, timeout=7)
        soup_bef = BeautifulSoup(r_bef.content, "html.parser")
        tds = soup_bef.select('td')
        for td in tds:
            val = td.get_text(strip=True)
            if "." in val and len(val) == 4:
                try: res_data["times"].append(float(val))
                except: pass
        
        if len(res_data["players"]) < 6: res_data["error"] = True
    except:
        res_data["error"] = True
    return res_data

# --- 2. 予測エンジン ---
def generate_prediction(data):
    p1 = data["players"][0]
    p4 = data["players"][3]
    t1 = data["times"][0] if len(data["times"]) >= 6 else 9.99
    t4 = data["times"][3] if len(data["times"]) >= 6 else 9.99
    
    # 基本ロジック（イン逃げ信頼度）
    if p1['rank'] == "A1":
        honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-2-5"]
    elif p1['rank'] == "A2":
        honmei = ["1-2-3", "1-3-2", "2-1-3", "1-2-4", "1-4-2"]
    else:
        honmei = ["1-2-3", "2-1-3", "3-1-2", "1-3-2", "2-3-1"]

    # 穴目（4カド・展示タイム差）
    is_ana = (t4 <= t1 - 0.08)
    if is_ana:
        aname = ["4-5-1", "4-5-6", "4-1-5", "4-1-2"]
    else:
        aname = ["4-1-2", "2-3-4", "4-5-1", "1-4-5"]
        
    return honmei, aname, is_ana

# --- 3. UI画面 ---
st.set_page_config(page_title="完全自動・競艇予測ソフト", layout="wide")
st.title("🚤 競艇全自動予測 AI-BOT")

# 会場・レース選択
st.sidebar.header("📝 レース選択")
jcd = st.sidebar.selectbox("会場", list(STADIUMS.keys()), format_func=lambda x: STADIUMS[x])
rno = st.sidebar.number_input("レース番号", 1, 12, 1)

if st.sidebar.button("🚀 予測を実行する", use_container_width=True):
    with st.spinner('公式サイトからリアルタイムデータを取得中...'):
        data = fetch_race_data(jcd, rno)
    
    if data["error"]:
        st.error("データの取得に失敗しました。時間をおいて再度お試しください。")
    else:
        # 予測計算
        honmei, aname, is_ana = generate_prediction(data)
        
        # 結果表示
        st.header(f"📍 {STADIUMS[jcd]} 第{rno}R 予測結果")
        
        # 選手情報カード
        cols = st.columns(6)
        for i, p in enumerate(data["players"]):
            with cols[i]:
                st.markdown(f"""<div style="text-align:center; border:1px solid #ddd; padding:10px; border-radius:10px;">
                <small>{i+1}号艇</small><br><b>{p['name']}</b><br><span style="color:red;">{p['rank']}</span>
                </div>""", unsafe_allow_html=True)
        
        st.divider()

        # 予測パネル
        c1, c2 = st.columns(2)
        with c1:
            st.success("🎯 AI 本命予想")
            for i, k in enumerate(honmei[:5], 1):
                st.write(f"{i}位： **{k}**")
        with c2:
            if is_ana: st.error("🔥 AI 穴目予想（4カド・タイム優勢）")
            else: st.info("💡 AI 穴目予想")
            for i, k in enumerate(aname[:4], 1):
                st.write(f"{i}位： **{k}**")

        # 履歴保存（CSV）
        history_file = "race_history.csv"
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        new_history = pd.DataFrame([{
            "日時": now, "会場": STADIUMS[jcd], "レース": f"{rno}R",
            "1号艇": data['players'][0]['name'], "AI本命": honmei[0], "結果": ""
        }])
        new_history.to_csv(history_file, mode='a', index=False, header=not os.path.exists(history_file), encoding="utf-8-sig")
        st.toast("予測データをCSVに記録しました")

# 履歴表示（下部）
if os.path.exists("race_history.csv"):
    st.divider()
    st.subheader("📊 予測履歴（保存先: race_history.csv）")
    st.dataframe(pd.read_csv("race_history.csv").tail(5), use_container_width=True)

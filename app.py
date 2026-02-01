import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# --- 1. G級レース会場を「文字」で探す ---
def get_stadium_status():
    url = "https://www.boatrace.jp/owpc/pc/race/index"
    g_races = []
    try:
        res = requests.get(url, timeout=5)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 開催中の全テーブル行をチェック
        for row in soup.select('tr'):
            text = row.get_text()
            grade = ""
            if "SG" in text: grade = "SG"
            elif "G1" in text: grade = "G1"
            elif "G2" in text: grade = "G2"
            elif "G3" in text: grade = "G3"
            
            if grade:
                link = row.select_one('a[href*="jcd="]')
                if link:
                    href = link.get('href')
                    jcd = href.split('jcd=')[1].split('&')[0]
                    # 場名を取得（2文字または3文字の漢字を探す）
                    name_div = row.select_one('div.is-jcd')
                    name = name_div.get_text(strip=True) if name_div else "開催場"
                    g_races.append({"jcd": jcd, "name": name, "grade": grade})
    except: pass
    return g_races

# --- 2. 選手名・ランク・タイムを「構造」で探す ---
def get_fresh_race_data(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    idx_url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    bef_url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    
    data = {"t1": None, "t4": None, "t_min": 9.99, "players": []}
    
    try:
        # 【選手情報】
        res_idx = requests.get(idx_url, timeout=5)
        soup_idx = BeautifulSoup(res_idx.text, 'html.parser')
        
        # 1〜6号艇の枠を順番にスキャン
        for i in range(1, 7):
            # クラス名ではなく、HTML内の「1」「2」という数字の並びから選手を探す
            player_box = soup_idx.select(f'tbody.is-p_top10')
            if len(player_box) >= i:
                box = player_box[i-1]
                # 名前
                name_tag = box.select_one('div.is-fs18 a')
                name = name_tag.get_text(strip=True).split(' ')[0] if name_tag else f"{i}号艇"
                # 級別（A1, A2, B1, B2 という文字列を直接探す）
                box_text = box.get_text()
                rank = "B1"
                for r in ["A1", "A2", "B2"]:
                    if r in box_text:
                        rank = r
                        break
                data["players"].append({"name": name, "rank": rank})
            else:
                data["players"].append({"name": f"{i}号艇", "rank": "B1"})

        # 【展示タイム】
        res_bef = requests.get(bef_url, timeout=5)
        soup_bef = BeautifulSoup(res_bef.text, 'html.parser')
        # 4列目(展示タイム)の数字をすべて拾う
        all_tds = soup_bef.select('td')
        times = []
        for td in all_tds:
            txt = td.get_text(strip=True)
            if len(txt) == 4 and "." in txt: # "6.85" のような形式を探す
                try: times.append(float(txt))
                except: pass
        
        if len(times) >= 6:
            data["t1"], data["t4"], data["t_min"] = times[0], times[3], min(times)
    except: pass
    return data

# --- 3. UI ---
st.set_page_config(page_title="競艇予測AI", layout="wide")
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

st.title("🚤 競艇予測AI (完全同期版)")

# G級ボタン
g_list = get_stadium_status()
if g_list:
    st.markdown("### 🔥 本日のグレードレース")
    g_cols = st.columns(len(g_list))
    for i, r in enumerate(g_list):
        if g_cols[i].button(f"🏆 {r['grade']} {r['name']}", key=f"g_{r['jcd']}_{i}"):
            st.session_state.jcd, st.session_state.rno = r['jcd'], None
            st.rerun()
    st.divider()

# 会場選択
st.header("会場選択")
cols = st.columns(8)
for i, (jcd, name) in enumerate(STADIUMS.items()):
    if cols[i % 8].button(name, key=f"v_{jcd}"):
        st.session_state.jcd, st.session_state.rno = jcd, None
        st.rerun()

if 'jcd' in st.session_state:
    st.divider()
    st.subheader(f"📍 {STADIUMS[st.session_state.jcd]} レース選択")
    r_cols = st.columns(12)
    for r in range(1, 13):
        if r_cols[r-1].button(f"{r}R", key=f"r_{r}"):
            st.session_state.rno = r
            st.rerun()

# 予測表示
if 'jcd' in st.session_state and 'rno' in st.session_state:
    st.divider()
    res = get_fresh_race_data(st.session_state.jcd, st.session_state.rno)
    
    if len(res["players"]) >= 6:
        p1, p4 = res["players"][0], res["players"][3]
        
        st.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 10px solid #ff4b4b;">
            <h2 style="margin:0;">分析：{STADIUMS[st.session_state.jcd]} {st.session_state.rno}R</h2>
            <p style="font-size:20px;"><b>1号艇：{p1['name']} ({p1['rank']}) ／ 4号艇：{p4['name']} ({p4['rank']})</b></p>
        </div>""", unsafe_allow_html=True)

        is_t = res["t1"] is not None
        diff = (res["t1"] - res["t4"]) if is_t else 0.0
        is_ana = (is_t and res["t4"] == res["t_min"] and diff >= 0.10)

        # 予測生成
        if p1['rank'] == "A1": honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2"]
        else: honmei = ["1-2-3", "1-3-2", "2-1-3", "3-1-2", "1-2-4"]
        aname = ["4-5-1", "4-5-6", "4-1-5"] if is_ana else ["4-1-2", "4-2-1", "4-5-1"]

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 本命予想")
            for i, k in enumerate(honmei, 1): st.write(f"{i}位： **{k}**")
        with c2:
            if is_ana: st.error("🔥 穴目予想 (タイム差アリ)")
            else: st.info("💡 穴目予想")
            for i, k in enumerate(aname, 1): st.write(f"{i}位： **{k}**")

        st.divider()
        st.subheader("📝 予測の根拠")
        st.write(f"・1号艇 **{p1['name']}選手 ({p1['rank']})** を基準に判定。")
        if is_t:
            st.write(f"・展示タイム：1:{res['t1']} / 4:{res['t4']} (差:{diff:.2f})")
        else:
            st.markdown("・<span style='color:red;'>展示タイム未反映のため、番組表データで算出。</span>", unsafe_allow_html=True)

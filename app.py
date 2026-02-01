import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# --- ブラウザのふりをするための設定 ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# --- 1. G級レース会場を全テキストから抽出 ---
def get_stadium_status():
    url = "https://www.boatrace.jp/owpc/pc/race/index"
    g_races = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=7)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # すべてのリンクをチェックしてJCDとグレードを紐付け
        links = soup.select('a[href*="jcd="]')
        for link in links:
            text = link.get_text()
            href = link.get('href')
            grade = ""
            if "SG" in text: grade = "SG"
            elif "G1" in text: grade = "G1"
            elif "G2" in text: grade = "G2"
            elif "G3" in text: grade = "G3"
            
            if grade and "jcd=" in href:
                jcd = href.split('jcd=')[1].split('&')[0]
                # 重複を避けて追加
                if not any(r['jcd'] == jcd for r in g_races):
                    g_races.append({"jcd": jcd, "name": text.replace(grade, "").strip(), "grade": grade})
    except: pass
    return g_races

# --- 2. 選手名・ランク・タイムを構造に頼らず抽出 ---
def get_fresh_race_data(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    idx_url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    bef_url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    
    data = {"t1": None, "t4": None, "t_min": 9.99, "players": []}
    
    try:
        # 【選手情報】
        res_idx = requests.get(idx_url, headers=HEADERS, timeout=7)
        soup_idx = BeautifulSoup(res_idx.text, 'html.parser')
        
        # 1〜6号艇のブロックを抽出
        player_boxes = soup_idx.select('tbody.is-p_top10')
        for i in range(6):
            if i < len(player_boxes):
                box = player_boxes[i]
                name_tag = box.select_one('div.is-fs18 a')
                name = name_tag.get_text(strip=True).split(' ')[0] if name_tag else f"{i+1}号艇"
                
                # テキスト全体からランクを探す
                txt = box.get_text()
                rank = "B1"
                for r in ["A1", "A2", "B2"]:
                    if r in txt:
                        rank = r
                        break
                data["players"].append({"name": name, "rank": rank})
            else:
                data["players"].append({"name": f"{i+1}号艇", "rank": "B1"})

        # 【展示タイム】
        res_bef = requests.get(bef_url, headers=HEADERS, timeout=7)
        soup_bef = BeautifulSoup(res_bef.text, 'html.parser')
        # 数字（タイム）らしきものを全抽出
        times = []
        for td in soup_bef.select('td'):
            val = td.get_text(strip=True)
            if len(val) == 4 and "." in val:
                try: times.append(float(val))
                except: pass
        
        if len(times) >= 6:
            data["t1"], data["t4"], data["t_min"] = times[0], times[3], min(times)
    except: pass
    return data

# --- 3. メインUI ---
st.set_page_config(page_title="競艇予測AI", layout="wide")
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

st.title("🚤 競艇予測AI (安定稼働版)")

# G級表示（セッションで保持せず毎回取得）
g_list = get_stadium_status()
if g_list:
    st.markdown("### 🔥 本日のグレードレース")
    g_cols = st.columns(len(g_list))
    for i, r in enumerate(g_list):
        if g_cols[i].button(f"🏆 {r['grade']} {r['name']}", key=f"g_{r['jcd']}_{i}", use_container_width=True):
            st.session_state.jcd, st.session_state.rno = r['jcd'], None
            st.rerun()
    st.divider()

st.header("会場選択")
cols = st.columns(8)
for i, (jcd, name) in enumerate(STADIUMS.items()):
    if cols[i % 8].button(name, key=f"v_{jcd}", use_container_width=True):
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

# --- 予測・分析表示 ---
if 'jcd' in st.session_state and 'rno' in st.session_state:
    st.divider()
    with st.spinner('最新データを解析中...'):
        res = get_fresh_race_data(st.session_state.jcd, st.session_state.rno)
    
    if len(res["players"]) >= 6:
        p1, p4 = res["players"][0], res["players"][3]
        
        st.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 10px solid #ff4b4b;">
            <h2 style="margin:0;">分析：{STADIUMS[st.session_state.jcd]} 第 {st.session_state.rno} レース</h2>
            <p style="font-size:22px; margin-top:10px;"><b>1号艇：{p1['name']} ({p1['rank']}) ／ 4号艇：{p4['name']} ({p4['rank']})</b></p>
        </div>""", unsafe_allow_html=True)

        is_t = res["t1"] is not None
        diff = (res["t1"] - res["t4"]) if is_t else 0.0
        is_ana = (is_t and res["t4"] == res["t_min"] and diff >= 0.10)

        # 予測アルゴリズム
        if p1['rank'] == "A1": honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2"]
        elif p1['rank'] == "A2": honmei = ["1-2-3", "1-3-2", "1-2-4", "1-4-2", "2-1-3"]
        else: honmei = ["1-2-3", "1-3-2", "2-1-3", "3-1-2", "1-2-4"]
        
        aname = ["4-5-1", "4-5-6", "4-1-5"] if is_ana else ["4-1-2", "4-2-1", "4-1-5"]

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
        st.write(f"・1号艇 **{p1['name']}選手 ({p1['rank']})** の実力を軸に設定。")
        if is_t:
            st.write(f"・展示タイムを反映。1号艇({res['t1']})と4号艇({res['t4']})の差は **{diff:.2f}秒** です。")
            if is_ana: st.write(f"・4号艇 **{p4['name']}選手** が最速かつ大幅なタイム差をつけているため穴目推奨。")
        else:
            st.markdown("・<span style='color:red;'>⚠️ 展示タイムがまだ出ていないため、番組表のデータのみで算出しています。</span>", unsafe_allow_html=True)

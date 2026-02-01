import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# --- 1. グレードレース取得（ロジック強化版） ---
def get_stadium_status():
    url = "https://www.boatrace.jp/owpc/pc/race/index"
    g_races = []
    try:
        response = requests.get(url, timeout=5)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 開催場ブロックをすべて取得
        race_items = soup.select('td.is-arrowNone')
        for item in race_items:
            link = item.select_one('a')
            if not link: continue
            
            # グレード判定（アイコン画像やテキストから判別）
            grade_label = ""
            img = item.select_one('img')
            if img:
                alt = img.get('alt', '')
                if 'SG' in alt: grade_label = "SG"
                elif 'G1' in alt: grade_label = "G1"
                elif 'G2' in alt: grade_label = "G2"
                elif 'G3' in alt: grade_label = "G3"
            
            # 画像がない場合、テキストからも探す
            if not grade_label:
                text = item.get_text()
                for g in ["SG", "G1", "G2", "G3"]:
                    if g in text:
                        grade_label = g
                        break
            
            if grade_label:
                name_tag = item.select_one('div.is-jcd')
                name = name_tag.get_text(strip=True) if name_tag else "不明"
                href = link.get('href', '')
                if 'jcd=' in href:
                    jcd = href.split('jcd=')[1].split('&')[0]
                    g_races.append({"jcd": jcd, "name": name, "grade": grade_label})
    except: pass
    return g_races

# --- 2. 最新データ取得 ---
def get_fresh_race_data(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    idx_url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    bef_url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    
    data = {"t1": None, "t4": None, "t_min": 9.99, "is_women": False, "players": [], "title": ""}
    
    try:
        # 選手・級別
        res_idx = requests.get(idx_url, timeout=5)
        soup_idx = BeautifulSoup(res_idx.text, 'html.parser')
        data["title"] = soup_idx.select_one('h2.label2_title').get_text(strip=True) if soup_idx.select_one('h2.label2_title') else ""
        
        tbodies = soup_idx.select('table.is-w748 tbody.is-p_top10')
        for tbody in tbodies[:6]:
            name_tag = tbody.select_one('div.is-fs18 a')
            name = name_tag.get_text(strip=True).split(' ')[0] if name_tag else "？"
            rank_tag = tbody.select_one('span[class*="is-rank"]')
            rank = rank_tag.get_text(strip=True) if rank_tag else "B1"
            data["players"].append({"name": name, "rank": rank})

        # 展示タイム
        res_bef = requests.get(bef_url, timeout=5)
        soup_bef = BeautifulSoup(res_bef.text, 'html.parser')
        table = soup_bef.select_one('table.is-w748')
        if table:
            times = []
            for row in table.select('tbody'):
                cells = row.select('td')
                if len(cells) >= 4:
                    try: times.append(float(cells[3].get_text(strip=True)))
                    except: continue
            if len(times) >= 6:
                data["t1"], data["t4"], data["t_min"] = times[0], times[3], min(times)
    except: pass
    return data

# --- 3. UI ---
st.set_page_config(page_title="競艇予測AI", layout="wide")
st.title("🚤 競艇予測AI (G級検知強化版)")

# G級取得（毎回チェック）
g_races = get_stadium_status()

if g_races:
    st.markdown("### 🔥 本日のグレードレース")
    g_cols = st.columns(len(g_races))
    for i, r in enumerate(g_races):
        if g_cols[i].button(f"🏆 {r['grade']} {r['name']}", key=f"g_{r['jcd']}", use_container_width=True):
            st.session_state.jcd, st.session_state.rno = r['jcd'], None
            st.rerun()
    st.divider()

STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

st.header("全会場")
cols = st.columns(8)
for i, (jcd, name) in enumerate(STADIUMS.items()):
    if cols[i % 8].button(name, key=f"btn_{jcd}"):
        st.session_state.jcd, st.session_state.rno = jcd, None
        st.rerun()

if 'jcd' in st.session_state:
    st.divider()
    st.subheader(f"📍 {STADIUMS[st.session_state.jcd]} レース選択")
    r_cols = st.columns(12)
    for r in range(1, 13):
        if r_cols[r-1].button(f"{r}R", key=f"r{r}"):
            st.session_state.rno = r
            st.rerun()

if 'jcd' in st.session_state and 'rno' in st.session_state:
    st.divider()
    res = get_fresh_race_data(st.session_state.jcd, st.session_state.rno)
    
    if len(res["players"]) >= 6:
        p1, p4 = res["players"][0], res["players"][3]
        
        st.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 10px solid #ff4b4b;">
            <h2 style="margin:0;">分析：{STADIUMS[st.session_state.jcd]} {st.session_state.rno}R</h2>
            <p style="margin:5px 0 0 0;">1号艇：{p1['name']} ({p1['rank']}) ／ 4号艇：{p4['name']} ({p4['rank']})</p>
        </div>""", unsafe_allow_html=True)

        # 予測
        is_t = res["t1"] is not None
        diff = (res["t1"] - res["t4"]) if is_t else 0.0
        is_ana = (is_t and res["t4"] == res["t_min"] and diff >= 0.10)

        if p1['rank'] == "A1": honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2"]
        elif p1['rank'] == "A2": honmei = ["1-2-3", "1-3-2", "1-2-4", "1-4-2", "1-3-4"]
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
        st.write(f"・1号艇 **{p1['name']}選手 ({p1['rank']})** の実力を基準に算出。")
        if is_t:
            st.write(f"・展示タイム差：**{diff:.2f}秒**。")
            if is_ana: st.write(f"・4号艇 **{p4['name']}選手** が最速かつ0.10秒差以上の優位性あり。")
        else:
            st.markdown("・<span style='color:red;'>展示タイム未反映のため、番組表データのみで算出しています。</span>", unsafe_allow_html=True)

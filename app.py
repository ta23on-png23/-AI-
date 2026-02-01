import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# --- 1. グレードレース取得 ---
def get_stadium_status():
    url = "https://www.boatrace.jp/owpc/pc/race/index"
    g_races = []
    try:
        response = requests.get(url, timeout=5)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('div.is-jcd')
        for item in items:
            link = item.find_parent('a')
            if link:
                classes = " ".join(link.get('class', []))
                grade = ""
                if 'is-gradeSG' in classes: grade = "SG"
                elif 'is-gradeG1' in classes: grade = "G1"
                elif 'is-gradeG2' in classes: grade = "G2"
                elif 'is-gradeG3' in classes: grade = "G3"
                if grade:
                    name = item.get_text(strip=True)
                    jcd = link.get('href').split('jcd=')[1].split('&')[0]
                    g_races.append({"jcd": jcd, "name": name, "grade": grade})
    except: pass
    return g_races

# --- 2. 特定レースの最新データを取得 (キャッシュ無効化) ---
def get_fresh_race_data(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    idx_url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    bef_url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    
    data = {"t1": None, "t4": None, "t_min": 9.99, "is_women": False, "ranks": ["B1"]*6, "title": ""}
    
    try:
        # 番組表から級別を取得
        res_idx = requests.get(idx_url, timeout=5)
        soup_idx = BeautifulSoup(res_idx.text, 'html.parser')
        data["title"] = soup_idx.select_one('h2.label2_title').text if soup_idx.select_one('h2.label2_title') else ""
        data["is_women"] = any(w in data["title"] for w in ["女子", "ヴィーナス", "レディース"])
        
        # 級別を抽出
        ranks = []
        rows = soup_idx.select('table.is-w748 tbody')
        for row in rows[:6]:
            r_span = row.select_one('span[class*="is-rank"]')
            ranks.append(r_span.text.strip() if r_span else "B1")
        data["ranks"] = ranks

        # 展示タイムを抽出
        res_bef = requests.get(bef_url, timeout=5)
        soup_bef = BeautifulSoup(res_bef.text, 'html.parser')
        times = []
        table = soup_bef.select_one('table.is-w748')
        if table:
            for row in table.select('tbody'):
                cells = row.select('td')
                if len(cells) >= 4:
                    try: times.append(float(cells[3].get_text(strip=True)))
                    except: continue
        if len(times) >= 6:
            data["t1"], data["t4"], data["t_min"] = times[0], times[3], min(times)
    except: pass
    return data

# --- 3. UI表示 ---
st.set_page_config(page_title="競艇予測AI", layout="wide")
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

st.title("🚤 競艇予測AI")

# 会場・レース選択
g_races = get_stadium_status()
if g_races:
    st.markdown("### 🔥 本日のグレードレース")
    g_cols = st.columns(len(g_races))
    for i, r in enumerate(g_races):
        if g_cols[i].button(f"🏆 {r['grade']} {r['name']}", key=f"g_{r['jcd']}"):
            st.session_state.jcd, st.session_state.rno = r['jcd'], None
            st.rerun()

st.header("会場")
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

# --- 4. 予測ロジック実行 (ここが重要) ---
if 'jcd' in st.session_state and 'rno' in st.session_state:
    st.divider()
    jcd, rno = st.session_state.jcd, st.session_state.rno
    
    # ★ 毎回最新データを取得するように修正
    res = get_fresh_race_data(jcd, rno)
    r1_rank = res["ranks"][0] # 1号艇の級別
    
    st.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 10px solid #ff4b4b;">
        <h2 style="margin: 0;">分析中：{STADIUMS[jcd]} 第 {rno} レース ({r1_rank}級)</h2></div>""", unsafe_allow_html=True)

    # 判定
    is_t_ok = res["t1"] is not None
    diff = (res["t1"] - res["t4"]) if is_t_ok else 0.0
    is_ana = (is_t_ok and res["t4"] == res["t_min"] and diff >= 0.10)

    # ★ 級別とタイムに基づいて予測を動的に生成
    if r1_rank == "A1":
        honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2"]
    elif r1_rank == "A2":
        honmei = ["1-2-3", "1-3-2", "1-2-4", "1-4-2", "1-3-4"]
    else: # B級
        honmei = ["1-2-3", "1-3-2", "2-1-3", "3-1-2", "1-2-4"]

    aname = ["4-5-1", "4-5-6", "4-1-5"] if is_ana else ["4-1-2", "4-2-1", "4-1-5"]

    # 表示
    col_h, col_a = st.columns(2)
    with col_h:
        st.subheader("🎯 本命予想")
        for i, k in enumerate(honmei, 1): st.write(f"{i}位： **{k}**")
    with col_a:
        if is_ana: st.error("🔥 穴目予想 (タイム差アリ！)")
        else: st.info("💡 穴目予想")
        for i, k in enumerate(aname, 1): st.write(f"{i}位： **{k}**")

    # 理由表示
    st.markdown("---")
    st.subheader("📝 予測の根拠")
    st.write(f"・1号艇の階級 (**{r1_rank}**) を基準に本命を算出。")
    if is_t_ok:
        st.write(f"・展示タイムを反映。1号艇と4号艇の差は **{diff:.2f}秒** です。")
        if is_ana: st.write("・**【注目】** 4号艇が最速かつ0.10秒以上の差があるため、カドまくりを最優先。")
    else:
        st.markdown("・<span style='color:red;'>展示タイム未反映のため、番組表データのみで算出しています。</span>", unsafe_allow_html=True)

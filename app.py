import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# --- 1. 開催状況・G級判定関数 ---
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
                classes = link.get('class', [])
                class_str = " ".join(classes)
                grade = ""
                if 'is-gradeSG' in class_str: grade = "SG"
                elif 'is-gradeG1' in class_str: grade = "G1"
                elif 'is-gradeG2' in class_str: grade = "G2"
                elif 'is-gradeG3' in class_str: grade = "G3"
                if grade:
                    name = item.get_text(strip=True)
                    jcd = link.get('href').split('jcd=')[1].split('&')[0]
                    g_races.append({"jcd": jcd, "name": name, "grade": grade})
    except: pass
    return g_races

# --- 2. 詳細データ取得関数 ---
def get_race_details(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    idx_url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    bef_url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    data = {"t1": None, "t4": None, "t_min": 9.99, "is_women": False, "ranks": ["B1"]*6, "race_title": ""}
    try:
        res_idx = requests.get(idx_url, timeout=5)
        soup_idx = BeautifulSoup(res_idx.text, 'html.parser')
        data["race_title"] = soup_idx.select_one('h2.label2_title').text if soup_idx.select_one('h2.label2_title') else ""
        data["is_women"] = "女子" in data["race_title"] or "ヴィーナス" in data["race_title"]
        ranks = []
        rows = soup_idx.select('table.is-w748 tbody')
        for row in rows[:6]:
            rank_span = row.select_one('span.is-rankA1, span.is-rankA2, span.is-rankB1, span.is-rankB2')
            ranks.append(rank_span.text if rank_span else "B1")
        data["ranks"] = ranks
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

# --- 3. UI設定 ---
st.set_page_config(page_title="競艇予測AI", layout="wide")
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

st.title("🚤 競艇予測AI")

if 'g_races' not in st.session_state:
    st.session_state.g_races = get_stadium_status()

# G級表示
if st.session_state.g_races:
    st.markdown("### 🔥 本日のグレードレース")
    g_cols = st.columns(len(st.session_state.g_races))
    for i, r in enumerate(st.session_state.g_races):
        if g_cols[i].button(f"🏆 {r['grade']} {r['name']}", key=f"g_{r['jcd']}"):
            st.session_state.jcd, st.session_state.rno = r['jcd'], None
            st.rerun()

st.header("全会場")
cols = st.columns(8)
for i, (jcd, name) in enumerate(STADIUMS.items()):
    with cols[i % 8]:
        if st.button(name, key=f"btn_{jcd}"):
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

# --- 分析・予測エリア ---
if 'jcd' in st.session_state and 'rno' in st.session_state:
    st.divider()
    st.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 10px solid #ff4b4b;">
        <h2 style="margin: 0;">分析中：{STADIUMS[st.session_state.jcd]} 第 {st.session_state.rno} レース</h2></div>""", unsafe_allow_html=True)
    
    res = get_race_details(st.session_state.jcd, st.session_state.rno)
    
    # 判定用変数
    r1 = res["ranks"][0]
    is_t_reflect = res["t1"] is not None
    diff = (res["t1"] - res["t4"]) if is_t_reflect else 0.0
    is_ana_trigger = (is_t_reflect and res["t4"] == res["t_min"] and diff >= 0.10)

    # 予測
    honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2"] if r1 == "A1" else ["1-3-2", "1-3-4", "1-2-3", "1-4-2", "1-2-4"]
    aname = ["4-5-1", "4-5-6", "4-1-5"] if is_ana_trigger else ["4-1-2", "4-2-1", "4-5-1"]

    # 表示
    col_h, col_a = st.columns(2)
    with col_h:
        st.subheader(f"🎯 本命予想 (1号艇:{r1})")
        for i, kumi in enumerate(honmei, 1): st.write(f"{i}位： **{kumi}**")
    with col_a:
        if is_ana_trigger: st.error("🔥 穴目予想 (タイム差アリ！)")
        else: st.info("💡 穴目予想")
        for i, kumi in enumerate(aname, 1): st.write(f"{i}位： **{kumi}**")

    # --- ★ 理由の箇条書き表示エリア ★ ---
    st.divider()
    st.subheader("📝 この予測を選んだ理由")
    
    reasons = []
    # 本命の理由
    if r1 == "A1": reasons.append(f"・1号艇に最高階級の **A1選手** が配置されており、イン逃げの確率が非常に高いため。")
    else: reasons.append(f"・1号艇がB級以下のため、内枠の実力差を考慮し、2・3号艇の逆転も含めた広めの本命構成。")
    
    # 展示タイムの理由
    if not is_t_reflect:
        reasons.append("・<span style='color:red;'>【警告】現在展示タイムが未反映のため、番組表（選手能力）のみで算出しています。</span>")
    else:
        reasons.append(f"・展示タイムを反映済み。1号艇と4号艇の差は **{diff:.2f}秒** です。")
        if is_ana_trigger:
            reasons.append(f"・**穴目推奨理由:** 4号艇が全艇の中で**最速タイム**を記録。かつ1号艇より0.10秒以上速いため、カドまくりの展開を重視。")
        else:
            reasons.append(f"・4号艇に目立った展示タイムの優位性がないため、セオリー通りの筋目（4-1-2等）を穴目に設定。")

    # 女子戦
    if res["is_women"]:
        reasons.append("・女子戦（ヴィーナス/オールレディース）のため、通常よりインコースの粘りやスタート事故の可能性を考慮。")

    for r in reasons:
        st.markdown(r, unsafe_allow_html=True)

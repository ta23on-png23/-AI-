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
        
        # 開催場リストを取得
        items = soup.select('div.is-jcd')
        for item in items:
            # 親要素を遡ってグレードクラスを確認
            link = item.find_parent('a')
            if link:
                classes = link.get('class', [])
                grade = ""
                if 'is-gradeSG' in classes: grade = "SG"
                elif 'is-gradeG1' in classes: grade = "G1"
                elif 'is-gradeG2' in classes: grade = "G2"
                elif 'is-gradeG3' in classes: grade = "G3"
                
                if grade:
                    name = item.get_text(strip=True)
                    # JCD(場コード)はURLから抽出
                    jcd = link.get('href').split('jcd=')[1].split('&')[0]
                    g_races.append({"jcd": jcd, "name": name, "grade": grade})
    except:
        pass
    return g_races

# --- 2. 展示タイム取得関数 ---
def get_live_times(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    try:
        response = requests.get(url, timeout=5)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        times = []
        table = soup.select_one('table.is-w748')
        if not table: return None, None, None
        rows = table.select('tbody')
        for row in rows:
            cells = row.select('td')
            if len(cells) >= 4:
                t_val = cells[3].get_text(strip=True)
                try: times.append(float(t_val))
                except: continue
        if len(times) >= 6: return times[0], times[3], min(times)
    except: pass
    return None, None, None

# --- 3. 画面基本構成 ---
st.set_page_config(page_title="競艇予測AI", layout="wide")
st.title("🚤 競艇予測AI (G級対応版)")

# G級レースの自動取得
if 'g_races' not in st.session_state:
    st.session_state.g_races = get_stadium_status()

# --- 4. G級特設エリア ---
if st.session_state.g_races:
    st.markdown("### 🔥 本日の注目グレードレース")
    g_cols = st.columns(len(st.session_state.g_races))
    for i, race in enumerate(st.session_state.g_races):
        with g_cols[i]:
            if st.button(f"🏆 {race['grade']} {race['name']}", key=f"g_{race['jcd']}", use_container_width=True):
                st.session_state.jcd = race['jcd']
                if 'rno' in st.session_state: del st.session_state.rno
                st.rerun()
    st.divider()

# --- 5. 通常会場選択 ---
STADIUMS = {"01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川", "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国", "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀", "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松", "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"}

st.header("全会場")
cols = st.columns(6)
for i, (jcd, name) in enumerate(STADIUMS.items()):
    with cols[i % 6]:
        if st.button(f"{jcd} {name}", key=jcd, use_container_width=True):
            st.session_state.jcd = jcd
            if 'rno' in st.session_state: del st.session_state.rno
            st.rerun()

# --- 6. レース選択・予測表示 ---
if 'jcd' in st.session_state:
    st.divider()
    st.subheader(f"📍 {STADIUMS[st.session_state.jcd]} レース選択")
    r_cols = st.columns(12)
    for r in range(1, 13):
        with r_cols[r-1]:
            if st.button(f"{r}R", key=f"r{r}"):
                st.session_state.rno = r

if 'rno' in st.session_state:
    jcd, rno = st.session_state.jcd, st.session_state.rno
    t1, t4, t_min = get_live_times(jcd, rno)
    
    if t1 is None:
        st.markdown("### <span style='color:red;'>⚠️ 展示タイム非反映（番組表データのみで算出）</span>", unsafe_allow_html=True)
        diff = 0.0
    else:
        diff = t1 - t4
        st.success(f"✅ 展示タイム反映済み (1:{t1} / 4:{t4} / 差:{diff:.2f})")

    honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2"]
    aname = ["4-5-1", "4-5-6", "4-1-5"]

    col_h, col_a = st.columns(2)
    with col_h:
        st.subheader("🎯 本命予想（上位5番）")
        for i, kumi in enumerate(honmei, 1):
            st.write(f"{i}位： **{kumi}**")
    with col_a:
        if t1 and diff >= 0.10:
            st.error("🔥 穴目予想（上位3番・タイム差アリ！）")
        else:
            st.info("💡 穴目予想（上位3番・参考）")
        for i, kumi in enumerate(aname, 1):
            st.write(f"{i}位： **{kumi}**")

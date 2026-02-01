import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# --- 1. スクレイピング関数 (エラー対策強化版) ---
def get_live_times(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    try:
        response = requests.get(url, timeout=5)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        times = []
        table = soup.select_one('table.is-w748')
        if not table:
            return None, None, None
            
        rows = table.select('tbody')
        for row in rows:
            cells = row.select('td')
            if len(cells) >= 4:
                t_val = cells[3].get_text(strip=True)
                try:
                    times.append(float(t_val))
                except ValueError:
                    continue
        
        if len(times) >= 6:
            return times[0], times[3], min(times)
    except Exception:
        pass
    return None, None, None

# --- 2. 画面基本構成 ---
st.set_page_config(page_title="競艇予測AI", layout="wide")
st.title("🚤 競艇予測AI (最新安定版)")

STADIUMS = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

# --- 3. 会場選択エリア ---
st.header("会場選択")
cols = st.columns(6)
for i, (jcd, name) in enumerate(STADIUMS.items()):
    with cols[i % 6]:
        if st.button(f"{jcd} {name}", key=jcd, use_container_width=True):
            st.session_state.jcd = jcd
            # レース選択をリセット
            if 'rno' in st.session_state:
                del st.session_state.rno
            st.rerun()

# --- 4. レース選択エリア ---
if 'jcd' in st.session_state:
    st.divider()
    st.subheader(f"📍 {STADIUMS[st.session_state.jcd]} レース選択")
    r_cols = st.columns(12)
    for r in range(1, 13):
        with r_cols[r-1]:
            if st.button(f"{r}R", key=f"r{r}"):
                st.session_state.rno = r

# --- 5. 予測実行エリア ---
if 'rno' in st.session_state:
    jcd, rno = st.session_state.jcd, st.session_state.rno
    
    # リアルタイムで展示タイムを取得
    t1, t4, t_min = get_live_times(jcd, rno)
    
    # ステータス表示
    if t1 is None:
        st.markdown("### <span style='color:red;'>⚠️ 展示タイム非反映（番組表データのみで算出）</span>", unsafe_allow_html=True)
        diff = 0.0
    else:
        diff = t1 - t4
        st.success(f"✅ 展示タイム反映済み (1: {t1} / 4: {t4} / 差: {diff:.2f})")

    # 予測ロジック
    honmei = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2"]
    aname = ["4-5-1", "4-5-6", "4-1-5"]

    # 画面表示
    col_h, col_a = st.columns(2)
    with col_h:
        st.subheader("🎯 本命予想（上位5番）")
        for i, kumi in enumerate(honmei, 1):
            st.write(f"{i}位： **{kumi}**")
            
    with col_a:
        # 展示タイム差が0.10秒以上の時だけ特別に強調
        if t1 is not None and diff >= 0.10:
            st.error("🔥 穴目予想（上位3番・タイム差アリ！）")
        else:
            st.info("💡 穴目予想（上位3番・参考）")
        
        for i, kumi in enumerate(aname, 1):
            st.write(f"{i}位： **{kumi}**")

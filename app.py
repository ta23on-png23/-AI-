import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# --- 1. スクレイピング関数 (公式サイトからデータを取る) ---
def get_live_times(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    
    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 展示タイムのテーブルを探す
        times = []
        table = soup.select_one('table.is-w748')
        if table:
            # 各艇の展示タイムを抽出
            rows = table.select('tbody')
            for row in rows[:6]:
                # 4番目のtd（展示タイムが入っている場所）を取得
                t_val = row.select('td')[3].text.strip()
                times.append(float(t_val))
        
        if len(times) >= 4:
            return times[0], times[3], min(times) # 1号艇, 4号艇, 全艇の最速
    except:
        pass
    return None, None, None

# --- 2. 画面表示部 ---
st.set_page_config(page_title="競艇予測AI", layout="wide")
st.title("🚤 競艇予測AI (リアルタイム版)")

STADIUMS = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

# サイドバーに記録を表示（的中率修正用）
st.sidebar.header("📊 予測履歴")
st.sidebar.info("今後のアップデートでここに的中率を表示します")

st.header("会場選択")
cols = st.columns(6)
selected_jcd = st.session_state.get('jcd', None)

for i, (jcd, name) in enumerate(STADIUMS.items()):
    with cols[i % 6]:
        if st.button(f"{jcd} {name}", key=jcd, use_container_width=True):
            st.session_state.jcd = jcd
            st.rerun()

if 'jcd' in st.session_state:
    selected_jcd = st.session_state.jcd
    st.divider()
    st.subheader(f"📍 {STADIUMS[selected_jcd]} のレース選択")
    r_cols = st.columns(12)
    
    for r in range(1, 13):
        with r_cols[r-1]:
            if st.button(f"{r}R", key=f"r{r}"):
                st.session_state.rno = r

if 'rno' in st.session_state:
    rno = st.session_state.rno
    jcd = st.session_state.jcd
    st.write(f"### {rno}R の予測分析を実行中...")
    
    # 本物のデータを取得
    t1, t4, t_min = get_live_times(jcd, rno)
    
    if t1 and t4:
        diff = t1 - t4
        st.write(f"【展示タイム】 1号艇: {t1} / 4号艇: {t4} (差: {diff:.2f})")
        
        # ロジック適用
        if t4 == t_min and diff >= 0.10:
            st.error(f"⚠️ 中穴アラート！ 4号艇が最速かつ1号艇と0.10秒以上の差")
            st.subheader("推奨買い目: **4-5-1** / 4-1-5")
        else:
            st.success("✅ 本命展開: 1号艇の逃げが濃厚です")
            st.subheader("推奨買い目: **1-2-3** / 1-2-4")
    else:
        st.warning("⏳ 展示タイムがまだ公開されていないか、取得できませんでした。")

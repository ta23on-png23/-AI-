import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# --- ブラウザ偽装設定 ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# --- 1. G級レース会場の取得 ---
def get_g_races():
    url = "https://www.boatrace.jp/owpc/pc/race/index"
    g_races = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=7)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 開催場リストのセルを全探索
        stadium_cells = soup.select('td.is-arrowNone')
        for cell in stadium_cells:
            # グレードアイコン（imgのalt）をチェック
            img = cell.select_one('img')
            grade = ""
            if img:
                alt = img.get('alt', '')
                if 'SG' in alt: grade = "SG"
                elif 'G1' in alt: grade = "G1"
                elif 'G2' in alt: grade = "G2"
                elif 'G3' in alt: grade = "G3"
            
            if grade:
                link = cell.select_one('a')
                if link and 'jcd=' in link.get('href'):
                    jcd = link.get('href').split('jcd=')[1].split('&')[0]
                    name_tag = cell.select_one('div.is-jcd')
                    name = name_tag.get_text(strip=True) if name_tag else "不明"
                    g_races.append({"jcd": jcd, "name": name, "grade": grade})
    except: pass
    return g_races

# --- 2. 出走表（選手名・級別）の厳密取得 ---
def get_race_table(jcd, rno):
    date = datetime.datetime.now().strftime("%Y%m%d")
    url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    
    players = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=7)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1号艇〜6号艇のデータが入っているtbodyを特定
        # 公式サイトでは is-p_top10 というクラスが各艇のブロック
        rows = soup.select('tbody.is-p_top10')
        
        for i, row in enumerate(rows[:6]):
            # 名字の抽出 (div.is-fs18 内の a タグ)
            name_element = row.select_one('div.is-fs18 a')
            full_name = name_element.get_text(strip=True) if name_element else f"艇番{i+1}"
            last_name = full_name.replace('\u3000', ' ').split(' ')[0] # 名字のみ
            
            # 級別の抽出 (spanタグのクラス名から判定)
            rank = "不明"
            rank_tag = row.select_one('span[class*="is-rank"]')
            if rank_tag:
                rank = rank_tag.get_text(strip=True)
            
            players.append({"name": last_name, "rank": rank})
    except Exception as e:
        print(f"Error: {e}")
    return players

# --- UI部 ---
st.set_page_config(page_title="競艇出走表取得", layout="wide")
st.title("🚤 競艇出走表・リアルタイム同期")

# 1. グレードレース表示
g_list = get_g_races()
if g_list:
    st.subheader("🔥 本日のグレードレース開催会場")
    g_cols = st.columns(len(g_list))
    for i, r in enumerate(g_list):
        if g_cols[i].button(f"🏆 {r['grade']} {r['name']}", key=f"g_{r['jcd']}"):
            st.session_state.jcd = r['jcd']
            st.rerun()
st.divider()

# 2. 会場選択
STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}
st.header("会場選択")
cols = st.columns(8)
for i, (jcd, name) in enumerate(STADIUMS.items()):
    if cols[i % 8].button(name, key=f"st_{jcd}"):
        st.session_state.jcd = jcd
        st.rerun()

# 3. レース番号と出走表の表示
if 'jcd' in st.session_state:
    st.divider()
    st.subheader(f"📍 {STADIUMS[st.session_state.jcd]} レース選択")
    r_cols = st.columns(12)
    for r in range(1, 13):
        if r_cols[r-1].button(f"{r}R", key=f"r_{r}"):
            st.session_state.rno = r
            st.rerun()

    if 'rno' in st.session_state:
        st.markdown(f"### 【第 {st.session_state.rno} レース 出走表】")
        with st.spinner('公式サイトから選手データを読み込み中...'):
            players = get_race_table(st.session_state.jcd, st.session_state.rno)
        
        if players:
            # 取得したデータを表形式で表示
            cols_p = st.columns(6)
            for i, p in enumerate(players):
                with cols_p[i]:
                    st.markdown(f"""
                    <div style="border: 2px solid #ccc; padding: 10px; border-radius: 5px; text-align: center;">
                        <span style="font-size: 20px; font-weight: bold;">{i+1}号艇</span><br>
                        <span style="font-size: 24px;">{p['name']}</span><br>
                        <span style="color: #ff4b4b; font-weight: bold;">{p['rank']}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.error("選手データが取得できませんでした。時間をおいて再度お試しください。")

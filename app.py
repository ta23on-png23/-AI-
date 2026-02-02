import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import random

# ボット対策：ブラウザのふりをする設定
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

STADIUMS = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

st.set_page_config(page_title="ボートレース選手データ取得テスト", layout="wide")
st.title("🏃 選手リスト取得テスター")

# サイドバー：会場とレース選択
jcd = st.sidebar.selectbox("会場を選択", list(STADIUMS.keys()), format_func=lambda x: STADIUMS[x])
rno = st.sidebar.number_input("レース番号", 1, 12, 1)

if st.sidebar.button("選手リストを取得", use_container_width=True):
    # 公式サイトのURL（出走表ページ）
    url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}"
    
    try:
        with st.spinner('通信中...'):
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code != 200:
                st.error(f"公式サイトにアクセスできませんでした (Status: {res.status_code})")
            else:
                soup = BeautifulSoup(res.content, "html.parser")
                # 選手データが入っている枠（tbody.is-p_top10）を探す
                rows = soup.select('tbody.is-p_top10')
                
                if not rows:
                    st.warning("選手データが見つかりません。非開催日か、まだ番組が確定していない可能性があります。")
                else:
                    player_list = []
                    for i, row in enumerate(rows[:6]):
                        # 名前と級別を抽出
                        name = row.select_one('div.is-fs18 a').get_text(strip=True) if row.select_one('div.is-fs18 a') else "取得失敗"
                        rank = "不明"
                        txt = row.get_text()
                        for r in ["A1", "A2", "B1", "B2"]:
                            if r in txt:
                                rank = r
                                break
                        
                        player_list.append({
                            "枠番": i + 1,
                            "名前": name,
                            "級別": rank
                        })
                    
                    # 結果をテーブルで表示
                    st.success(f"{STADIUMS[jcd]} 第{rno}R の選手データを取得しました")
                    st.table(pd.DataFrame(player_list))
                    
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

st.info("※このアプリは予測を行いません。データの受信テスト専用です。")

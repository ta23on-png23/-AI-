import streamlit as st
import requests
from bs4 import BeautifulSoup

st.title("競艇予測AI - 開発中")

# 24場のボタン作成（テスト用）
st.subheader("会場を選択してください")
cols = st.columns(4)
stadiums = ["桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖"]

for i, stadium in enumerate(stadiums):
    with cols[i % 4]:
        if st.button(stadium):
            st.success(f"{stadium}が選択されました。データを取得します...")

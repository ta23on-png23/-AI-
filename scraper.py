# scraper.py
import requests
from bs4 import BeautifulSoup

def get_live_times(jcd, rno, date):
    """
    公式サイトから展示タイムを取得する
    """
    url = f"https://www.boatrace.jp/owpc/pc/race/before?jcd={jcd}&rno={rno}&hd={date}"
    # ここにスクレイピングコードを書く（後ほど詳細を実装）
    # 一旦、テスト用の値を返すようにします
    return 6.85, 6.74
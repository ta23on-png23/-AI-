import requests
from bs4 import BeautifulSoup

def get_race_program_test(jcd, rno, date):
    # 公式サイトの番組表URL
    url = f"https://www.boatrace.jp/owpc/pc/race/index?jcd={jcd}&rno={rno}&hd={date}"
    
    response = requests.get(url)
    response.encoding = response.apparent_encoding # 文字化け防止
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # --- 女子戦判定 ---
    race_title = soup.find('h2', class_='label2_title').text if soup.find('h2', class_='label2_title') else ""
    is_women_race = "女子" in race_title or "ヴィーナス" in race_title
    
    # --- G級判定 ---
    # クラス名に 'is-gradeG1' などが含まれているかチェック
    header_class = soup.find('div', class_='label2')['class'] if soup.find('div', class_='label2') else []
    grade = "一般"
    for c in header_class:
        if "is-gradeG1" in c: grade = "G1"
        elif "is-gradeG3" in c: grade = "G3"
        # SGやG2も同様に追加
    
    print(f"--- {race_title} ({grade}) ---")
    print(f"女子戦フラグ: {is_women_race}")

    # --- 選手データ抽出 ---
    # 艇ごとの情報を取得（1〜6号艇）
    rows = soup.select('table.is-w748 tbody')
    for i, row in enumerate(rows[:6], 1):
        # 階級（A1, A2, B1, B2）
        rank = row.select_one('span.is-rankA1, span.is-rankA2, span.is-rankB1, span.is-rankB2').text
        # 選手名
        name = row.select_one('div.is-fs18 a').text.replace('\u3000', ' ')
        
        print(f"{i}号艇: {name} [{rank}]")

# 本日の日付(YYYYMMDD)でテスト
get_race_program_test(jcd='04', rno='1', date='20260201')
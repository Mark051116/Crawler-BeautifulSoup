import requests
from bs4 import BeautifulSoup
import sqlite3

# 頁面網址
urls = [
    "https://csie.asia.edu.tw/zh_tw/associate_professors_2?page_no=1&",
    "https://csie.asia.edu.tw/zh_tw/associate_professors_2?page_no=2&"
]

def clean(text):
    return text.strip().replace('\xa0', ' ').replace('\n', '').replace('\r', '')

def extract_data_from_page(soup):
    data = []
    sections = soup.find_all('div', class_='i-member-section')
    print(f"這頁共找到 {len(sections)} 個職稱區塊。")
    
    for section in sections:
        title_tag = section.find('h3', class_='i-member-status-title')
        title = clean(title_tag.get_text()) if title_tag else "未知職稱"
        
        professor_items = section.find_all('div', class_='i-member-item')
        print(f"{title} 區塊有 {len(professor_items)} 位老師")
        
        for item in professor_items:
            name = ""
            research = ""

            # 抓姓名（兩種結構）
            name_span = item.find('span', class_='i-member-value member-data-value-name')
            if name_span:
                name = clean(name_span.get_text())
            else:
                name_tag = item.find('h3')
                if name_tag:
                    name = clean(name_tag.get_text())

            # 抓研究領域（兩種結構）
            research_span = item.find('span', class_='i-member-value member-data-value-7')
            if research_span:
                research = clean(research_span.get_text())
            else:
                research_p = item.find('p')
                research = clean(research_p.get_text()) if research_p else "尚未提供"

            if name:
                data.append({'title': title, 'name': name, 'research': research})
    
    return data

# 建立 SQLite 資料庫
conn = sqlite3.connect('professors.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS professors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        name TEXT,
        research TEXT
    )
''')
conn.commit()

# 主程式
all_professors = []

try:
    for url in urls:
        response = requests.get(url)
        response.raise_for_status()
        print(f"\n成功抓取：{url}")
        soup = BeautifulSoup(response.content, 'html.parser')
        professors = extract_data_from_page(soup)
        all_professors.extend(professors)

        # 存進 SQLite
        for prof in professors:
            cursor.execute('''
                INSERT INTO professors (title, name, research)
                VALUES (?, ?, ?)
            ''', (prof['title'], prof['name'], prof['research']))
        conn.commit()

    # 存成 .txt
    with open("professors.txt", "w", encoding="utf-8") as f:
        for prof in all_professors:
            f.write(f"職稱: {prof['title']}, 姓名: {prof['name']}, 研究領域: {prof['research']}\n")

    print(f"\n✅ 共擷取 {len(all_professors)} 位老師資料，已成功寫入 professors.txt 與 SQLite 資料庫")

except Exception as e:
    print("❌ 發生錯誤：", e)

finally:
    conn.close()

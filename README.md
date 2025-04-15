# Crawler-BeautifulSoup

這個專案是一個使用 Python 和 BeautifulSoup 撰寫的網頁爬蟲，目的是自動擷取亞洲大學資訊工程學系（CSIE）網站上的教師資料。爬蟲會抓取每位老師的職稱、姓名和研究領域，並將資料儲存成兩個格式：文字檔 (professors.txt) 和 SQLite 資料庫 (professors.db)。

# 使用技術
1.Python 3.x

2.BeautifulSoup：用來解析 HTML 內容

3.requests：用來發送 HTTP 請求抓取網頁

4.sqlite3：用來將資料儲存進 SQLite 資料庫

# 程式碼如何運作
這段程式碼的目的是從指定的兩個網頁中抓取教授資料，並將資料儲存到 professors.txt 檔案以及 professors.db SQLite 資料庫中。程式分為幾個主要的步驟：初始化、資料抓取、資料解析、資料儲存和錯誤處理。

## 1. 導入必要的庫
程式開始時，我們導入了以下三個庫：

requests：用來發送 HTTP 請求，從網頁獲取內容。

beautifulsoup4：用來解析網頁的 HTML，抽取出所需的資料。

sqlite3：用來將抓取到的資料儲存到 SQLite 資料庫。

```python
import requests

from bs4 import BeautifulSoup

import sqlite3
```

## 2. 定義清理函式 (clean)
這個函式會清理抓取到的資料，去除多餘的空白字元、換行符號等，保證資料乾淨並準備好進行儲存。

```python
def clean(text):
    
    return text.strip().replace('\xa0', ' ').replace('\n', '').replace('\r', '')
```

## 3. 定義資料擷取函式 (extract_data_from_page)
這個函式負責處理每一頁的 HTML，從中提取教師資料。它會處理每個職稱區塊（如系主任、教授等），並抓取每位老師的姓名和研究領域。

sections：通過 find_all 找到所有職稱區塊，這些區塊包含教師資料。

title_tag：從每個區塊中抓取職稱（如：系主任、教授等）。

professor_items：從每個區塊中抓取所有的老師項目（每位老師的信息）。

在每個老師項目中，我們會檢查是否能夠抓取到姓名和研究領域，有兩種結構需要處理，因此會分別處理不同的標籤來抓取資料。如果資料中沒有提供研究領域，則會填寫為「尚未提供」。

```python
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
```

## 4. 建立資料庫 (SQLite)
在這部分，程式建立了一個 SQLite 資料庫來儲存抓取到的資料。如果資料庫或表格不存在，程式會創建它們。

```python
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
```

## 5. 抓取資料並儲存到資料庫與文字檔
主程式會遍歷指定的網頁，對每一頁進行抓取。每抓取一頁資料，程式會：

呼叫 extract_data_from_page 函式來解析網頁內容，擷取教師資料。

把每位教師的資料儲存到 SQLite 資料庫中。

將抓取到的資料儲存到 professors.txt 檔案中。

```python
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
```

## 6. 錯誤處理
在爬蟲運行過程中，若發生任何錯誤（如網頁無法訪問，或資料儲存過程出錯），程式會捕捉到錯誤並顯示錯誤訊息。

```python
except Exception as e:
    print("❌ 發生錯誤：", e)

finally:
    conn.close()
```

## 7. 程式執行流程簡述
程式首先透過 requests 下載兩個網頁的內容。

接著利用 BeautifulSoup 解析網頁的 HTML 結構，抓取每位教授的姓名、職稱和研究領域。

資料會儲存到 professors.db 的 SQLite 資料庫中，並且也會儲存到 professors.txt 文字檔中。

最後，程式顯示抓取結果，並顯示擷取的教師數量。

# 遇到的困難與解決方式
## 1.部分老師缺少研究領域資訊
有些老師的網頁資料中並未提供研究領域。為避免漏掉這些老師，我修改程式邏輯，讓即使沒有研究資料也會保留該筆資料，並以「尚未提供」標註。

## 2.老師分類顯示異常
第一頁所有老師的職稱都被解析成「系主任」。經嘗試後發現 BeautifulSoup 難以區分各老師所屬職稱區塊，可能是因為 HTML 結構不夠明確。因此，這部分無法完全準確分類，但已盡量保留原本抓取到的職稱標題。

## 3.不同職稱的 HTML 結構不一致
有些資料使用 h3、有些則使用 span，研究領域也分別出現在 span 或 p 中。因此程式中必須針對兩種不同結構進行條件判斷與資料清理。

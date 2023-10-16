import os
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

def process_html(content):
    hot_news_title = []
    hot_news_url = []
    hot_news_hotness = []

    soup = BeautifulSoup(content, 'lxml')
    urls_titles = soup.select('#pl_top_realtimehot > table > tbody > tr > td.td-02 > a')
    hotness = soup.select('#pl_top_realtimehot > table > tbody > tr > td.td-02 > span')

    for i in range(len(urls_titles)-1):
        hot_news_title.append(urls_titles[i + 1].get_text())
        hot_news_url.append("https://s.weibo.com"+urls_titles[i]['href'])
        hot_news_hotness.append(hotness[i].get_text())
    
    local_time = datetime.utcnow()
    beijing_time = local_time + timedelta(hours=8)
    year = beijing_time.strftime('%Y')
    month_day = beijing_time.strftime('%m%d')
    minute = beijing_time.hour * 60 + beijing_time.minute
    path = '../../News/CN/' + year + '/' + month_day + '/'

    if not os.path.exists(path):
        os.makedirs(path)

    df = pd.DataFrame(
        {
            '排名': range(1, len(hot_news_title) + 1),
            '标题': hot_news_title,
            '链接': hot_news_url,
            '热点': hot_news_hotness,
        }
    )
    df.to_csv(path + '微博热搜榜.' + str(minute) + '.csv', index=False)
    df.to_html(path + '微博热搜榜.' + str(minute) + '.html', index=False)

chrome_driver_path = 'lib/chromedriver.exe'

chrome_driver = webdriver.Chrome()

url = 'https://s.weibo.com/top/summary?cate=realtimehot'

chrome_driver.set_window_size(1920, 1080)

chrome_driver.get(url)

chrome_driver.implicitly_wait(8.0)

try:
    element = WebDriverWait(chrome_driver, 15).until(
        EC.presence_of_element_located((By.ID, "searchapps"))
    )
    process_html(chrome_driver.page_source)
finally:
    chrome_driver.close()
    chrome_driver.quit()

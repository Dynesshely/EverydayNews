import os
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

def is_valid_href(href):
    """判断 href 是否为可用的站内/站外链接。

    微博热搜里的置顶/广告行 href 是 javascript:void(0);，历史版本把它
    直接拼成了 "https://s.weibo.comjavascript:void(0);" 这种垃圾链接，
    这里统一视为无链接。
    """
    if not href:
        return False
    href = href.strip()
    if not href or href.lower().startswith("javascript:"):
        return False
    if href in ("#", "/", "void(0)", "void(0);"):
        return False
    return True

def build_url(href):
    """把站内相对 href 拼成完整链接；无效 href 返回空字符串。"""
    if not is_valid_href(href):
        return ""
    href = href.strip()
    if href.lower().startswith(("http://", "https://")):
        return href
    return "https://s.weibo.com" + href

def parse_rank(row):
    """读取该行的排名；「置顶」等非榜单行返回 None（与历史数据保持一致，不收录）。"""
    cell = row.select_one('td.td-01')
    if cell is None:
        return None
    text = cell.get_text().strip()
    return int(text) if text.isdigit() else None

def process_html(content):
    hot_news_title = []
    hot_news_url = []
    hot_news_hotness = []

    soup = BeautifulSoup(content, 'lxml')
    # 逐 <tr> 解析，标题 / 链接 / 热度都取自同一行，杜绝任何索引错位。
    # 历史版本的 process_html() 存在 off-by-one：标题取 urls_titles[i + 1]，
    # 而链接取 urls_titles[i]，导致每条记录的链接都指向上一行的标题。
    rows = soup.select('#pl_top_realtimehot > table > tbody > tr')

    for row in rows:
        rank = parse_rank(row)
        if rank is None:
            continue
        link = row.select_one('td.td-02 > a')
        if link is None:
            continue
        title = link.get_text().strip()
        if not title:
            continue
        url = build_url(link.get('href', ''))
        span = row.select_one('td.td-02 > span')
        hotness = span.get_text().strip() if span is not None else ''

        hot_news_title.append(title)
        hot_news_url.append(url)
        hot_news_hotness.append(hotness)

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

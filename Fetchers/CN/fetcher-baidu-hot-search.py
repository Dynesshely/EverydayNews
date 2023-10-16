import requests
import os
import pandas as pd
from datetime import datetime, timedelta

url = 'https://top.baidu.com/api/board?platform=wise&tab=realtime'

header = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Mobile Safari/537.36',
    'Host': 'top.baidu.com',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://top.baidu.com/board?tab=novel',
}

r = requests.get(url, header)

json_data = r.json()

top_content_list = json_data['data']['cards'][0]['topContent']
content_list = json_data['data']['cards'][0]['content']
title_list = []
order_list = []
score_list = []
descr_list = []
url_list = []
img_list = []

for i in range(0, len(top_content_list)):
    title_list.append(top_content_list[i]['word'])
    order_list.append(top_content_list[i]['index'])
    score_list.append(top_content_list[i]['hotScore'])
    descr_list.append(top_content_list[i]['desc'])
    url_list.append(top_content_list[i]['url'])
    img_list.append(top_content_list[i]['img'])

for i in range(0, len(content_list)):
    title_list.append(content_list[i]['word'])
    order_list.append(content_list[i]['index'] + len(top_content_list))
    score_list.append(content_list[i]['hotScore'])
    descr_list.append(content_list[i]['desc'])
    url_list.append(content_list[i]['url'])
    img_list.append(content_list[i]['img'])

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
        '热搜排名': order_list,
        '热搜标题': title_list,
        '描述': descr_list,
        '热搜指数': score_list,
        '链接地址': url_list,
        '封图链接': img_list
    }
)
df.to_csv(path + '百度热搜榜.' + str(minute) + '.csv', index=False)
df.to_html(path + '百度热搜榜.' + str(minute) + '.html', index=False)

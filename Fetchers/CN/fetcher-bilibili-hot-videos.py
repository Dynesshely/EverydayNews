import requests
import os
import csv
import json
import time
from datetime import datetime, timedelta

url = 'https://www.bilibili.com'

headers = {
    'Cookie': '{}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
    'Referer': 'https://www.bilibili.com/v/fashion/makeup/?spm_id_from=333.5.b_7375626e6176.2',
    'sec-fetch-dest': 'script',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'same-site'
}

local_time = datetime.utcnow()
beijing_time = local_time + timedelta(hours=8)
year = beijing_time.strftime('%Y')
month_day = beijing_time.strftime('%m%d')
minute = beijing_time.hour * 60 + beijing_time.minute
path = '../../News/CN/' + year + '/' + month_day + '/'
csvfile = path + 'BiliBili 热门视频.' + str(minute) + '.csv'

if not os.path.exists(path):
    os.makedirs(path)

def get_parse(result):
    D = []
    items = result['data']['list']
    for item in items:
        id = item['aid']
        title = item['title']
        tname = item['tname']
        uid = item['owner']['mid']
        uname = item['owner']['name']
        pic = item['pic']
        times = item['pubdate']
        timearray2 = time.localtime(times)
        time2 = time.strftime('%Y-%m-%d', timearray2)
        view = item['stat']['view']
        danmaku = item['stat']['danmaku']
        like = item['stat']['like']
        coin = item['stat']['coin']
        favorite = item['stat']['favorite']
        share = item['stat']['share']
        reply = item['stat']['reply']
        time3 = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        data = [id, uid, uname, title, tname, pic, time2, view, danmaku, like, coin, favorite, share, reply, time3]
        print(data)
        D.append(data)
    save(D)

def save(data):
    with open(csvfile, 'a', newline='', encoding='utf-8') as file:
        write=csv.writer(file)
        write.writerows(data)

def main():
    li = ['视频 ID', '用户 ID', '用户昵称', '标题', '归属类别', '图片', '发布时间', '观看人数', '弹幕数', '点赞数', '投币数', '收藏数', '分享数', '评论数', '当前时间']
    
    with open(csvfile, 'a', newline='', encoding='utf-8') as file:
        write = csv.writer(file)
        write.writerow(li)
        
    for i in range(1,11):
        url = 'https://api.bilibili.com/x/web-interface/popular?ps=20&pn={}'.format(i)
        print(url)
        response=requests.get(url,headers=headers).text
        result=json.loads(response)
        get_parse(result)

if __name__ == '__main__':
    main()

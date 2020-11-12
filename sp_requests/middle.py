'''
将所有功能整合起来
'''
from spider import *
from orm import *
from settings import *
import time
from urllib.parse import quote
from concurrent.futures.thread import ThreadPoolExecutor
from sp_queue import *
import requests
from requests.utils import dict_from_cookiejar

all_thread = []
#在某个进程完成时删除对应的key_word
def pop_key_word(key_word,future):
    _queue_action = QueueAction(**configs)
    _queue_action.pop_key_word(key_word.encode())
    _queue_action.qclose()

#用于获取baiduuid
def get_baiduuid():
    url = 'https://www.baidu.com/'
    h = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'
    }
    res = requests.get(url,headers=h)
    cookies = dict_from_cookiejar(res.cookies)
    return ('BAIDUID=' + cookies['BAIDUID'] + ';')

def save_data():
    global global_list
    global end_flag
    sql = Orm()
    while True:
        global_list_bak = global_list.copy()
        # if global_list_bak != []:
        #     print(global_list_bak)
        for data in global_list_bak:
            sql.insert_data(MYSQL_TABLE,data)
            global_list.remove(data)

        holder = [t.running() for t in all_thread]
        thread_over_status = list(map(lambda x:int(x),holder))
        if end_flag['status'] == 1 and global_list == [] and (1 not in thread_over_status):
            print('over sql')
            sql.sclose()
            break

#纪录线程池错误日志
def error_log(future):
    if future.exception():
        print(future.exception())

def fetch_all(key_word,use_redis=False):
    global global_request_url
    global global_uncomplete_url
    global headers
    global end_flag
    global all_thread
    global bd_uid
    #获取10个baiduuid，数量无所谓，尽量超过10个，也可以选择事先存储在redis里
    for _ in range(10):
        bd_uid.append(get_baiduuid())
        time.sleep(0.1)
    #创建线程池
    pool = ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS)
    pool1 = ThreadPoolExecutor(max_workers=1)
    #直接死循环开启sql检测数据状态
    pool1.submit(save_data)
    bd_request = BdRequests()
    bd_s = BdSp(key_word)
    queue_a = QueueAction(**configs)
    redis_cursor = queue_a.redis_cursor
    #起点url
    base = 'https://www.baidu.com/s?wd=' + quote(key_word)
    global_request_url.append(base)
    while True:
        global_url_bak = global_request_url.copy()
        global_uncomplete_url_bak = global_uncomplete_url.copy()
        #有未完成的，加入请求列表
        for uncomplete in global_uncomplete_url_bak:
            global_url_bak.insert(0,uncomplete)
            global_uncomplete_url.remove(uncomplete)

        for url in global_url_bak:
            #提交请求到线程池
            if not use_redis:
                if base == url:
                    c = pool.submit(bd_request.make_request, url, bd_s.parse_next_page, headers, dont_filter=True)
                    c.add_done_callback(error_log)
                    all_thread.append(c)
                else:
                    c = pool.submit(bd_request.make_request, url, bd_s.parse_detail, headers)
                    #获取下一页这里每次开启都要获取，否则会死循环
                    d = pool.submit(bd_request.make_request, url, bd_s.parse_next_page, headers,dont_filter=True)
                    c.add_done_callback(error_log)
                    d.add_done_callback(error_log)
                    all_thread.append(c)
                    all_thread.append(d)
            else:
                if base == url:
                    c = pool.submit(bd_request.make_request, url, bd_s.parse_next_page, headers, dont_filter=True,redis_cursor=redis_cursor)
                    c.add_done_callback(error_log)
                    all_thread.append(c)
                else:
                    c = pool.submit(bd_request.make_request, url, bd_s.parse_detail, headers,redis_cursor=redis_cursor)
                    d = pool.submit(bd_request.make_request, url, bd_s.parse_next_page, headers,redis_cursor=redis_cursor,dont_filter=True)
                    c.add_done_callback(error_log)
                    d.add_done_callback(error_log)
                    all_thread.append(c)
                    all_thread.append(d)
            try:
                #每次请求完毕删除请求列表
                #会出错是由于uncomplete的缘故，无需处理
                global_request_url.remove(url)
            except:
                pass
            time.sleep(DOWNLOAD_DELAY)
        # if global_url_bak != []:
        #     print(global_url_bak)
        #     print('=' * 100)
        # print([t.running() for t in all_thread])
        holder = [t.running() for t in all_thread]
        thread_over_status = list(map(lambda x:int(x),holder))
        if end_flag['status'] == 1 and global_url_bak == [] and (1 not in thread_over_status):
            print('over main')
            if use_redis:
                queue_a.qclose()
            break


if __name__ == '__main__':
    fetch_all('北京')
















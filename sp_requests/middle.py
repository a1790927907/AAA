import orm
import sp_queue
import spider
from settings import *
import threading
import time

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cookie': 'BAIDUID=8C34F3725437FDB859AA39E5FDFFD164:FG=1;',
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
}
#由于需要返回值，所以重写Thread
class MyThread(threading.Thread):
    def __init__(self,func,args=(),kwargs={}):
        super(MyThread,self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def run(self):
        self.result = self.func(*self.args,**self.kwargs)
    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

def save_data_to_sql(data_generator):
    #每次需要创建新的连接，解决互斥锁的问题
    sql = orm.SaveData(MYSQL_USERNAME, MYSQL_PWD, MYSQL_DATABASE)
    for data in data_generator:
        print(data)
        #sleep一段时间解决数据库无法长时间alive问题以及其他问题
        time.sleep(0.2)
        sql.save_data(data,'bd')

def run_spider(key_word):
    num = 0
    b = spider.Baidu(key_word)
    thread_dict = {}
    next_page = b.start_url
    page_flag = 0
    r = spider.Request()
    queue_action = sp_queue.QueueAction(**configs)
    redis_cursor = queue_action.redis_cursor
    cookie_flag = 0
    #请求部分全部写在这里
    while True:
        #创建多个线程访问
        #num用于判定是否是start_url
        if num == 0:
            thread_dict['tp' + str(num)] = MyThread(func=r.make_requests, args=(next_page, b.parse, headers,True),kwargs={'redis_cursor': redis_cursor})
            thread_dict['pp' + str(num)] = MyThread(func=r.make_requests, args=(next_page, b.parse_page_url, headers, True),kwargs={'redis_cursor': redis_cursor})
            thread_dict['tp' + str(num)].start()
            time.sleep(DOWNLOAD_DELAY)
            thread_dict['pp' + str(num)].start()

        elif num != 0:
            if cookie_flag:
                thread_dict['tp' + str(num)] = MyThread(func=r.make_requests, args=(next_page, b.parse, headers,True),kwargs={'redis_cursor': redis_cursor})
                cookie_flag = 0
            else:
                thread_dict['tp' + str(num)] = MyThread(func=r.make_requests, args=(next_page, b.parse, headers),kwargs={'redis_cursor': redis_cursor})
            thread_dict['pp' + str(num)] = MyThread(func=r.make_requests,args=(next_page, b.parse_page_url, headers,True),kwargs={'redis_cursor': redis_cursor})
            thread_dict['tp' + str(num)].start()
            time.sleep(DOWNLOAD_DELAY)
            thread_dict['pp' + str(num)].start()

        #由于线程的同时执行问题，next_page返回的速度跟不上执行的速度
        #这里需要等next_page取到值
        #这里应该不要等待，但是如果没有next_page就无法开始下一次的请求，所以这里就会耗时(待解决)
        while True:
            #具体见spider.py
            if (thread_dict['pp' + str(num)].get_result() is not None) and (thread_dict['pp' + str(num)].get_result() != 'no next') and (not isinstance(thread_dict['pp' + str(num)].get_result(),dict)):
                next_page = thread_dict.pop('pp' + str(num))
                next_page = next_page.get_result()
                num += 1
                break

            #跳过百度搜索的验证码检测
            elif isinstance(thread_dict['pp' + str(num)].get_result(),dict):
                bdcookie = thread_dict['pp' + str(num)].get_result()
                if bdcookie.get('BAIDUID'):
                    headers['Cookie'] = f"BAIDUID={bdcookie.get('BAIDUID')};"
                    #避免未处理的url被去重
                    cookie_flag = 1
                    break
                else:
                    print('log cookie:')
                    print(bdcookie.get('BAIDUID'))
                    page_flag = 1
                    break

            if thread_dict['pp' + str(num)].get_result() == 'no next':
                thread_dict.pop('pp' + str(num))
                #说明到了最后一页
                page_flag = 1
                break

        #采取一次性处理指定量数据的方式
        #数据量在settings里面设置
        if (len(thread_dict) > DATA_MANAGE_NUM) or page_flag == 1:
            #由于pop操作，所以需要一份新的thread_dict
            thread_dict_copy = thread_dict.copy()
            for key in thread_dict_copy:
                #采用了同请求过滤的模式
                if ('tp' in key) and (thread_dict[key].get_result() is not None) and (thread_dict[key].get_result() != 'exists'):
                    generator_result = thread_dict.pop(key)
                    generator_result = generator_result.get_result()
                    t = threading.Thread(target=save_data_to_sql, args=(generator_result,))
                    t.start()
                elif thread_dict[key].get_result() == 'exists':
                    thread_dict.pop(key)
        if page_flag == 1:
            print(page_flag)
            break
        time.sleep(DOWNLOAD_DELAY)















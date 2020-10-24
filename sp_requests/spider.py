import requests
from lxml import etree
from datetime import datetime
import re
from requests.utils import dict_from_cookiejar
from hashlib import md5
import pickle
from urllib.parse import quote

#用于发起请求的类
class Request(object):
    dupe_set = set()
    def make_requests(self,url,callback,headers,dont_filter=False,method='get',**kwargs):
        '''
        :param url: 请求的url地址
        :param callback: 回调函数
        :param headers: 请求头
        :param dont_filter: 是否过滤
        :param method: 请求方法
        :param kwargs: extra参数,可以加入redis_cursor参数以及body请求体(需要配合method='post')
        :return: item generator
        '''
        if method == 'get':
            if not dont_filter:
                #尝试获取redis
                #采用dupefilter进行过滤
                #使用md5加密
                if kwargs.get('redis_cursor',''):
                    body = kwargs.get('body','')
                    #extra：指纹加入了callback回调函数
                    s = pickle.dumps([method,body,url,callback])
                    dupefilter = md5(s).hexdigest()
                    pipe = kwargs['redis_cursor'].pipeline()
                    add_result = pipe.sadd('dupefilter',dupefilter)
                    pipe.execute()
                    kwargs['redis_cursor'].save()
                    pipe.close()

                    #没有重复的话add_result返回1
                    if add_result:
                        res = requests.get(url, headers=headers)
                        return callback(res.text)
                    else:
                        #存在返回exists
                        return 'exists'

                #无redis_cursor参数，则使用类属性
                #由于set在内存中，无法持久化
                else:
                    dupe_copy = self.dupe_set.copy()
                    body = kwargs.get('body', '')
                    s = pickle.dumps([method,body,url,callback])
                    dupefilter = md5(s).hexdigest()
                    self.dupe_set.add(dupefilter)
                    if len(self.dupe_set.difference(dupe_copy)) != 0:
                        res = requests.get(url, headers=headers)
                        return callback(res.text)
                    else:
                        return 'exists'

            #dont_filter设置为True，则不用验证指纹
            else:
                res = requests.get(url, headers=headers)
                return callback(res.text)

class Baidu(object):
    def __init__(self,key_word):
        self.key_word = key_word
        self.start_url = 'https://www.baidu.com/s?wd=' + quote(key_word)

    #获取翻页的url
    def parse_page_url(self,response):
        selector_xpath = etree.HTML(response)
        next_page_url_list = selector_xpath.xpath('//div[@class="page-inner"]/a[contains(text(),"下一页")]/@href')
        if next_page_url_list != []:
            next_page_url = 'https://www.baidu.com' + next_page_url_list[0]
            return next_page_url
        else:
            #请求过多或者过快会出现旋转验证码
            #更新一次cookies即可跳过旋转验证码
            if selector_xpath.xpath('//div[@id="page"]') == []:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
                }
                res = requests.get('https://www.baidu.com/', headers=headers)
                cookies = dict_from_cookiejar(res.cookies)
                return cookies
            else:
                #最后一页返回no next
                return 'no next'

    #每页的数据处理
    def parse(self,response):
        selector_xpath = etree.HTML(response)
        all_data = selector_xpath.xpath('//div[@id="content_left"]/div/h3/a[1]')
        for data in all_data:
            item = {}
            item['key_word'] = self.key_word
            item['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            title_list = data.xpath('.//text()')
            item['title'] = ''.join(
                [re.sub(r'\n|\t|\r| ', '', i) for i in title_list if re.sub(r'\n|\t|\r| ', '', i)])
            yield item


if __name__ == '__main__':
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
    }
    b = Baidu('上海')
    r = Request()
    gen1 = r.make_requests('https://www.baidu.com/s?wd=%E4%B8%8A%E6%B5%B7',b.parse,headers=headers)
    gen2 = r.make_requests('https://www.baidu.com/s?wd=%E4%B8%8A%E6%B5%B7',b.parse,headers=headers)
    print(gen1)
    print(gen2)
    for i in gen1:
        print(i)
    # for j in gen2:
    #     print(j)













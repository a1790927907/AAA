from hashlib import md5
import pickle
from lxml import etree
import re
from datetime import datetime
import requests
from requests.utils import dict_from_cookiejar
from settings import BASE_URL
from urllib.parse import urljoin
import json
import time
global_list = []
global_request_url = []
global_uncomplete_url = set()
global_page_list = set()
end_flag = {'status':0}
flag = {'stop':0}
bd_uid = []

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cookie': 'BAIDUID=08EEBA636D73FDF1BC86E7710C0F701B:FG=1;',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'
}
class BdRequests(object):
    dupe = set()
    def make_request(self,url,callback,headers,method='get',dont_filter=False,**kwargs):
        '''
        用于发起请求
        :param url: url地址
        :param callback: 回调函数
        :param headers: 请求头
        :param method: 请求方法
        :param dont_filter: 是否过滤
        :param kwargs: 可以加入cookies参数以及redis_cursor参数(如果有可以加入)
        :return:
        '''
        if method == 'get':
            if not dont_filter:
                if 'redis_cursor' in kwargs:
                    redis_cursor = kwargs['redis_cursor']
                    pipe = redis_cursor.pipeline()
                    all_secret = pickle.dumps([method,url,b'',callback])
                    md5_enc_secret = md5(all_secret).hexdigest()
                    pipe.sadd('dupefilter',md5_enc_secret)
                    add_result = pipe.execute()
                    redis_cursor.save()
                    pipe.close()
                    #去除重复的请求
                    if add_result == [0]:
                        return None
                    else:
                        if 'cookies' in kwargs:
                            res = requests.get(url,headers=headers,cookies=kwargs['cookies'])
                            text = res.text
                        else:
                            res = requests.get(url,headers=headers)
                            text = res.text
                        callback(text,{'redis_cursor':kwargs['redis_cursor'],'s':md5_enc_secret,'url':url})
                else:
                    all_secret = pickle.dumps([method,url,b'',callback])
                    md5_enc_secret = md5(all_secret).hexdigest()
                    dupe_bak = self.dupe.copy()
                    self.dupe.add(md5_enc_secret)
                    if len(dupe_bak) == len(self.dupe):
                        return None
                    else:
                        if 'cookies' in kwargs:
                            res = requests.get(url, headers=headers, cookies=kwargs['cookies'])
                            text = res.text
                        else:
                            res = requests.get(url, headers=headers)
                            text = res.text
                        callback(text,{'dupe':self.dupe,'s':md5_enc_secret,'url':url})
            else:
                if kwargs.get('cookies',''):
                    res = requests.get(url,headers=headers,cookies=kwargs['cookies'])
                    text = res.text
                else:
                    res = requests.get(url, headers=headers)
                    text = res.text
                callback(text,{'url':url})

class BdSp(object):
    def __init__(self,key_word):
        self.key_word = key_word

    def parse_detail(self,text,meta):
        global end_flag
        global headers
        global global_list
        global bd_uid
        selector = etree.HTML(text)
        #一旦出现图片验证码需要更换cookie来跳过
        if selector.xpath('//div[@id="page"]') == []:
            #由于百度服务端的更新速度，这里直接访问百度首页获取cookie会出现问题
            #一般2-3s之后生成的BAIDUUID才可用
            #这里直接采用生成完毕的，可以事先访问指定数量次百度主页获取一定数量的cookie
            headers['Cookie'] = bd_uid[0]
            #由于多线程原因可能会出现浪费的现象
            bd_uid.pop(0)
            print(headers['Cookie'])
            #需要删除对应的dupefilter
            #当前请求不算
            if meta.get('redis_cursor',''):
                pipe = meta['redis_cursor'].pipeline()
                pipe.srem('dupefilter',meta['s'])
                meta['redis_cursor'].save()
                pipe.close()
            elif meta.get('dupe',''):
                meta['dupe'].remove(meta['s'])
            #存储失败的请求，之后再来
            global_uncomplete_url.add(meta['url'])
            return
        all_e = selector.xpath('//div[@id="content_left"]/div[@tpl!="recommend_list"]')
        for e in all_e:
            item = {}
            item['key_word'] = self.key_word
            title = e.xpath('./h3/a//text()')
            title = [re.sub(r'\t|\n|\r| ','',t) for t in title if re.sub(r'\t|\r|\n| ','',t)]
            item['title'] = ''.join(title)
            item['url'] = e.xpath('./h3/a/@href')[0]
            item['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            img_url = e.xpath('./div/div/a/img/@src')
            item['img_url'] = json.dumps(img_url)
            global_list.append(item)
        print(meta['url'])
        print('='*100)
        if selector.xpath('//div[@id="page"]/div/a[contains(text(),"下一页")]') == []:
            end_flag['status'] = 1


    def parse_next_page(self,text,meta):
        global global_page_list
        global headers
        global global_request_url

        #以下同理
        #与上分开是由于速度以及避免url去重后出现死循环问题
        selector = etree.HTML(text)
        if selector.xpath('//div[@id="page"]') == []:
            headers['Cookie'] = bd_uid[0]
            bd_uid.pop(0)
            print(headers['Cookie'])
            if meta.get('redis_cursor',''):
                pipe = meta['redis_cursor'].pipeline()
                pipe.srem('dupefilter',meta['s'])
                meta['redis_cursor'].save()
                pipe.close()
            elif meta.get('dupe',''):
                meta['dupe'].remove(meta['s'])
            global_uncomplete_url.add(meta['url'])
            return
        all_page = selector.xpath('//div[@id="page"]/div/a')
        for page in all_page:
            #获取当前页面所有的页面url
            next_page_url = urljoin(BASE_URL,page.xpath('./@href')[0])
            #截取url
            #每页url参数均不相同，截取相同部分
            next_page_url = re.findall(r'(.*?pn=.*?)&',next_page_url)[0]
            add_previous_len = len(global_page_list)
            global_page_list.add(next_page_url)
            #如果重复则不加入
            if len(global_page_list) != add_previous_len:
                global_request_url.append(next_page_url)



if __name__ == '__main__':
    b = BdRequests()
    bd = BdSp('上海')
    from concurrent.futures.thread import ThreadPoolExecutor
    from urllib.parse import quote
    pool = ThreadPoolExecutor(max_workers=4)
    pool.submit(b.make_request,('https://www.baidu.com/s?wd=' + quote('上海')),bd.parse_detail,headers)
    pool.submit(b.make_request,('https://www.baidu.com/s?wd=' + quote('上海')),bd.parse_next_page,headers)
    import time
    time.sleep(3)
    print(global_page_list)
    print(global_request_url)
    print(global_list)




















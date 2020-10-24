from settings import *
import redis

class QueueAction(object):
    def __init__(self,**kwargs):
        self.redis_cursor = redis.StrictRedis(**kwargs)

    #写入消息队列
    def save_key_words(self,key_words):
        pipe = self.redis_cursor.pipeline()
        for word in key_words:
            pipe.rpush('keywords',word)
            pipe.execute()
        pipe.close()
        self.redis_cursor.save()

    #获取所有的key_words
    def get_key_words(self):
        key_words = self.redis_cursor.lrange('keywords',0,-1)
        return key_words

    #删除指定key_word
    def pop_key_word(self,key_word):
        self.redis_cursor.lrem('keywords',1,key_word)
        self.redis_cursor.save()

    def qclose(self):
        self.redis_cursor.close()

if __name__ == '__main__':
    #在这里操作消息队列
    #可以使用文件一次性写入
    #关键词之间逗号隔开
    #可以在爬取过程中持续插入关键词
    #file_path在settings中设置
    if file_path:
        with open(file_path, 'r') as f:
            key_words = f.read().replace('\n', '').replace('\r', '')
            if key_words:
                all_key_words = key_words.split(',')
            else:
                all_key_words = []
        #清空文件内容
        with open(file_path,'w') as f1:
            f1.write('')
            f1.flush()
    else:
        key_words = input('输入关键字(英文逗号隔开):')
        if key_words:
            all_key_words = key_words.split(',')
        else:
            all_key_words = []
    if all_key_words != []:
        q = QueueAction(**configs)
        q.save_key_words(all_key_words)







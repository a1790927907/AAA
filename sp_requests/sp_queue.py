import redis
from settings import configs

class QueueAction(object):
    def __init__(self,**kwargs):
        self.redis_cursor = redis.StrictRedis(**kwargs)

    def save_key_words(self,key_words):
        pipe = self.redis_cursor.pipeline()
        for k in key_words:
            pipe.rpush('keywords',k)
            pipe.execute()
        self.redis_cursor.save()
        pipe.close()

    def get_and_pop_one_key_word(self):
        key_word = self.redis_cursor.lindex('keywords',0)
        pipe = self.redis_cursor.pipeline()
        pipe.lrem('keywords',1,key_word)
        pipe.execute()
        pipe.close()
        return key_word.decode()

    def get_all_key_words(self):
        key_words = self.redis_cursor.lrange('keywords',0,-1)
        key_words = map(lambda x:x.decode(),key_words)
        return list(key_words)

    def pop_key_word(self,key_word):
        pipe = self.redis_cursor.pipeline()
        pipe.lrem('keywords',1,key_word)
        pipe.execute()
        self.redis_cursor.save()

    def qclose(self):
        self.redis_cursor.close()

if __name__ == '__main__':
    queue_action = QueueAction(**configs)
    redis_curs = queue_action.redis_cursor

    # with open('file.txt','r',encoding='utf-8') as f:
    #     key_words = f.read()
    # key_words = key_words.split(',')
    # queue_action.save_key_words(key_words)
    # import time
    # time.sleep(2)
    # print(queue_action.get_all_key_words())










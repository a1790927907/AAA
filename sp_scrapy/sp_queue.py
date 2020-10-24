import redis
from snyg.settings import config
class QueueAction(object):
    def __init__(self,**kwargs):
        self.redis_cursor = redis.StrictRedis(**kwargs)

    def save_key_words(self,key_words):
        pipe = self.redis_cursor.pipeline()
        for word in key_words:
            pipe.rpush('keywords:suning',word)
            pipe.execute()
        pipe.close()
        self.redis_cursor.save()

    def pop_key_word(self,key_word):
        pipe = self.redis_cursor.pipeline()
        pipe.lrem('keywords:suning',1,key_word)
        pipe.execute()
        pipe.close()
        self.redis_cursor.save()


    def get_key_words(self):
        all_key_words = self.redis_cursor.lrange('keywords:suning',0,-1)
        return all_key_words

    #000000011731822396-0070069904-1-total?originalCmmdtyType=style
    def get_and_pop_one_keyword(self):
        key_word = self.redis_cursor.lindex('keywords:suning',0)
        pipe = self.redis_cursor.pipeline()
        pipe.lrem('keywords:suning',1,key_word)
        pipe.execute()
        self.redis_cursor.save()
        return key_word

    def qclose(self):
        self.redis_cursor.close()



if __name__ == '__main__':
    key_words = input('输入关键词:')
    all_key_words = key_words.split(',')
    q = QueueAction(**config)
    q.save_key_words(all_key_words)













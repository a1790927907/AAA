'''
###主入口
 - 只有当所有进程结束后才会结束，一个关键词创建一个新的进程，可以在中途加入新的字段
 - 新字段的加入根据settings.py里面的最大进程数来决定什么时候运行
 - 如果没有设置最大进程数，字段加入后会立刻执行
 - 想要加入字段调用sp_queue.py
'''
from middle import *
from multiprocessing import Process
import time
from orm import SaveData
from settings import *
import pymysql
if __name__ == '__main__':
    try:
        with open('file.txt','r') as f:
            c = f.read()
            c = c.split(',')
        with open('file.txt','w') as f1:
            f1.write('')
            f1.flush()
    except:
        pass
    #在一开始就创建数据库
    mysql1 = pymysql.connect('mysql','root','0365241lk')
    cursor1 = mysql1.cursor()
    sqlcmd = f'create database if not exists {MYSQL_DATABASE};'
    cursor1.execute(sqlcmd)
    mysql1.commit()
    while True:
        try:
            #不断连接直到连接成功
            sql = SaveData(MYSQL_USERNAME,MYSQL_PWD,MYSQL_DATABASE)
            sql.create_database('bd')
            break
        except:
            continue
    queue_action = sp_queue.QueueAction(**configs)
    try:
        queue_action.save_key_words(c)
    except:
        pass
    redis_cursor = queue_action.redis_cursor
    process_list = []
    finish_flag = 0
    try:
        max_process = MAX_PROCESS_NUM
    except:
        max_process = None
    while True:
        key_words_in_redis = queue_action.get_key_words()
        if max_process:
            if len(process_list) < max_process:
                key_w = key_words_in_redis[:(max_process-len(process_list))]
                for word in key_w:
                    print(word.decode())
                    process = Process(target=run_spider, args=(word.decode(),))
                    process.start()
                    process_list.append(process)
                    queue_action.pop_key_word(word)

        else:
            for word in key_words_in_redis:
                print(word.decode())
                process = Process(target=run_spider, args=(word.decode(),))
                process.start()
                process_list.append(process)
                queue_action.pop_key_word(word)

        for p in process_list:
            if not p.is_alive():
                process_list.remove(p)

        if finish_flag:
            break

        if process_list == []:
            finish_flag = 1

        time.sleep(5)
    redis_cursor.close()








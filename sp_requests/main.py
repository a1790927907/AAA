from sp_queue import *
from concurrent.futures.process import ProcessPoolExecutor
from middle import *
import time
from functools import partial
import pymysql

if __name__ == '__main__':
    #配合docker，这里停5s
    time.sleep(5)
    while True:
        try:
            sql = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, port=MYSQL_PORT)
            break
        except:
            continue
    cursor = sql.cursor()
    sqlcmd = f'create database if not exists {MYSQL_DB};'
    sqlcmd1 = f'alter database {MYSQL_DB} character set utf8mb4 collate utf8mb4_unicode_ci;'
    cursor.execute(sqlcmd)
    cursor.execute(sqlcmd1)
    sql.commit()
    cursor.close()
    sql.close()
    new_sql = Orm()
    new_sql.create_table(MYSQL_TABLE)
    new_sql.sclose()

    queue_action = QueueAction(**configs)
    pool = ProcessPoolExecutor(max_workers=MAX_PROCESS)
    with open('file.txt','r',encoding='utf-8') as f:
        key_words = f.read()
    key_words = key_words.split(',')
    queue_action.save_key_words(key_words)
    redis_cursor = queue_action.redis_cursor
    time.sleep(0.2)
    all_process = []
    all_key_words = queue_action.get_all_key_words()
    all_key_words_bak = all_key_words.copy()
    while True:
        bak = all_key_words.copy()
        for key_word in bak:
            a = pool.submit(fetch_all,key_word,use_redis=True)
            a.add_done_callback(partial(pop_key_word,key_word))
            all_process.append(a)
            all_key_words.remove(key_word)

        new_get_key_words = queue_action.get_all_key_words()
        for j in all_key_words_bak:
            try:
                new_get_key_words.remove(j)
            except:
                pass
        if new_get_key_words != []:
            for l in new_get_key_words:
                all_key_words.append(l)
                all_key_words_bak.append(l)
            continue
        process_status = [i.running() for i in all_process]
        st = list(map(lambda x:int(x),process_status))
        if (1 not in st):
            break













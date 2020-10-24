from scrapy import cmdline
from multiprocessing import Process
from snyg.settings import MAX_PROCESS,config
from sp_queue import QueueAction
import time
def st():
    cmdline.execute('scrapy crawl snygsp'.split())

if __name__ == '__main__':
    process_list = []
    queue_action = QueueAction(**config)
    all_key_words = queue_action.get_key_words()
    if all_key_words != []:
        while True:
            while len(process_list) < MAX_PROCESS:
                all_key_words = queue_action.get_key_words()
                if all_key_words == []:
                    break
                process = Process(target=st)
                process.start()
                process_list.append(process)
                #scrapy开启较慢,redis速度过快，这里需要等待一会
                time.sleep(4)

            for p in process_list:
                if not p.is_alive():
                    process_list.remove(p)

            if process_list == [] and queue_action.get_key_words() == []:
                break

            time.sleep(3)

    queue_action.qclose()










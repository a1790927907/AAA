import pymysql
from datetime import datetime
#数据库操作
class SaveData(object):
    def __init__(self,username,password,dbname,host='localhost'):
        self.host = host
        self.uername = username
        self.password = password
        self.dbname = dbname
        self.mysql = pymysql.connect(self.host,self.uername,self.password,self.dbname)
        self.cursor = self.mysql.cursor()

    #字典形式传入data
    #确保mysql里有对应的表
    def save_data(self,data,tbname):
        all_keys = [all_key_v[0] for all_key_v in data.items()]
        keys_str = ','.join(all_keys)
        values_list = []
        for k,val in data.items():
            if isinstance(val,str):
                values_list.append(f'"{val}"')
            elif isinstance(val,bool):
                values_list.append(str(int(val)))
            else:
                values_list.append(f'{val}')
        values_str = ','.join(values_list)
        sqlcmd = f'insert into {tbname}({keys_str}) values({values_str})'
        try:
            #缓解Lost connection to MySQL server问题
            #具体解决在middle.py
            self.mysql.ping(reconnect=True)
            self.cursor.execute(sqlcmd)
            self.mysql.commit()
        except:
            self.mysql.rollback()


    def sclose(self):
        self.cursor.close()
        self.mysql.close()

if __name__ == '__main__':
    s = SaveData('root','0365241lk','baidu')
    s.save_data({'key_word': '上海', 'time': '2020-10-23 23:36:11', 'title': '上海-品牌项目信息'},'bd')














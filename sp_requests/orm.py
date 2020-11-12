import pymysql
from settings import *

class Orm(object):
    def __init__(self):
        self.mysql = pymysql.connect(host=MYSQL_HOST,user=MYSQL_USER,passwd=MYSQL_PASSWORD,port=MYSQL_PORT,db=MYSQL_DB)
        self.cursor = self.mysql.cursor()

    def create_table(self,tbname):
        sqlcmd = f'create table if not exists {tbname}(id int auto_increment primary key,key_word varchar(150) not null,title varchar(150) not null,url text not null,time datetime not null,img_url text);'
        self.cursor.execute(sqlcmd)
        self.mysql.commit()

    def insert_data(self,tbname,data):
        l_bak = ['id'] + [i for i in data.keys()]
        v_bak = tuple([i for i in data.values()])
        s_bak = tuple(['0'] + ['%s'] * len(v_bak))
        sql_l_bak = ','.join(l_bak)
        sql_s_bak = ','.join(s_bak)
        sqlcmd = f'insert into {tbname}({sql_l_bak}) values({sql_s_bak});'
        params = [v_bak]
        self.cursor.executemany(sqlcmd,params)
        self.mysql.commit()

    def sclose(self):
        self.mysql.close()
        self.cursor.close()

if __name__ == '__main__':
    orm = Orm()
    orm.create_table('bd')
    orm.insert_data('bd',{'key_word': '上海', 'title': '上海市人民政府', 'url': 'http://www.baidu.com/link?url=SIu0vCMmUjFjbcxcsfbVXkJhqg-tfZhtTUMda-ScnO1sCBTH9pMczD4_KNIVWl-B', 'time': '2020-11-07 06:15:36', 'img_url': '["https://dss1.bdstatic.com/6OF1bjeh1BF3odCf/it/u=2423316306,4063082714&fm=85&app=81&f=JPEG?w=121&h=75&s=8180FE168CA0FE1313DC2DFE0300D033"]'})

















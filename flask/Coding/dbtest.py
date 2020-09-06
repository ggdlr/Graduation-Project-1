import pymysql
import paramiko
db  = pymysql.connect(host='192.168.0.96', user='root', passwd='', db='user_info', charset='utf8')
cursor = db.cursor()

flist=[]
i=0
sql1 = '''
            INSERT INTO user_code(user_id) VALUES('test') 
     '''
cursor.execute(sql1)
db.commit()
db.close()

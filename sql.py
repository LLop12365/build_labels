import pymysql
import datetime
import pytz
from typing import List
from utils import MYSQL_LINE, MYSQL_ACCOUNT, MYSQL_PWD, MYSQL_POST, MYSQL_DATABASE

def mysql_connect():
    """
    连接数据库

    Output: 
        cnx: 连接
        cursor: 游标
    """
    cnx = pymysql.connect(
        host=MYSQL_LINE, 
        port=MYSQL_POST,
        user=MYSQL_ACCOUNT, 
        passwd=MYSQL_PWD,
        database=MYSQL_DATABASE)
    cursor = cnx.cursor()

    return cnx, cursor

def meterial_list(cursor) -> List[dict]:
    """
    连接数据库，并且输出当前小时上一个小时的素材id，素材标题，素材链接，创建时间

    Args:
        cursor: 游标
    
    Output:
        dict_res: 素材id对应的情况
    """
    now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    format_time = (now - datetime.timedelta(hours=0)).strftime("%Y%m%d%H")

    query = """select id, title, path, create_time 
                from material 
                where DATE_FORMAT(FROM_UNIXTIME(create_time), '%Y%m%d%H')='{}'
                order by create_time DESC
            """.format(format_time)
    cursor.execute(query)

    columns_name = [col[0] for col in cursor.description]
    res = cursor.fetchall()

    dict_res = [dict(zip(columns_name, row)) for row in res]
        
    return dict_res

def meterial_list2(cursor, dt1, dt2) -> List[dict]:
    """
    连接数据库，并且输出当前小时上一个小时的素材id，素材标题，素材链接，创建时间

    Args:
        cursor: 游标
        dt1: 前置时间 %Y%m%d%H%M
        dt2: 当前时间 %Y%m%d%H%M
    
    Output:
        dict_res: 素材id对应的情况
    """
    query = """select id, title, path, create_time
                from material 
                where DATE_FORMAT(FROM_UNIXTIME(create_time), '%Y%m%d%H%i') between '{}' and '{}'
            """.format(dt1, dt2)
    cursor.execute(query)

    columns_name = [col[0] for col in cursor.description]
    res = cursor.fetchall()

    dict_res = [dict(zip(columns_name, row)) for row in res]
        
    return dict_res

def write_table(connection, cursor, label_list: List[dict]) -> int:
    """
    将结果写入table中

    Args:
        connection: 连接
        cursor: 游标
        label_list: 结果字典
    
    Output:
        写入mysql的条数
    """
    data = []
    now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    for material in label_list:
        for label in label_list[material]:
            data.append((2, int(material), label, '罗朗', now, now))
    query = """insert into material_label (company, material_id, content, create_user, create_time, update_time)
                values (%s, %s, %s, %s, %s, %s)"""
    cursor.executemany(query, data)

    connection.commit()

    return len(data)

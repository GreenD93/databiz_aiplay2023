import pymysql
from config.settings import *

pymysql.install_as_MySQLdb()
def get_db_connection(
        host=SQL_HOST,
        port=SQL_PORT,
        user=SQL_USERNAME,
        passwd=SQL_PASSWD,
        db=SQL_SCHEMA_NAME,
        charset=SQL_CHARSET
):

    db = pymysql.connect(
        host=host,
        port=port,
        user=user,
        passwd=passwd,
        db=db,
        charset=charset
    )

    return db
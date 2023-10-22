from src.db_utils import *

def verify_account(id, pwd):

    db = get_db_connection(host=SQL_HOST, user=SQL_USERNAME, passwd=SQL_PASSWD, db=SQL_SCHEMA_NAME)

    user_info = {
        'id' : None,
        'pwd' : None,
        'name' : None,
        'geng' : None,
        'ageg' : None,
        'jobseg' : None
    }

    try:
        with db.cursor() as curs:
            curs.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')
            db.commit()


            sql = f"""
                  SELECT id, pwd, name, geng, ageg, jobseg
                  FROM user_profile
                  WHERE id = '{id}' and pwd = '{pwd}'
            """

            print(sql)

            curs.execute(sql)
            rows = curs.fetchall()
            row = rows[0]

            user_info['id'] = row[0]
            user_info['pwd'] = row[1]
            user_info['name'] = row[2]
            user_info['geng'] = row[3]
            user_info['ageg'] =  row[4]
            user_info['jobseg'] =  row[5]

        return user_info, True

    except:
        return user_info, False


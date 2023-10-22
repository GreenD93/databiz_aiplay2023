import openai
import re

from src.db_utils import *
from src.prompt import *
from config.settings import *

openai.api_key = OPENAI_KEY
class MKTPhraseGenerator:
    def __init__(self):

        self.prompt = PROMPT_DICT["MKT_PHRASE_PRMPT"]

        self.basic_prod_dic = {
            'aptloan': "아파트 담보대출",
            'codek_freeaccount': "자유적금",
            'coin_info': "가상자산(비트코인) 시세정보",
            'hiteenpromotion': "중/고등학생 체크카드",
            'homelearn_event': "초등학생 학습지",
            'togetheraccount': "모임통장"
        }

        self.error_template = {
            'aptloan': {'text1': '큰 돈 새는 주담대 이자 이제는 이자도 절약해요 부자 솔루션', 'text2': '- 절약 비교해보면 케뱅 아파트담보대출'},
            'codek_freeaccount': {'text1': '단순하고 쉬운게 좋다면? ', 'text2': '코드K 자유적금이 딱이에요 복잡한 우대조건 필요 없어요'},
            'coin_info': {'text1': '비트코인 시세 조회 어디서 하세요?', 'text2': '여기서도 간편하게 조회가 가능해요!'},
            'hiteenpromotion': {'text1': '우리 아이 버스•지하철 교통비 500원씩 싸게 타는 방법이 있어요', 'text2': 'Hi teen 자세히 알아보기'},
            'homelearn_event': {'text1': '우리 아이 성적에 고민이 많으신 부모님들!', 'text2': '전교 1등 노하우 알려드릴게요!'},
            'togetheraccount': {'text1': '같이 모으는 돈에도', 'text2': '최고 연 10%(세전) 이자 받기'}
        }
        pass

    def generate_mkt_phrase(self, prod_nm, name, prompt):

        response = self._generate_chat_completion(prompt)

        print(response)

        try:
            text1, text2 = self.preprocess_response(response, name)
        except:
            # error handle
            error_handle_texts = self.error_template[prod_nm]
            text1, text2 = error_handle_texts['text1'], error_handle_texts['text2']

        return text1, text2

    def preprocess_response(self, response, name):
        def _preprocess_pipeline(response):

            pipe_cnt = response.split('|')

            if len(pipe_cnt) == 2:
                text1, text2 = response.split("|")
                return text1, text2

            else:
                texts = response.split('|')
                text1 = texts[0]
                text2 = " ".join(texts[1:])
                return text1, text2

        def _preprocess_text(text, name):
            # regex
            text = re.sub('[0-9]위.', '', text)
            text = re.sub('[0-9]위', '', text)

            # replace
            text = text.replace('결과:', '')
            text = text.replace('"', '')
            text = text.replace('\n', '')
            text = text.replace('{CUST_FULL_NM}', name)
            text = text.replace('(CUST_FULL_NM)', name)
            text = text.replace('[CUST_FULL_NM]', name)
            text = text.replace('{고객}', name)
            text = text.replace('(고객)', name)
            text = text.replace('[고객]', name)
            text = text.replace('고객', name)
            text = text.replace('(첫 번째 문장)', "")
            text = text.replace('(두 번째 문장)', "")
            text = text.strip()

            return text

        text1, text2 = _preprocess_pipeline(response)
        text1 = _preprocess_text(text1, name)
        text2 = _preprocess_text(text2, name)

        text1 = text1.strip()
        text2 = text2.strip()

        return text1, text2
    def _generate_chat_completion(self, prompt):

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response = response["choices"][0]["message"]["content"]

        return response

    def _get_basic_prod(self, prod_nm):
        return self.basic_prod_dic[prod_nm]

    def generate_prompt(self, prod_nm, geng, ageg, jobseg):

        basic_prod_nm = self._get_basic_prod(prod_nm)
        prod_infos, _ = self._search_prod_infos(prod_nm)

        prod_info = prod_infos['prod_info']
        prod_promotion_info = prod_infos['prod_promotion_info']
        prod_ir = prod_infos['prod_ir']

        best_mkt_phrases, _ = self._search_best_mkt_phrases(prod_nm, geng, ageg, jobseg)

        prompt = self.prompt.format(
            basic_prod_nm=basic_prod_nm,
            best_mkt_phrases=best_mkt_phrases,
            prod_info=prod_info,
            prod_promotion_info=prod_promotion_info,
            prod_ir=prod_ir,
            ageg=ageg,
            geng=geng,
            jobseg=jobseg
        )

        return prompt

    def _search_prod_infos(self, prod_nm):
        """
            Input:
                prod_nm: str ex) 'aptloan'
            Return:
                best_mkt_phrases: dict
        """
        db = get_db_connection(host=SQL_HOST, user=SQL_USERNAME, passwd=SQL_PASSWD, db=SQL_SCHEMA_NAME)
        try:
            with db.cursor() as curs:
                curs.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')
                db.commit()

                sql = f"""
                    SELECT prod_nm, prod_info, prod_promotion_info, prod_ir
                    FROM prd_info
                    WHERE
                        prod_nm = '{prod_nm}'
                """

                print(sql)

                curs.execute(sql)
                rows = curs.fetchall()
                row = rows[0]

                prod_nm = row[0]
                prod_info = row[1].replace('\\n','\n')
                prod_promotion_info = row[2].replace('\\n','\n')
                prod_ir = row[3].replace('\\n','\n')

                prod_infos = {
                    'prod_nm' : prod_nm,
                    'prod_info': prod_info,
                    'prod_promotion_info': prod_promotion_info,
                    'prod_ir': prod_ir
                }

            return prod_infos, True

        except:

            prod_infos = {
                'prod_nm' : '',
                'prod_info': '',
                'prod_promotion_info': '',
                'prod_ir': ''
            }
            return prod_infos, False


    def _search_best_mkt_phrases(self, prod_nm, geng, ageg, jobseg):
        """
            Input:
                prod_nm: str ex) 'aptloan'
                gegng: str ex) '여성'
                ageg: str ex) '20대'
                jpbseg str ex) '전문직'
            Return:
                best_mkt_phrases: str
        """
        db = get_db_connection(host=SQL_HOST, user=SQL_USERNAME, passwd=SQL_PASSWD, db=SQL_SCHEMA_NAME)
        try:
            with db.cursor() as curs:
                curs.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')
                db.commit()

                sql = f"""
                    SELECT mkt_phrase
                    FROM mkt_phrase
                    WHERE 
                        prod_nm = '{prod_nm}'
                        and geng = '{geng}'
                        and ageg = '{ageg}'
                        and jobseg = '{jobseg}'
                    ORDER BY ctr desc
                    LIMIT 5;
                """

                print(sql)

                curs.execute(sql)
                rows = curs.fetchall()

                best_mkt_phrases = ""
                for idx, row in enumerate(rows):
                    mkt_phrase = row[0]
                    best_mkt_phrases += f"{idx + 1}위. {mkt_phrase}\n"

            return best_mkt_phrases, True

        except:
            best_mkt_phrases = ""
            return best_mkt_phrases, False


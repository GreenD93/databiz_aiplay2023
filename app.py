from flask import Flask, render_template, jsonify, make_response, session, request
from flask_cors import CORS

from src.mkt_phrase_generator import MKTPhraseGenerator
from src.verify_account import *
from config.settings import *

# ----------------
# init
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

mkt_phrase_generator = MKTPhraseGenerator()
apriori_df = pd.read_csv('data/apriori.csv')
# ----------------

app.secret_key = 'any random string'

@app.route("/", methods = ['GET', 'POST'])
def index():

    if not session.get('name', 0):
        return render_template('login.html')

    elif request.method == 'POST':
        try:
            last_click_prod = session['last_click_prod']

            name = session["name"]
            geng = session["geng"]
            ageg = session["ageg"]
            jobseg = session["jobseg"]
            profile_url = session["profile_url"]

            # apriori rule
            condition = f"""
                prod_nm == '{last_click_prod}' & geng == '{geng}' & ageg == '{ageg}' & jobseg == '{jobseg}'
            """
            prod_nm = apriori_df.query(condition)['post_prod_nm'].values[0]

            # generate prompt
            prompt = mkt_phrase_generator.generate_prompt(prod_nm, geng, ageg, jobseg)

            print(prompt)

            # get openai response
            text1, text2 = mkt_phrase_generator.generate_mkt_phrase(prod_nm, name, prompt)

            print(text1)
            print(text2)

            # bnnr_url 변경
            bnnr_url = f"../static/img/bnnr_imgs/{prod_nm}.png"

            # 있다면 apriori rule로 찾아서 보여주기
            return render_template('index.html',
                                       name=name,
                                       ageg=ageg,
                                       geng=geng,
                                       jobseg=jobseg,
                                       profile_url=profile_url,
                                       prod=prod_nm,
                                       bnnr_url=bnnr_url,
                                       title=text1,
                                       sub_text=text2
                                   )

        except:

            name = session["name"]
            geng = session["geng"]
            ageg = session["ageg"]
            jobseg = session["jobseg"]
            profile_url = session["profile_url"]
            prod_nm = DEFAULT_PROD_NM
            title = DEFAULT_TITLE
            sub_text = DEFAULT_TEXT
            bnnr_url = f"../static/img/bnnr_imgs/{prod_nm}.png"

            return render_template('index.html',
                                       name=name,
                                       ageg=ageg,
                                       geng=geng,
                                       jobseg=jobseg,
                                       profile_url=profile_url,
                                       prod=prod_nm,
                                       bnnr_url=bnnr_url,
                                       title=title,
                                       sub_text=sub_text
                                   )


    elif request.method == 'GET':

        name, geng, ageg, jobseg = session['name'], session['geng'], session['ageg'], session['jobseg']
        user_df = MASS_DF[(MASS_DF['geng'] == geng) & (MASS_DF['ageg'] == ageg) & (MASS_DF['jobseg'] == jobseg)]

        prod_nm = user_df['contentname'].values[0]
        title = user_df['title'].values[0]
        sub_text = user_df['sub_text'].values[0]
        bnnr_url = f"../static/img/bnnr_imgs/{prod_nm}.png"

        return render_template('index.html',
                                   name=session['name'],
                                   ageg=session['ageg'],
                                   geng=session['geng'],
                                   jobseg=session['jobseg'],
                                   profile_url=session['profile_url'],
                                   prod=prod_nm,
                                   bnnr_url=bnnr_url,
                                   title=title,
                                   sub_text=sub_text
                               )


# 로그인 페이지 출력
@app.route('/login', methods = ['GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html',
                               retry=False
                               )
    else:
        return json.dumps({'returnCode': 'NG', 'message': 'Method ' + request.method + ' not allowed.'}), 405


@app.route('/prod', methods = ['POST'])
def prod():
    # global last_click_prod

    if request.method == 'POST':

        response = request.get_json()

        click_prod = response['prod']
        session['last_click_prod'] = click_prod

        res = make_response(
            jsonify(
                {
                    'prod': '123',
                    'url' : f'/prod_page/prod={click_prod}'
                }
            )
        )
        return res
@app.route('/prod_page/<prod>')
def prod_page(prod):
    prod_url = f"../static/img/cropped_imgs/{prod}.jpeg"
    prod_url = prod_url.replace("prod=","")
    return render_template("prod_page.html",
                           prod_url=prod_url)

@app.route('/verify', methods = ['GET'])
def verify():

    id = request.args.get('username')
    pwd = request.args.get('password')

    id = id.lower()
    user_info, access = verify_account(id, pwd)

    print(user_info, access)

    if access:
        # mass 상품 찾기
        # default 문구

        name, geng, ageg, jobseg = user_info['name'], user_info['geng'], user_info['ageg'], user_info['jobseg']
        user_df = MASS_DF[(MASS_DF['geng'] == geng) & (MASS_DF['ageg'] == ageg) & (MASS_DF['jobseg'] == jobseg)]

        prod_nm = user_df['contentname'].values[0]
        title = user_df['title'].values[0]
        sub_text = user_df['sub_text'].values[0]

        title = title.replace('{CUST_FULL_NM}',name)
        sub_text = sub_text.replace('{CUST_FULL_NM}', name)
        bnnr_url = f"../static/img/bnnr_imgs/{prod_nm}.png"

        session['name'] = name
        session['ageg'] = ageg
        session['geng'] = geng
        session['jobseg'] = jobseg

        if session['geng'] == '남성':
            profile_url = "../static/img/undraw_profile.svg"
        else:
            profile_url = "../static/img/undraw_profile_3.svg"

        session['profile_url'] = profile_url

        return render_template('index.html',
                               name=session['name'],
                               ageg=session['ageg'],
                               geng=session['geng'],
                               jobseg=session['jobseg'],
                               profile_url=session['profile_url'],
                               prod=prod_nm,
                               bnnr_url=bnnr_url,
                               title=title,
                               sub_text=sub_text
                               )

    else:
        return render_template('login.html',
                               retry=True)


# 로그아웃
@app.route('/logout', methods = ['POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return render_template('login.html',
                               retry=False
                               )


# 오픈소스 고지문
# 사외망 오픈 서비스는 오픈소스 고지문 필수로 포함해야 함
@app.route('/opensource', methods = ['GET'])
def opensource():
    if request.method == 'GET':
        return render_template('opensource-notice.html')
    else:
        return json.dumps({'returnCode': 'NG', 'message': 'Method ' + request.method + ' not allowed.'}), 405


# Flask 서버 실행
if __name__ == '__main__':
    #app.run(host='0.0.0.0', debug=True)
    app.run(host='0.0.0.0',port=5001,debug=True)

# インポートするライブラリ
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, MessageTemplateAction, URITemplateAction
)

import os

import psycopg2

import re

# 軽量なウェブアプリケーションフレームワーク:Flask
app = Flask(__name__)


#環境変数からLINE Access Tokenを設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
#環境変数からLINE Channel Secretを設定
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# DBコネクション取得関数
def get_connection():
    host="ec2-107-21-255-181.compute-1.amazonaws.com"
    port=5432
    dbname="dduecrd1p23pgq"
    user="grcmdjajgfsjex"
    password="e9ace79c30017efd493887b9d8d9ed1ac0e3bc0eeca060cfed0271b99be2c9d7"
    conText = "host={} port={} dbname={} user={} password={}"
    conText = conText.format(host,port,dbname,user,password)
    return psycopg2.connect(conText)

# usr_id の値をチェックする
def is_exist_usr(target):
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = "SELECT usr_id FROM usr_data2 WHERE usr_id ='{}'"
            sql = sql.format(target)
            cur.execute(sql)
                
            if len(cur.fetchall()):
                return True
            else:
                return False

# 返事取得関数
def get_response_message(mes_from,usr_id):

    # flagの取得
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = "SELECT flag FROM usr_data2 WHERE usr_id = '{}'"
            sql = sql.format(usr_id)
            cur.execute(sql)
            (flag_num,) = cur.fetchone()

    # "寝る"が入力された時
    if mes_from == "寝る" or mes_from == "ねる":
        mes="明日何時に起きる？(入力例:8:00,14:30)"

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data2 SET flag = 1 WHERE usr_id = '{}'"
                sql = sql.format(usr_id)
                cur.execute(sql)
                conn.commit()
                
        return mes
            
    # "時間"が入力された時
    if ":" in mes_from and flag_num == 1:

        regex = re.compile('\d+')
        tar_time = time(0,0)
        tar_time = regex.findall(mes_from)

        mes= tar_time + "に設定したよ！"

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data2 SET flag = 2 WHERE usr_id = '{}'"
                sql = sql.format(usr_id)
                cur.execute(sql)
                conn.commit()
        
        return mes
    
                
    # それ以外
    mes = "もう一度入力してみて"
    return mes


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# MessageEvent
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # flag
    flag=0
    
    #regist profile into DB
    profile=line_bot_api.get_profile(event.source.user_id)
    usr_name = profile.display_name
    usr_id=profile.user_id
    picture=profile.picture_url
    
    if not is_exist_usr(usr_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "INSERT INTO usr_data2 (usr_id,usr_name,picture,flag) VALUES ('{}','{}','{}',{})"
                sql = sql.format(usr_id,usr_name,picture,flag)
                cur.execute(sql)
                conn.commit()
    
    #get reply from recv messege
    response_message=get_response_message(event.message.text,usr_id)
    
    #send reply messeges    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_message)
    )
    
if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
    

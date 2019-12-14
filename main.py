# インポートするライブラリ
from flask import Flask, request, abort
import psycopg2

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
                sql = 'SELECT usr_id FROM user_data WHERE usr_id ="' + target + '"'
                cur = conn.execute(sql)
                
    if len(cur.fetchall()):
        return True
    else:
        return False

# 返事取得関数
def get_response_message(mes_from):

    # "寝る"が入力された時
    if mes_from == "寝る" or mes_from == "ねる":
        mes="明日何時に起きる？(例:8時,14時30分)"
        
        return mes
            
    # "時間"が入力された時
    if "時" in mes_from:
        mes=mes_from + "に設定したよ！"
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
    name = profile.display_name
    usr_id=profile.user_id
    picture=profile.picture_url

    if not is_exist_usr(usr_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "insert into user_data(usr_id,name,picture,flag) values({},{},{},{});"
                sql = sql.format(usr_id,name,picture,flag)
                cur.execute(sql)
                conn.commit()
                
    #get reply from recv messege
    responce_message=get_response_message(event.message.text)
    if responce_message in "設定":
        regex = re.compile('\d+')
        match = [0,0]
        match = regex.findall(mes_from)
        
    #send reply messeges    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=responce_message)
    )
    
if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
    

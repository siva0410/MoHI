# インポートするライブラリ
#from flask import Flask, request, abort
from flask import Flask, request, from flask import Flask, request, abort
import json
import base64

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, MessageTemplateAction, URITemplateAction, ThingsEvent, ScenarioResult,
)

import os

import psycopg2

import time
from datetime import datetime

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
            sql = "SELECT usr_id FROM usr_data5 WHERE usr_id ='{}'"
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
            sql = "SELECT flag FROM usr_data5 WHERE usr_id = '{}'"
            sql = sql.format(usr_id)
            cur.execute(sql)
            (flag_num,) = cur.fetchone()

    # "寝る"が入力された時
    if mes_from == "寝る" or mes_from == "ねる":
        mes="明日何時に起きる？(入力例:8:00,14:30)"

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data5 SET flag = 1 WHERE usr_id = '{}'"
                sql = sql.format(usr_id)
                cur.execute(sql)
                conn.commit()
                
        return mes
            
    # "時間"が入力された時
    if ":" in mes_from and flag_num == 1:
        mes_from = "2000/1/1 " + mes_from
        tar_time = datetime.datetime.strptime(mes_from,'%Y/%m/%d %H:%M')
        mes = "{}時{}分に設定したよ！"
        mes = mes.format(tar_time.hour,tar_time.minute)

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data5 SET flag = 2 WHERE usr_id = '{}'"
                sql = sql.format(usr_id)
                cur.execute(sql)
                conn.commit()

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data5 SET target_time = '{}' WHERE usr_id = '{}'"
                time = "{}:{}:{}"
                time = time.format(tar_time.hour,tar_time.minute,tar_time.second)
                sql = sql.format(time,usr_id)
                cur.execute(sql)
                conn.commit()
        
        return mes

    # "おはよう"が入力された時
    if "おはよ" in mes_from and flag_num == 2:
        hel_time = datetime.fromtimestamp(event.timestamp/1000.0)
        mes = "おはようございます！\n 現在の時刻は{}時{}分{}秒です！"
        mes = mes.format(hel_time.hour,hel_time.minute,hel_time.second)

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data5 SET flag = 3 WHERE usr_id = '{}'"
                sql = sql.format(usr_id)
                cur.execute(sql)
                conn.commit()

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data5 SET hello_time = '{}' WHERE usr_id = '{}'"
                time = "{}:{}:{}"
                time = time.format(hel_time.hour,hel_time.minute,hel_time.second)
                sql = sql.format(time,usr_id)
                cur.execute(sql)
                conn.commit()
        
        return mes

    # "リセット"が入力された時
    if mes_from == "リセット":
        mes="リセットしました！"

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data5 SET flag = 0 WHERE usr_id = '{}'"
                sql = sql.format(usr_id)
                cur.execute(sql)
                conn.commit()

        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = "UPDATE usr_data5 SET target_time = '' WHERE usr_id = '{}'"
                sql = sql.format(time,usr_id)
                cur.execute(sql)
                conn.commit()
        return mes
                
    # それ以外
    mes = "もう一度入力してみて\n 候補:「ねる」「リセット」"
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
                sql = "INSERT INTO usr_data5 (usr_id,usr_name,picture,flag) VALUES ('{}','{}','{}',{})"
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

@handler.add(ThingsEvent)
def handle_things_event(event):
    if event.things.type != "scenarioResult":
        return
    if event.things.result.result_code != "success":
        app.logger.warn("Error result: %s", event)
        return

    button_state = int.from_bytes(base64.b64decode(event.things.result.ble_notification_payload), 'little')
    if button_state > 0:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Button is pressed!"))

    
if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
    

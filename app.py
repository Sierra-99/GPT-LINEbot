from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from dotenv import load_dotenv
from collections import deque
import logging
import sqlite3

# .envファイルを読み込む
if os.path.exists('.env'):
    load_dotenv()

# LINEの認証情報を取得する
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

# LINE Bot APIの設定
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI APIの認証情報を取得する
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# OpenAI APIの設定
openai.api_key = OPENAI_API_KEY

# エラー処理
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

file_handler = logging.FileHandler("error.log")
file_handler.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# データベース接続の設定
conn = sqlite3.connect("chat_history.db")
c = conn.cursor()

# テーブル作成
c.execute('''CREATE TABLE IF NOT EXISTS chat_history
    (user_id text, message text, timestamp text)''')
conn.commit()

# ユーザーの名前を取得する関数
def get_user_name(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except LineBotApiError as e:
        logger.error(f"LineBotApiError: {e}")
        return "user"

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    # LINEからのWebhookイベントを処理する
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(200)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # LINEからのテキストメッセージを処理する
    user_message = event.message.text
    
    # ユーザーのIDを取得する
    user_id = event.source.user_id
    
    # ユーザー名がまだ取得されていない場合は、取得する
    user_name = get_user_name(user_id)
    
    # トーク履歴をデータベースに保存
    c.execute("INSERT INTO chat_history VALUES (?, ?, ?)", (user_id, user_message, str(event.timestamp)))
    conn.commit()
    
    # 過去のトーク履歴を取得
    c.execute("SELECT message FROM chat_history WHERE user_id=? ORDER BY timestamp DESC LIMIT 5", (user_id,))
    history = c.fetchall()
    
    # 過去のトーク履歴から文字列を生成
    history_str = ", ".join([h[0] for h in history])
    
    # 返答を生成
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Your name is <AI's NAME>."},
                
                {"role": "system", "content": "You are the <AI's ROLE>."},
                
                {"role": "system", "content": "You are talking with {}.".format(user_name)},
                
                {"role": "system", "content": "Chat history is {}.".format(history_str)},
                
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )
        bot_response = response.choices[0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Error: {e}")
        bot_response = "Oops, something went wrong. Please try again later."
    
    # LINEに応答を返信
    try:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=bot_response)
        )
    except LineBotApiError as e:
        logger.error(f"Failed to reply to the user: {e}")

if __name__ == '__main__':
    # SSL証明書のパス
    context = ('/etc/letsencrypt/live/example.com/fullchain.pem', '/etc/letsencrypt/live/example.com/privkey.pem')
    
    # アクセス元IP制限無し。
    app.run(debug=False, host='0.0.0.0', port=5000, ssl_context=context)

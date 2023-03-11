from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from dotenv import load_dotenv
from collections import deque
import logging

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

# ユーザーの名前を取得する関数
def get_user_name(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except LineBotApiError as e:
        logger.error(f"LineBotApiError: {e}")
        return "user"

# グローバル変数にユーザー名を格納
user_names = {}

# ユーザーごとのトーク履歴を記憶
user_history = {}

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
    if user_id not in user_names:
        user_names[user_id] = get_user_name(user_id)
    user_name = user_names[user_id]
    
    # ユーザーの履歴を取得
    history = user_history.setdefault(user_id, deque(maxlen=5))
    
    # トーク履歴に追加する
    history.append(user_message)
    
    # トーク履歴を代入
    history_length = len(history)
    if history_length >= 5:
        str1, str2, str3, str4, str5 = [str(history[i]) for i in range(history_length - 5, history_length)]
    else:
        str_list = [str(history[i]) for i in range(history_length)] + [""] * (5 - history_length)
        str1, str2, str3, str4, str5 = str_list[0], str_list[1], str_list[2], str_list[3], str_list[4]
    
    # 返答を生成
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Your name is <AI's NAME>."},
                
                {"role": "system", "content": "You are the <AI's ROLE>."},
                
                {"role": "system", "content": "You are talking with {}.".format(user_name)},
                
                {"role": "system", "content": "Chat history is {}, {}, {}, {}, {}.".format(str1, str2, str3, str4, str5)},
                {"role": "system", "content": "Read the chat history from str1 to str5 and reply to the user with a response in the context of the conversation."},
                
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
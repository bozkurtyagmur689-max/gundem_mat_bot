import os
import uuid
import sqlite3
import threading
import hashlib
import base64
import requests
from flask import Flask, request
import telebot

# GUNCEL KONFIGURASYON BILGILERI
TELEGRAM_BOT_TOKEN = "8789026893:AAHbPlzbRbUMJoDuGcmUG3DdxwsjpC3cS3c"
X_CLIENT_ID = "Q1I1ZzlwaVcyQWREY1B5d2hHc1M6MTpjaQ"
X_CLIENT_SECRET = "cq1qQqxu69Wa0apOUhgsLsVSlPQ84UT_dbl2rZIz7Zw5USDli4"
REDIRECT_URI = "https://x-telegram-bot-servis.onrender.com/callback"
SCOPES = "tweet.read tweet.write users.read offline.access"

oauth_sessions = {}
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def init_db():
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        access_token TEXT,
        refresh_token TEXT
    )
    ''')
    conn.commit()
    conn.close()

def save_tokens(telegram_id, access_token, refresh_token):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO users (telegram_id, access_token, refresh_token)
    VALUES (?, ?, ?)
    ''', (telegram_id, access_token, refresh_token))
    conn.commit()
    conn.close()

def get_user_token(telegram_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute('SELECT access_token FROM users WHERE telegram_id = ?', (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# FLASK WEB SUNUCUSU
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Sunucusu Aktif ve Calisiyor!"

@app.route("/callback")
def callback():
    state = request.args.get("state")
    code = request.args.get("code")
    
    if state not in oauth_sessions:
        return "Gecersiz veya suresi dolmus oturum istegi."
        
    session_data = oauth_sessions.pop(state)
    telegram_id = session_data["telegram_id"]
    code_verifier = session_data["code_verifier"]

    token_url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier
    }
    
    response = requests.post(
        token_url,
        data=data,
        auth=(X_CLIENT_ID, X_CLIENT_SECRET)
    )
    
    if response.status_code == 200:
        token_json = response.json()
        save_tokens(telegram_id, token_json["access_token"], token_json.get("refresh_token", ""))
        return "<h1>Giris Basarili!</h1><p>Telegram'a donup botu kullanmaya baslayabilirsiniz.</p>"
    else:
        return f"Token alma hatasi: {response.text}"

# TELEGRAM BOT KOMUTLARI
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    state = str(uuid.uuid4())
    
    raw_bytes = os.urandom(32)
    code_verifier = base64.urlsafe_b64encode(raw_bytes).decode('utf-8').rstrip('=')
    
    hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(hashed).decode('utf-8').rstrip('=')

    oauth_sessions[state] = {
        "telegram_id": user_id,
        "code_verifier": code_verifier
    }
    
    auth_url = (
        f"https://twitter.com/i/oauth2/authorize?"
        f"response_type=code&client_id={X_CLIENT_ID}&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES.replace(' ', '%20')}&state={state}"
        f"&code_challenge={code_challenge}&code_challenge_method=S256"
    )
    
    bot.reply_to(
        message, 
        f"Merhaba! X (Twitter) hesabınızı bağlamak için aşağıdaki bağlantıya tıklayın:\n\n{auth_url}"
    )

@bot.message_handler(commands=['tweet'])
def post_tweet(message):
    user_id = message.from_user.id
    token = get_user_token(user_id)
    
    if not token:
        bot.reply_to(message, "Lütfen önce /start komutunu kullanarak X hesabınızı bağlayın.")
        return

    tweet_text = message.text.replace("/tweet", "").strip()
    if not tweet_text:
        bot.reply_to(message, "Lütfen paylaşmak istediğiniz metni yazın.\nÖrnek: `/tweet Merhaba Dünya!`")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://api.twitter.com/2/tweets",
        headers=headers,
        json={"text": tweet_text}
    )
    
    if response.status_code == 201:
        bot.reply_to(message, "Tweet başarıyla paylaşıldı! 🚀")
    else:
        bot.reply_to(message, f"Tweet paylaşılırken hata oluştu: {response.text}")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

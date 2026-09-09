import os
import uuid
import sqlite3
import threading
from flask import Flask, request
from requests_oauthlib import OAuth2Session
import telebot

# KONFIGURASYON BILGILERI
TELEGRAM_BOT_TOKEN = "8789026893:AAHbPlzbRbUMJoDuGcmUG3DdxwsjpC3sCs3c"
X_CLIENT_ID = "Q1I1ZzlwaVcyQWREY1B5d2hhc1M6MTpjaA"
X_CLIENT_SECRET = "LW_UJGP9GzdiFCDtjWwL8pC516bQ1Q34Jk"
REDIRECT_URI = "https://x-telegram-bot-servis.onrender.com/callback"
SCOPES = ["tweet.read", "tweet.write", "users.read", "offline.access"]
AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

oauth_states = {}
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

# FLASK WEB SUNUCUSU
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Sunucusu Aktif ve Calisiyor!"

@app.route("/callback")
def callback():
    state = request.args.get("state")
    code = request.args.get("code")
    if state not in oauth_states:
        return "Gecersiz veya suresi dolmus oturum istegi."
    telegram_id = oauth_states.pop(state)
    twitter = OAuth2Session(X_CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
    token = twitter.fetch_token(
        token_url=TOKEN_URL,
        client_secret=X_CLIENT_SECRET,
        code=code,
        include_client_id=True
    )
    save_tokens(telegram_id, token["access_token"], token.get("refresh_token", ""))
    return "Giris basarili! Telegram'a donup botu kullanabilirsiniz."

# TELEGRAM BOT KOMUTU
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    state = str(uuid.uuid4())
    oauth_states[state] = user_id
    
    twitter = OAuth2Session(X_CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
    authorization_url, _ = twitter.authorization_url(AUTH_URL, state=state)
    
    bot.reply_to(
        message, 
        f"Merhaba! X (Twitter) hesabınızı bağlamak için aşağıdaki bağlantıya tıklayın:\n\n{authorization_url}"
    )

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    init_db()
    # Botu ayrı bir thread'de dinlemeye al
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    # Flask sunucusunu başlat
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

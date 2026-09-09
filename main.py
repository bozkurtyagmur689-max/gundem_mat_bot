import os
import io
import uuid
import sqlite3
import threading
import requests
from flask import Flask, request
from requests_oauthlib import OAuth2Session
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# KONFIGURASYON BILGILERI
TELEGRAM_BOT_TOKEN = "8789026893:AAHbPlzbRbUMJoDuGcmUG3DdxwsjpC3sCs3c"
X_CLIENT_ID = "Q1I1ZzlwaVcyQWREY1B5d2hhc1M6MTpjaA"
X_CLIENT_SECRET = "LW_UJGP9GzdiFCDtjWwL8pC516bQ1Q34Jk"
REDIRECT_URI = "https://x-telegram-bot-servis.onrender.com/callback"
SCOPES = ["tweet.read", "tweet.write", "users.read", "offline.access"]
AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

oauth_states = {}

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

def get_tokens(telegram_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT access_token, refresh_token FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (None, None)

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

# TELEGRAM BOT KOMUTLARI
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = str(uuid.uuid4())
    oauth_states[state] = user_id
    
    twitter = OAuth2Session(X_CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
    authorization_url, _ = twitter.authorization_url(AUTH_URL, state=state)
    
    await update.message.reply_text(
        f"Merhaba! X (Twitter) hesabınızı bağlamak için aşağıdaki bağlantıya tıklayın:\n\n{authorization_url}"
    )

def run_telegram_bot():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    init_db()
    # Telegram botunu arka planda çalıştır
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Flask web sunucusunu ana döngüde çalıştır
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

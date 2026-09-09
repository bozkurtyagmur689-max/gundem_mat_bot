import os
import io
import uuid
import sqlite3
import threading
import asyncio
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

def start_bot_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    loop.run_until_complete(application.updater.start_polling(drop_pending_updates=True))
    loop.run_forever()

if __name__ == "__main__":
    init_db()
    # Telegram botunu ayrı bir thread içinde yeni event loop ile başlat
    t = threading.Thread(target=start_bot_loop, daemon=True)
    t.start()
    
    # Flask sunucusunu ana thread'de çalıştır
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

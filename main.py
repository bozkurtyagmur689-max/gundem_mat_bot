import os
import io
import sqlite3
import threading
import requests
from flask import Flask, request
from requests_oauthlib import OAuth2Session
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
# KONFIGURASYON BILGILERI
TELEGRAM_BOT_TOKEN = "BOTFATHER_DAN_ALINAN_TOKEN"
X_CLIENT_ID = "X_DEVELOPER_CLIENT_ID"
X_CLIENT_SECRET = "X_DEVELOPER_CLIENT_SECRET"
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
cursor.execute("SELECT access_token, refresh_token FROM users WHERE telegram_id = ?",
(telegram_id,))
row = cursor.fetchone()
conn.close()
return row if row else (None, None)
app = Flask(__name__)
@app.route("/")
def home():
return "Bot Sunucusu Aktif ve Calisiyor!"
@app.route("/callback")
def callback():
state = request.args.get("state")
code = request.args.get("code")
if state not in oauth_states:
return "Gecersiz veya suresi dolmus oturum istegi.", 400
telegram_id = oauth_states.pop(state)
twitter = OAuth2Session(X_CLIENT_ID, redirect_uri=REDIRECT_URI, state=state)
token = twitter.fetch_token(
token_url=TOKEN_URL,
client_secret=X_CLIENT_SECRET,
code=code,
include_client_id=True
)
save_tokens(telegram_id, token["access_token"], token.get("refresh_token"))
return "

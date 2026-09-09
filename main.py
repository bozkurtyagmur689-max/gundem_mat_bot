import os
import threading
import requests
from requests_oauthlib import OAuth1
from flask import Flask
import telebot

# --- SABIT BILGILER ---
TELEGRAM_BOT_TOKEN = "8789026893:AAHbPlzbRbUMJoDuGcmUG3DdxwsjpC3cS3c"

# X (TWITTER) OAUTH 1.0a ANAHTARLARI
CONSUMER_KEY = "V3N5KZxWAcDVad4mxbQF0FTAk"
CONSUMER_SECRET = "C6VXRz1PGJ9Lxt07R2XVBZV3SERCoeWWeLhQuwVVCs3JDpm25O"
ACCESS_TOKEN = "2092914538412720128-SM27wPHZf4pk4NaM2jIUHMuZlyBxmq"
ACCESS_TOKEN_SECRET = "7OtuiFYCOQZpUjWKJs8MNtwBtvvmNyR0etnPGR5i4JMuGo5mmw"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Sunucusu Aktif ve Calisiyor!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Merhaba! Botunuz hazır ve X hesabınıza bağlı.\n"
        "Tweet atmak için: `/tweet Mesajınız` yazabilirsiniz."
    )

@bot.message_handler(commands=['tweet'])
def post_tweet(message):
    tweet_text = message.text.replace("/tweet", "").strip()
    if not tweet_text:
        bot.reply_to(message, "Lütfen paylaşmak istediğiniz metni yazın.\nÖrnek: `/tweet Merhaba Dünya!`")
        return

    # Direct OAuth 1.0a Kimlik Doğrulaması (Yönlendirme gerektirmez)
    auth = OAuth1(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET
    )
    
    url = "https://api.twitter.com/2/tweets"
    response = requests.post(url, auth=auth, json={"text": tweet_text})
    
    if response.status_code == 201:
        bot.reply_to(message, "Tweet başarıyla paylaşıldı! 🚀")
    else:
        bot.reply_to(message, f"Tweet atılırken hata oluştu: {response.text}")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

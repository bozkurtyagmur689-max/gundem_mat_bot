import os
from flask import Flask, request
import telebot
from mastodon import Mastodon

# Bilgileriniz
TOKEN = os.environ.get('TELEGRAM_TOKEN', 'TELEGRAM_BOT_TOKENINIZI_BURAYA_YAZABILIRSINIZ')
MASTODON_ACCESS_TOKEN = "fQYq5Pj5pwnOMT1Mcr2rwJRcJK_8H0vSY-5bFl9JRYs"
MASTODON_API_BASE_URL = "https://mastodon.social"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Mastodon istemcisini başlatıyoruz
mastodon = Mastodon(
    access_token=MASTODON_ACCESS_TOKEN,
    api_base_url=MASTODON_API_BASE_URL
)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # Render'daki gerçek adresin buraya eklendi
    bot.set_webhook(url='https://x-telegram-bot-servis.onrender.com/' + TOKEN)
    return "Bot aktif ve Mastodon'a bağlı!", 200

@bot.message_handler(commands=['tweet', 'post'])
def send_to_mastodon(message):
    text = message.text.replace('/tweet', '').replace('/post', '').strip()
    
    if not text:
        bot.reply_to(message, "Lütfen gönderilecek metni yazın. Örn: /tweet Merhaba Dünya")
        return

    try:
        mastodon.status_post(text)
        bot.reply_to(message, "Başarıyla Mastodon'da paylaşıldı! 🚀")
    except Exception as e:
        bot.reply_to(message, f"Bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

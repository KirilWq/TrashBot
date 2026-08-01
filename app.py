import os
import logging
from flask import Flask, request
import telebot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set")
    raise RuntimeError("BOT_TOKEN not set")

# optional secret path to make webhook URL unguessable
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "changeme-secret")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Example handler using pyTelegramBotAPI decorators
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привіт! Бот успішно підключений до Cloud Run webhook.")

@app.route("/", methods=["GET"])
def index():
    return "OK", 200

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def telegram_webhook():
    if request.headers.get("content-type") != "application/json":
        # Telegram always sends JSON for updates
        return "", 400
    json_str = request.get_data().decode("utf-8")
    try:
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        logger.exception("Failed processing update: %s", e)
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

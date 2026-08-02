import os
import logging
from flask import Flask, request
from flask_cors import CORS
import telebot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set")
    raise RuntimeError("BOT_TOKEN not set")

# optional secret path to make webhook URL unguessable
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "changeme-secret")

# Optional: FRONTEND_URL env var (set in Render) to restrict CORS to your frontend.
FRONTEND_URL = os.environ.get("FRONTEND_URL")

# Import the main bot instance and handlers from bot.py so all handlers are registered
# and the same bot instance processes webhook updates.
from bot import bot as telegram_bot

app = Flask(__name__)

# Configure CORS: if FRONTEND_URL provided, restrict to it; otherwise allow all origins (useful for testing)
if FRONTEND_URL:
    CORS(app, origins=[FRONTEND_URL])
else:
    CORS(app)

@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# health / ping endpoint for frontend to verify backend connectivity
@app.route("/api/ping", methods=["GET"])
def api_ping():
    return {"ok": True, "message": "pong", "service": "tg-backend"}, 200

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def telegram_webhook():
    if request.headers.get("content-type") != "application/json":
        # Telegram always sends JSON for updates
        return "", 400
    json_str = request.get_data().decode("utf-8")
    try:
        update = telebot.types.Update.de_json(json_str)
        telegram_bot.process_new_updates([update])
    except Exception as e:
        logger.exception("Failed processing update: %s", e)
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

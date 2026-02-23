import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
PORT = int(os.environ.get("PORT", 10000))

DATA_FILE = "data.json"
CHECK_INTERVAL = 300

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running 24/7 🚀"

# ==============================
# DATA SYSTEM
# ==============================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "admins": [], "watch": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ==============================
# SIMPLE COMMAND
# ==============================

def start(update, context):
    update.message.reply_text("✅ Bot running 24/7 on Render")

# ==============================
# MAIN
# ==============================

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))

    print("Bot polling started...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=PORT)

import os
import threading
from flask import Flask
from telegram.ext import Updater, CommandHandler

# =====================
# ENV
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

# =====================
# FLASK
# =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running ✅"

# =====================
# TELEGRAM
# =====================
def start(update, context):
    update.message.reply_text(
        "🚀 Instagram Monitor Bot Active!\n\nPowered by @proxyfxc"
    )

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    print("Bot polling started...")
    updater.start_polling()
    updater.idle()

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

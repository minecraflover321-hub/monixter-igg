import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# ENV VARIABLES
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables!")

# =========================
# FLASK APP (KEEP ALIVE)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running successfully ✅"

# =========================
# TELEGRAM BOT FUNCTIONS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🚀 Instagram Monitor Bot Active!\n\n"
        "Bot is running successfully.\n\n"
        "Powered by @proxyfxc"
    )

# =========================
# START TELEGRAM BOT
# =========================
def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("Bot polling started...")
    application.run_polling()

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    # Run bot in separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Run flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

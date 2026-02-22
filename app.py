import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
from bot import start, add_watch
from scheduler import monitor
from config import BOT_TOKEN

app = Flask(__name__)

@app.route("/")
def health():
    return "Bot Running ✅"

async def telegram_main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addwatch", add_watch))

    # Start background monitor task
    application.create_task(monitor(application))

    await application.run_polling()

def run_telegram():
    asyncio.run(telegram_main())

if __name__ == "__main__":
    # Run Telegram bot in separate thread
    threading.Thread(target=run_telegram).start()

    # Bind to Render PORT properly
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

import asyncio
from flask import Flask
from telegram.ext import ApplicationBuilder
from telegram.ext import CommandHandler
from bot import start, add_watch
from scheduler import monitor
from config import BOT_TOKEN

app = Flask(__name__)

@app.route("/")
def health():
    return "Bot Running ✅"

async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addwatch", add_watch))

    application.create_task(monitor(application))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
import os
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

def start(update, context):
    update.message.reply_text(
        "🚀 Instagram Monitor Bot Active!\n\nPowered by @proxyfxc"
    )

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))

    print("Bot polling started...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    m

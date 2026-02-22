import os
import json
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

DATA_FILE = "data.json"

# -----------------------
# Load / Save Data
# -----------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"watch": {}, "ban": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# -----------------------
# Fake Status Checker (Replace later with real API)
# -----------------------
def check_status(username):
    # Demo logic
    if username.lower().startswith("ban"):
        return "banned"
    return "active"

# -----------------------
# Commands
# -----------------------
def start(update, context):
    update.message.reply_text(
        "🚀 Instagram Monitor Bot Active\n\n"
        "Commands:\n"
        "/watch username\n"
        "/ban username\n"
        "/check username\n"
        "/list\n"
        "/remove username\n\n"
        "Powered by @proxyfxc"
    )

def watch(update, context):
    if not context.args:
        update.message.reply_text("Usage: /watch username")
        return

    username = context.args[0]
    data = load_data()
    data["watch"][username] = "unknown"
    save_data(data)

    update.message.reply_text(f"✅ {username} added to WATCH list")

def ban(update, context):
    if not context.args:
        update.message.reply_text("Usage: /ban username")
        return

    username = context.args[0]
    data = load_data()
    data["ban"][username] = "banned"
    save_data(data)

    update.message.reply_text(f"🚫 {username} added to BAN list")

def check(update, context):
    if not context.args:
        update.message.reply_text("Usage: /check username")
        return

    username = context.args[0]
    status = check_status(username)

    update.message.reply_text(
        f"🔍 {username} status: {status.upper()}"
    )

def list_users(update, context):
    data = load_data()
    watch_list = "\n".join(data["watch"].keys()) or "Empty"
    ban_list = "\n".join(data["ban"].keys()) or "Empty"

    update.message.reply_text(
        f"👀 WATCH LIST:\n{watch_list}\n\n"
        f"🚫 BAN LIST:\n{ban_list}"
    )

def remove(update, context):
    if not context.args:
        update.message.reply_text("Usage: /remove username")
        return

    username = context.args[0]
    data = load_data()

    data["watch"].pop(username, None)
    data["ban"].pop(username, None)

    save_data(data)

    update.message.reply_text(f"❌ {username} removed from all lists")

# -----------------------
# Main
# -----------------------
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("watch", watch))
    dp.add_handler(CommandHandler("ban", ban))
    dp.add_handler(CommandHandler("check", check))
    dp.add_handler(CommandHandler("list", list_users))
    dp.add_handler(CommandHandler("remove", remove))

    print("Bot polling started...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

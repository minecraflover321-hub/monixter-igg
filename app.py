import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

DATA_FILE = "data.json"
CHECK_INTERVAL = 120  # seconds

# -----------------------
# Data Handling
# -----------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "watch": {}, "ban": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# -----------------------
# Subscription Logic
# -----------------------
def is_allowed(user_id):
    if user_id == OWNER_ID:
        return True
    data = load_data()
    if str(user_id) not in data["users"]:
        return False
    expiry = data["users"][str(user_id)]
    return datetime.utcnow() < datetime.fromisoformat(expiry)

def approve(update, context):
    if update.effective_user.id != OWNER_ID:
        return
    if len(context.args) != 2:
        update.message.reply_text("Usage: /approve user_id days")
        return

    user_id = context.args[0]
    days = int(context.args[1])

    data = load_data()
    expiry = datetime.utcnow() + timedelta(days=days)
    data["users"][user_id] = expiry.isoformat()
    save_data(data)

    update.message.reply_text(f"Approved {user_id} for {days} days")

# -----------------------
# Status Provider (Replaceable)
# -----------------------
def check_status(username):
    try:
        url = f"https://insta-profile-info-api.vercel.app/api/instagram.php?username={username}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and "username" in r.text:
            return "active"
        return "banned"
    except:
        return "unknown"

# -----------------------
# Commands
# -----------------------
def start(update, context):
    update.message.reply_text(
        "🚀 Instagram Monitor Bot\n\n"
        "/watch username\n"
        "/ban username\n"
        "/check username\n"
        "/list\n"
        "/remove username\n\n"
        "Powered by @proxyfxc"
    )

def watch(update, context):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        update.message.reply_text("Subscription required.")
        return

    if not context.args:
        update.message.reply_text("Usage: /watch username")
        return

    username = context.args[0].lower()
    data = load_data()

    if user_id != OWNER_ID:
        user_watch_count = sum(1 for u in data["watch"] if data["watch"][u]["owner"] == user_id)
        if user_watch_count >= 20:
            update.message.reply_text("Limit reached (20 usernames).")
            return

    data["watch"][username] = {"status": "unknown", "owner": user_id}
    save_data(data)
    update.message.reply_text(f"{username} added to WATCH list")

def ban(update, context):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        update.message.reply_text("Subscription required.")
        return

    if not context.args:
        update.message.reply_text("Usage: /ban username")
        return

    username = context.args[0].lower()
    data = load_data()
    data["ban"][username] = {"status": "banned", "owner": user_id}
    save_data(data)
    update.message.reply_text(f"{username} added to BAN list")

def check(update, context):
    if not context.args:
        update.message.reply_text("Usage: /check username")
        return

    username = context.args[0].lower()
    status = check_status(username)
    update.message.reply_text(f"{username} status: {status.upper()}")

def list_users(update, context):
    data = load_data()
    watch = "\n".join(data["watch"].keys()) or "Empty"
    ban = "\n".join(data["ban"].keys()) or "Empty"
    update.message.reply_text(f"WATCH:\n{watch}\n\nBAN:\n{ban}")

def remove(update, context):
    if not context.args:
        update.message.reply_text("Usage: /remove username")
        return

    username = context.args[0].lower()
    data = load_data()
    data["watch"].pop(username, None)
    data["ban"].pop(username, None)
    save_data(data)
    update.message.reply_text(f"{username} removed")

# -----------------------
# Monitoring Engine
# -----------------------
def monitor_loop(updater):
    while True:
        data = load_data()

        # WATCH → detect ban
        for username in list(data["watch"].keys()):
            status = check_status(username)
            prev = data["watch"][username]["status"]

            if prev != "banned" and status == "banned":
                owner = data["watch"][username]["owner"]
                updater.bot.send_message(owner, f"{username} BANNED successfully")
                data["watch"][username]["status"] = "banned"

            if prev == "banned" and status == "active":
                owner = data["watch"][username]["owner"]
                updater.bot.send_message(owner, f"{username} UNBANNED successfully")
                data["watch"][username]["status"] = "active"

        save_data(data)
        time.sleep(CHECK_INTERVAL)

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
    dp.add_handler(CommandHandler("approve", approve))

    threading.Thread(target=monitor_loop, args=(updater,), daemon=True).start()

    print("Bot polling started...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

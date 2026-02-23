import os
import json
import asyncio
import requests
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DATA_FILE = "data.json"
CHECK_INTERVAL = 300  # 5 min
MAX_USERS = 300
MAX_USER_WATCH = 20

# ---------------- DATA ---------------- #

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "admins": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ---------------- PERMISSIONS ---------------- #

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return is_owner(user_id) or user_id in data["admins"]

def is_approved(user_id):
    if is_owner(user_id):
        return True
    user = data["users"].get(str(user_id))
    if not user:
        return False
    if datetime.utcnow() > datetime.fromisoformat(user["expiry"]):
        return False
    return True

# ---------------- INSTAGRAM CHECK ---------------- #

def check_instagram(username):
    try:
        url = f"https://insta-profile-info-api.vercel.app/api/instagram.php?username={username}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        if "User not found" in r.text:
            return "banned"
        return "active"
    except:
        return None

# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
✨ WELCOME TO MONITOR BOT ✨
━━━━━━━━━━━━━━━━━━━━
Powered by: @proxyfxc

📌 Commands:
🔹 /watch username
🔹 /ban username
🔹 /status username
🔹 /list
🔹 /banlist
━━━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(msg)

async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_approved(user_id):
        return await update.message.reply_text("🚫 Subscription Required.")

    if not context.args:
        return await update.message.reply_text("Usage: /watch username")

    username = context.args[0].lower()

    user_data = data["users"].setdefault(str(user_id), {
        "watch": [],
        "ban": [],
        "expiry": (datetime.utcnow() + timedelta(days=1)).isoformat()
    })

    if not is_owner(user_id) and len(user_data["watch"]) >= MAX_USER_WATCH:
        return await update.message.reply_text("⚠️ Watch limit reached (20).")

    if username not in user_data["watch"]:
        user_data["watch"].append(username)
        save_data(data)

    await update.message.reply_text(f"✅ {username} added to Watch List.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_approved(user_id):
        return await update.message.reply_text("🚫 Subscription Required.")

    if not context.args:
        return await update.message.reply_text("Usage: /ban username")

    username = context.args[0].lower()

    user_data = data["users"].setdefault(str(user_id), {
        "watch": [],
        "ban": [],
        "expiry": (datetime.utcnow() + timedelta(days=1)).isoformat()
    })

    if username not in user_data["ban"]:
        user_data["ban"].append(username)
        save_data(data)

    await update.message.reply_text(f"📌 {username} added to Ban List.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /status username")

    username = context.args[0].lower()
    result = check_instagram(username)

    if result == "banned":
        await update.message.reply_text(f"🚫 {username} is BANNED")
    elif result == "active":
        await update.message.reply_text(f"✅ {username} is ACTIVE")
    else:
        await update.message.reply_text("⚠️ Unable to fetch status.")

async def list_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = data["users"].get(str(user_id))
    if not user or not user["watch"]:
        return await update.message.reply_text("No watch list.")
    text = "👀 Watch List:\n" + "\n".join(user["watch"])
    await update.message.reply_text(text)

async def list_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = data["users"].get(str(user_id))
    if not user or not user["ban"]:
        return await update.message.reply_text("No ban list.")
    text = "🚫 Ban List:\n" + "\n".join(user["ban"])
    await update.message.reply_text(text)

# ---------------- MONITOR LOOP ---------------- #

async def monitor(app):
    while True:
        for user_id, user in data["users"].items():

            # Watch → detect ban
            for username in list(user["watch"]):
                result = check_instagram(username)
                if result == "banned":
                    await app.bot.send_message(
                        chat_id=int(user_id),
                        text=f"🚨 ALERT: {username} BANNED"
                    )
                    if username not in user["ban"]:
                        user["ban"].append(username)

            # Ban → detect unban
            for username in list(user["ban"]):
                result = check_instagram(username)
                if result == "active":
                    await app.bot.send_message(
                        chat_id=int(user_id),
                        text=f"🎉 {username} UNBANNED SUCCESSFULLY"
                    )
                    user["ban"].remove(username)

        save_data(data)
        await asyncio.sleep(CHECK_INTERVAL)

# ---------------- FLASK KEEP ALIVE ---------------- #

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot Running"

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

# ---------------- MAIN ---------------- #

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("watch", watch))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_watch))
    app.add_handler(CommandHandler("banlist", list_ban))

    app.create_task(monitor(app))

    await app.run_polling()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())

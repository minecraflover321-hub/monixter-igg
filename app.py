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
CHECK_INTERVAL = 300
MAX_USER_WATCH = 20

# ---------------- DATA ---------------- #

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {"users": {}}

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

data = load_data()

# ---------------- PERMISSION ---------------- #

def is_owner(uid):
    return uid == OWNER_ID

def is_approved(uid):
    if is_owner(uid):
        return True
    user = data["users"].get(str(uid))
    if not user:
        return False
    try:
        if datetime.utcnow() > datetime.fromisoformat(user["expiry"]):
            return False
    except:
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
    await update.message.reply_text(
        "✨ WELCOME TO MONITOR BOT ✨\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Powered by: @proxyfxc\n\n"
        "Commands:\n"
        "/watch username\n"
        "/ban username\n"
        "/status username\n"
        "/list\n"
        "/banlist\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_approved(uid):
        return await update.message.reply_text("🚫 Subscription Required")
    if not context.args:
        return await update.message.reply_text("Usage: /watch username")
    username = context.args[0].lower()
    user = data["users"].setdefault(str(uid), {
        "watch": [],
        "ban": [],
        "expiry": (datetime.utcnow() + timedelta(days=30)).isoformat()
    })
    if not is_owner(uid) and len(user["watch"]) >= MAX_USER_WATCH:
        return await update.message.reply_text("⚠️ Watch limit reached (20)")
    if username not in user["watch"]:
        user["watch"].append(username)
        save_data(data)
    await update.message.reply_text(f"✅ {username} added to Watch List")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_approved(uid):
        return await update.message.reply_text("🚫 Subscription Required")
    if not context.args:
        return await update.message.reply_text("Usage: /ban username")
    username = context.args[0].lower()
    user = data["users"].setdefault(str(uid), {
        "watch": [],
        "ban": [],
        "expiry": (datetime.utcnow() + timedelta(days=30)).isoformat()
    })
    if username not in user["ban"]:
        user["ban"].append(username)
        save_data(data)
    await update.message.reply_text(f"📌 {username} added to Ban List")

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
        await update.message.reply_text("⚠️ Unable to fetch status")

async def list_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = data["users"].get(str(uid))
    if not user or not user["watch"]:
        return await update.message.reply_text("No watch list")
    await update.message.reply_text("👀 Watch List:\n" + "\n".join(user["watch"]))

async def list_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = data["users"].get(str(uid))
    if not user or not user["ban"]:
        return await update.message.reply_text("No ban list")
    await update.message.reply_text("🚫 Ban List:\n" + "\n".join(user["ban"]))

# ---------------- MONITOR ---------------- #

async def monitor(application):
    while True:
        # Loop over a copy to avoid dictionary size change issues
        uids = list(data["users"].keys())
        for uid in uids:
            user = data["users"][uid]
            # Watch check
            for username in list(user.get("watch", [])):
                result = check_instagram(username)
                if result == "banned":
                    try:
                        await application.bot.send_message(chat_id=int(uid), text=f"🚨 ALERT: {username} BANNED")
                        if username not in user.get("ban", []):
                            user.setdefault("ban", []).append(username)
                    except: pass
            # Ban check
            for username in list(user.get("ban", [])):
                result = check_instagram(username)
                if result == "active":
                    try:
                        await application.bot.send_message(chat_id=int(uid), text=f"🎉 {username} UNBANNED SUCCESSFULLY")
                        user["ban"].remove(username)
                    except: pass
        save_data(data)
        await asyncio.sleep(CHECK_INTERVAL)

# ---------------- FLASK ---------------- #

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot Running"

def run_flask():
    # Render uses port 10000 by default, keeping your port
    flask_app.run(host="0.0.0.0", port=10000)

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    # Start Flask in background
    Thread(target=run_flask, daemon=True).start()

    # Setup Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("watch", watch))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("list", list_watch))
    application.add_handler(CommandHandler("banlist", list_ban))

    # Correct way to add a background task in PTB v20
    async def post_init(app):
        asyncio.create_task(monitor(app))

    application.post_init = post_init
    
    # Run bot
    application.run_polling()

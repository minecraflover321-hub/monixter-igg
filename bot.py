from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import OWNER_ID, MAX_USERS, MAX_USERNAMES
from database import load_db, save_db, is_subscription_active
from datetime import datetime, timedelta

db = load_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in db["users"]:
        if len(db["users"]) >= MAX_USERS and int(user_id) != OWNER_ID:
            await update.message.reply_text("User limit reached.")
            return

        db["users"][user_id] = {
            "role": "owner" if int(user_id) == OWNER_ID else "user",
            "expiry": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "watch": [],
            "ban": []
        }
        save_db(db)

    await update.message.reply_text("Bot Activated ✅")

async def add_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("Usage: /addwatch username")
        return

    username = context.args[0]
    user = db["users"][user_id]

    if not is_subscription_active(user):
        await update.message.reply_text("Subscription expired.")
        return

    if user["role"] != "owner" and len(user["watch"]) >= MAX_USERNAMES:
        await update.message.reply_text("Max username limit reached.")
        return

    if username not in user["watch"]:
        user["watch"].append(username)
        save_db(db)

    await update.message.reply_text(f"{username} added to Watch List.")
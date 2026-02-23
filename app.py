import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler
from flask import Flask

# Flask Server for Render (Keep Alive)
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ==============================
# CONFIG & DATA
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
DATA_FILE = "data.json"
CHECK_INTERVAL = 300 

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "admins": [], "watch": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "admins": [], "watch": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==============================
# ROLE SYSTEM
# ==============================
def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    data = load_data()
    return user_id == OWNER_ID or user_id in data["admins"]

def is_allowed(user_id):
    if is_admin(user_id): return True
    data = load_data()
    if str(user_id) not in data["users"]: return False
    expiry = datetime.fromisoformat(data["users"][str(user_id)])
    return datetime.utcnow() < expiry

# ==============================
# STATUS CHECKER
# ==============================
def check_status(username):
    try:
        url = f"https://insta-profile-info-api.vercel.app/api/instagram.php?username={username}"
        r = requests.get(url, timeout=15)
        if r.status_code != 200: return "unknown"
        return "active" if '"username"' in r.text else "banned"
    except:
        return "unknown"

# ==============================
# COMMANDS
# ==============================
def start(update, context):
    update.message.reply_text("✨ MONITOR BOT ACTIVE ✨\n/watch <user>\n/check <user>\n/list")

def watch(update, context):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        update.message.reply_text("❌ Subscription required.")
        return
    if not context.args:
        update.message.reply_text("Usage: /watch username")
        return

    username = context.args[0].lower()
    data = load_data()
    
    if not is_admin(user_id):
        user_watch = [u for u in data["watch"] if data["watch"][u].get("owner") == user_id]
        if len(user_watch) >= 20:
            update.message.reply_text("⚠ Limit reached (20 max).")
            return

    data["watch"][username] = {"status": "unknown", "owner": user_id, "confirm": 0}
    save_data(data)
    update.message.reply_text(f"✅ Monitoring started for: {username}")

def check(update, context):
    if not context.args:
        update.message.reply_text("Usage: /check username")
        return
    username = context.args[0].lower()
    status = check_status(username)
    emoji = "🟢" if status == "active" else "🔴" if status == "banned" else "⚪"
    update.message.reply_text(f"{emoji} Status: {status.upper()}")

def list_users(update, context):
    user_id = update.effective_user.id
    data = load_data()
    user_watch = [u for u in data["watch"] if data["watch"][u].get("owner") == user_id]
    if not user_watch:
        update.message.reply_text("📭 List empty.")
        return
    update.message.reply_text("📋 Watchlist:\n" + "\n".join([f"• {u}" for u in user_watch]))

def remove(update, context):
    if not context.args: return
    username = context.args[0].lower()
    data = load_data()
    if username in data["watch"]:
        del data["watch"][username]
        save_data(data)
        update.message.reply_text(f"❌ Removed {username}")

def approve(update, context):
    if not is_admin(update.effective_user.id) or len(context.args) != 2: return
    user_id, days = context.args[0], int(context.args[1])
    data = load_data()
    data["users"][user_id] = (datetime.utcnow() + timedelta(days=days)).isoformat()
    save_data(data)
    update.message.reply_text(f"✅ User {user_id} approved for {days} days.")

# ==============================
# MONITOR ENGINE
# ==============================
def monitor_loop(updater):
    while True:
        try:
            data = load_data()
            changed = False
            for username in list(data["watch"].keys()):
                status = check_status(username)
                if status == "unknown": continue
                
                watch_info = data["watch"][username]
                if status != watch_info["status"]:
                    watch_info["confirm"] += 1
                else:
                    watch_info["confirm"] = 0

                if watch_info["confirm"] >= 3:
                    owner = watch_info["owner"]
                    msg = f"🚨 {username} BANNED ❌" if status == "banned" else f"🎉 {username} ACTIVE ✅"
                    try:
                        updater.bot.send_message(owner, msg)
                    except: pass
                    watch_info["status"] = status
                    watch_info["confirm"] = 0
                    changed = True
            
            if changed: save_data(data)
        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(CHECK_INTERVAL)

# ==============================
# MAIN
# ==============================
def main():
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("watch", watch))
    dp.add_handler(CommandHandler("check", check))
    dp.add_handler(CommandHandler("list", list_users))
    dp.add_handler(CommandHandler("remove", remove))
    dp.add_handler(CommandHandler("approve", approve))

    threading.Thread(target=monitor_loop, args=(updater,), daemon=True).start()

    print("Bot is alive...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

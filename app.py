import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify
from telegram.ext import Updater, CommandHandler

# Flask app for health check
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

DATA_FILE = "data.json"
CHECK_INTERVAL = 300  # 5 Minutes

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

# ==============================
# DATA SYSTEM
# ==============================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "admins": [], "watch": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ==============================
# ROLE SYSTEM
# ==============================
def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    data = load_data()
    return user_id == OWNER_ID or user_id in data["admins"]

def is_allowed(user_id):
    if is_admin(user_id):
        return True
    data = load_data()
    if str(user_id) not in data["users"]:
        return False
    expiry = datetime.fromisoformat(data["users"][str(user_id)])
    return datetime.utcnow() < expiry

# ==============================
# STATUS CHECKER
# ==============================
def check_status(username):
    try:
        url = f"https://insta-profile-info-api.vercel.app/api/instagram.php?username={username}"
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return "unknown"

        if '"username"' in r.text:
            return "active"

        return "banned"
    except Exception as e:
        print(f"Error checking {username}: {e}")
        return "unknown"

# ==============================
# UI MESSAGES
# ==============================
WELCOME_MSG = """
✨ WELCOME TO MONITOR BOT ✨
━━━━━━━━━━━━━━━━━━━━
Powered by: @proxyfxc

I provide 24/7 professional Instagram monitoring.

📍 Commands:
🔹 /watch <username>
🔹 /check <username>
🔹 /list
🔹 /remove <username>

👑 Admin:
🔸 /approve <user_id> <days>
🔸 /addadmin <user_id>
🔸 /removeadmin <user_id>
━━━━━━━━━━━━━━━━━━━━
"""

# ==============================
# COMMANDS
# ==============================
def start(update, context):
    update.message.reply_text(WELCOME_MSG)

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
        user_watch = [u for u in data["watch"] if data["watch"][u]["owner"] == user_id]
        if len(user_watch) >= 20:
            update.message.reply_text("⚠ Limit reached (20 usernames max).")
            return

    data["watch"][username] = {
        "status": "unknown",
        "owner": user_id,
        "confirm": 0
    }

    save_data(data)

    update.message.reply_text(
        f"✅ USER ADDED TO WATCH\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Username: {username}\n"
        f"Status: Monitoring started"
    )

def check(update, context):
    if not context.args:
        update.message.reply_text("Usage: /check username")
        return

    username = context.args[0].lower()
    status = check_status(username)

    emoji = "🟢" if status == "active" else "🔴" if status == "banned" else "⚪"

    update.message.reply_text(
        f"{emoji} LIVE STATUS REPORT\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Username: {username}\n"
        f"Status: {status.upper()}"
    )

def list_users(update, context):
    user_id = update.effective_user.id
    data = load_data()

    user_watch = [u for u in data["watch"] if data["watch"][u]["owner"] == user_id]

    if not user_watch:
        update.message.reply_text("📭 Your watchlist is empty.")
        return

    formatted = "\n".join([f"• {u}" for u in user_watch])

    update.message.reply_text(
        f"📋 YOUR WATCHLIST\n━━━━━━━━━━━━━━━━━━━━\n{formatted}"
    )

def remove(update, context):
    if not context.args:
        update.message.reply_text("Usage: /remove username")
        return

    username = context.args[0].lower()
    data = load_data()

    if username in data["watch"]:
        del data["watch"][username]
        save_data(data)
        update.message.reply_text(f"❌ Removed {username} from watchlist.")
    else:
        update.message.reply_text("Username not found.")

# ==============================
# ADMIN COMMANDS
# ==============================
def approve(update, context):
    if not is_admin(update.effective_user.id):
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

    update.message.reply_text(f"✅ User {user_id} approved for {days} days.")

def add_admin(update, context):
    if not is_owner(update.effective_user.id):
        return

    if not context.args:
        update.message.reply_text("Usage: /addadmin user_id")
        return

    user_id = int(context.args[0])
    data = load_data()

    if user_id not in data["admins"]:
        data["admins"].append(user_id)
        save_data(data)

    update.message.reply_text(f"👑 {user_id} promoted to ADMIN.")

def remove_admin(update, context):
    if not is_owner(update.effective_user.id):
        return

    if not context.args:
        update.message.reply_text("Usage: /removeadmin user_id")
        return

    user_id = int(context.args[0])
    data = load_data()

    if user_id in data["admins"]:
        data["admins"].remove(user_id)
        save_data(data)

    update.message.reply_text(f"❌ {user_id} removed from ADMIN.")

# ==============================
# MONITOR ENGINE
# ==============================
def monitor_loop(updater):
    while True:
        try:
            data = load_data()

            for username in list(data["watch"].keys()):
                status = check_status(username)
                prev = data["watch"][username]["status"]

                if status == "unknown":
                    continue

                if status != prev:
                    data["watch"][username]["confirm"] += 1
                else:
                    data["watch"][username]["confirm"] = 0

                if data["watch"][username]["confirm"] >= 3:
                    owner = data["watch"][username]["owner"]

                    try:
                        if status == "banned":
                            updater.bot.send_message(
                                owner,
                                f"🚨 ALERT\n━━━━━━━━━━━━━━━━━━━━\n"
                                f"Username: {username}\n"
                                f"Status: BANNED ❌"
                            )
                        elif status == "active":
                            updater.bot.send_message(
                                owner,
                                f"🎉 UPDATE\n━━━━━━━━━━━━━━━━━━━━\n"
                                f"Username: {username}\n"
                                f"Status: UNBANNED ✅"
                            )
                    except Exception as e:
                        print(f"Error sending message to {owner}: {e}")

                    data["watch"][username]["status"] = status
                    data["watch"][username]["confirm"] = 0

            save_data(data)
        except Exception as e:
            print(f"Error in monitor loop: {e}")
        
        time.sleep(CHECK_INTERVAL)

# ==============================
# FLASK ROUTES
# ==============================
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "bot": "running",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/stats')
def stats():
    data = load_data()
    return jsonify({
        "total_users": len(data["users"]),
        "total_admins": len(data["admins"]),
        "total_watched": len(data["watch"]),
        "owner_id": OWNER_ID
    })

# ==============================
# BOT THREAD FUNCTION
# ==============================
def run_bot():
    """Run the Telegram bot"""
    try:
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("watch", watch))
        dp.add_handler(CommandHandler("check", check))
        dp.add_handler(CommandHandler("list", list_users))
        dp.add_handler(CommandHandler("remove", remove))
        dp.add_handler(CommandHandler("approve", approve))
        dp.add_handler(CommandHandler("addadmin", add_admin))
        dp.add_handler(CommandHandler("removeadmin", remove_admin))

        # Start monitor thread
        threading.Thread(target=monitor_loop, args=(updater,), daemon=True).start()

        print("Bot polling started...")
        updater.start_polling()
        updater.idle()
    except Exception as e:
        print(f"Error in bot thread: {e}")

# ==============================
# MAIN ENTRY POINT
# ==============================
if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask app (Render will call this)
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

import asyncio
from database import load_db, save_db
from config import CHECK_INTERVAL

async def check_status(username):
    # Placeholder
    # Yaha tum approved API integrate karoge
    return "ACTIVE"

async def monitor(application):
    while True:
        db = load_db()

        for user_id, user in db["users"].items():
            for username in list(user["watch"]):
                status = await check_status(username)

                if status == "BANNED":
                    await application.bot.send_message(
                        chat_id=user_id,
                        text=f"🚫 BANNED SUCCESSFULLY\nUsername: {username}\nPowered by @proxyfxc"
                    )
                    user["watch"].remove(username)
                    user["ban"].append(username)

            for username in list(user["ban"]):
                status = await check_status(username)

                if status == "ACTIVE":
                    await application.bot.send_message(
                        chat_id=user_id,
                        text=f"✅ UNBANNED SUCCESSFULLY\nUsername: {username}\nPowered by @proxyfxc"
                    )
                    user["ban"].remove(username)
                    user["watch"].append(username)

        save_db(db)
        await asyncio.sleep(CHECK_INTERVAL)
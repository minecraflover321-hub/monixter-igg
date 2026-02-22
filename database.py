import json
import os
from datetime import datetime

DB_FILE = "data.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_subscription_active(user):
    if user["role"] == "owner":
        return True
    expiry = datetime.strptime(user["expiry"], "%Y-%m-%d")
    return datetime.now() < expiry
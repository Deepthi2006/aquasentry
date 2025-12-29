import json
import secrets
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

DATA_PATH = Path(__file__).parent.parent / "data"

active_tokens = {}

def load_users():
    users_file = DATA_PATH / "users.json"
    if users_file.exists():
        with open(users_file, "r") as f:
            return json.load(f)["users"]
    return []

def authenticate_user(username: str, password: str):
    users = load_users()
    for user in users:
        if user["username"] == username and user["password"] == password:
            token = secrets.token_hex(32)
            active_tokens[token] = {
                "user_id": user["id"],
                "username": user["username"],
                "name": user["name"],
                "role": user["role"],
                "expires": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            return {
                "success": True,
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "name": user["name"],
                    "role": user["role"]
                }
            }
    return {"success": False, "error": "Invalid username or password"}

def validate_token(token: str):
    if token in active_tokens:
        token_data = active_tokens[token]
        expires = datetime.fromisoformat(token_data["expires"])
        if datetime.now() < expires:
            return {"valid": True, "user": token_data}
        else:
            del active_tokens[token]
    return {"valid": False}

def logout(token: str):
    if token in active_tokens:
        del active_tokens[token]
        return {"success": True}
    return {"success": False}

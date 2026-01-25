import os
import json
from datetime import datetime

# Global states
user_states = {}
user_progress = {}

def load_user_progress(file_path):
    global user_progress
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                user_progress = json.load(f)
        except Exception as e:
            print(f"[STATE] Error loading user progress: {e}")
            user_progress = {}

def save_user_progress(file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(user_progress, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[STATE] Error saving user progress: {e}")

def register_user_activity(chat_id, file_path=None):
    cid = str(chat_id)
    if cid not in user_progress:
        user_progress[cid] = []
        if file_path:
            save_user_progress(file_path)

def update_last_activity(chat_id):
    if chat_id in user_states:
        user_states[chat_id]["last_activity"] = datetime.now()

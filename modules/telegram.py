import os

import requests
import dotenv

class Telegram:
    def __init__(self,
                 token: str,
                 chat_id: int):
        self.token = token
        self.chat_id = chat_id
        self.message_id = None
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, message: str):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error sending message to Telegram: {e}")
            return None

    def edit_message(self, message_id: int, new_message: str):
        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "text": new_message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error editing message in Telegram: {e}")
            return None

dotenv.load_dotenv(".env")
notif = Telegram(
    token=os.getenv("TELEGRAM_TOKEN"),
    chat_id=int(os.getenv("CHAT_ID"))
)
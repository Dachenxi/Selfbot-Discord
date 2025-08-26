import os
import requests
import dotenv
from typing import Optional

class Telegram:
    def __init__(self,
                 token: str,
                 chat_id: int):
        self.token = token
        self.chat_id = chat_id
        self.message_id = None
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, message: str, message_thread_id: Optional[int] = None) -> dict | None:
        url = f"{self.base_url}/sendMessage"
        if message_thread_id:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "markdown",
                "message_thread_id": message_thread_id
            }
        else:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "markdown"
            }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error sending message to Telegram: {e}")
            return None

    def edit_message(self, message_id: int, new_message: str, message_thread_id: Optional[int] = None) -> dict | None:
        url = f"{self.base_url}/editMessageText"
        if message_thread_id:
            payload = {
                "chat_id": self.chat_id,
                "message_id": message_id,
                "text": new_message,
                "parse_mode": "markdown",
                "message_thread_id": message_thread_id
            }
        else:
            payload = {
                "chat_id": self.chat_id,
                "message_id": message_id,
                "text": new_message,
                "parse_mode": "markdown"
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
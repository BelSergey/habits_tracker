
import requests
from django.conf import settings


def send_telegram_message(chat_id: str, message: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        return
    url = f'{settings.TELEGRAM_API_URL}{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    requests.post(url, data={'chat_id': chat_id, 'text': message}, timeout=10)
import telegram
import requests
import logging
import os

# === CONSTANTS
logger = logging.getLogger("health-monitor")
logger.setLevel(logging.INFO)
chat_id = "-347437679"
token = "635186642:AAFeZ8KjyhQLSg4HBVt1Wd2vCqYQEFa-1-E"
url = "https://api.telegram.org/bot" + token + "/sendPhoto"
TEST = False


def send_image(msg, gate):
    if not TEST:  # === TODO remove TEST
        if os.name == 'nt':
            path = f"C:/Users/gsantiago/PycharmProjects/2021/logs/health-monitor/{gate.replace(':', '_').replace('/', '_')}.png"
        else:
            path = f"/var/log/python/health-monitor/uploads/{gate.replace(':', '_').replace('/', '_')}.png"
        data = {"chat_id": chat_id, "caption": msg}
        file = {"photo": open(path, "rb")}
        r = requests.post(url, files=file, data=data)
        # logger.info(r.text)


def send(msg):
    if not TEST:
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id=chat_id, text=msg)




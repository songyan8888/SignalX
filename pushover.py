import os
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")


def send_pushover(message: str, title: str = "NotifyX", url: str = "") -> dict:
    """Send a push notification via Pushover. Returns the API response as dict."""
    payload = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "title": title,
    }
    if url:
        payload["url"] = url
        payload["url_title"] = "View Source"

    resp = requests.post(
        "https://api.pushover.net/1/messages.json",
        data=payload,
        timeout=10,
        verify=False,
    )
    return resp.json()

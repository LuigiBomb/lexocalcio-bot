import os
import sys
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

CUSTOM_EMOJI_ID = "5834548084742294874"


def validate_env():
    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")

    if missing:
        raise RuntimeError("Variabili ambiente mancanti: " + ", ".join(missing))


def send_test_message():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    text = (
        f'<a href="tg://emoji?id={CUSTOM_EMOJI_ID}">🔵</a> '
        f'Test emoji premium '
        f'<a href="tg://emoji?id={CUSTOM_EMOJI_ID}">🔵</a>'
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()
    print("Messaggio test inviato correttamente.")


def main():
    validate_env()
    send_test_message()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        sys.exit(1)

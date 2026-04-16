import os
import sys
import html
import requests
from datetime import datetime
from collections import defaultdict
from zoneinfo import ZoneInfo

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@LexoCalcio")
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")

ROME_TZ = ZoneInfo("Europe/Rome")

COMPETITIONS = {
    "SA": "🇮🇹 Serie A",
    "PL": "🏴 Premier League",
    "BL1": "🇩🇪 Bundesliga",
    "PD": "🇪🇸 LaLiga",
    "FL1": "🇫🇷 Ligue 1",
    "CL": "🏆 Champions League",
    "EL": "🏆 Europa League",
    "ECL": "🏆 Conference League",
    "CIT": "🇮🇹 Coppa Italia",
}

TEAM_EMOJIS = {
    "Inter": "⚫",
    "Roma": "🟡",
    "Torino": "🟤",
    "Napoli": "🔵",
    "Milan": "🔴",
    "Juventus": "⚪",
    "Lazio": "🔵",
    "Atalanta": "🔵",
    "Bologna": "🔴",
    "Fiorentina": "🟣",
    "Genoa": "🔴",
    "Cagliari": "🔴",
    "Parma": "🟡",
    "Verona": "🟡",
    "Lecce": "🟡",
    "Monza": "🔴",
    "Empoli": "🔵",
    "Udinese": "⚫",
    "Como": "🔵",
    "Pisa": "🔵",
    "Cremonese": "🔴",
    "Chelsea": "🔵",
    "Liverpool": "🔴",
    "Arsenal": "🔴",
    "Manchester City": "🔵",
    "Manchester United": "🔴",
    "Tottenham": "⚪",
    "Newcastle": "⚫",
    "Bayern": "🔴",
    "Dortmund": "🟡",
    "Leverkusen": "🔴",
    "RB Leipzig": "🔴",
    "Union Berlino": "🔴",
    "Colonia": "⚪",
    "St. Pauli": "🟤",
    "Real Madrid": "⚪",
    "Barcellona": "🔵",
    "Barcelona": "🔵",
    "Atletico Madrid": "🔴",
    "Valencia": "⚪",
    "Siviglia": "🔴",
    "Sevilla": "🔴",
    "Getafe": "🔵",
    "Athletic Club": "🔴",
    "Celta Vigo": "🔵",
    "Real Oviedo": "🔵",
    "Alavés": "🔵",
    "Osasuna": "🔴",
    "PSG": "🔵",
    "Marsiglia": "🔵",
    "Lione": "⚪",
    "Monaco": "🔴",
    "Nantes": "🟢",
    "Lorient": "🟠",
    "Le Havre": "🔵",
    "Auxerre": "🔵",
    "Metz": "🟣",
    "Angers": "⚫",
    "Paris FC": "🔵",
}

API_URL = "https://api.football-data.org/v4/matches"


def validate_env():
    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if not FOOTBALL_DATA_API_KEY:
        missing.append("FOOTBALL_DATA_API_KEY")

    if missing:
        raise RuntimeError("Variabili ambiente mancanti: " + ", ".join(missing))


def get_today_strings():
    now_rome = datetime.now(ROME_TZ)
    return now_rome.strftime("%Y-%m-%d"), now_rome.strftime("%d/%m/%Y")


def fetch_matches_for_today():
    day_api, _ = get_today_strings()

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_API_KEY,
    }

    params = {
        "dateFrom": day_api,
        "dateTo": day_api,
    }

    response = requests.get(API_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()
    matches = payload.get("matches", [])

    filtered = []
    for match in matches:
        code = match.get("competition", {}).get("code")
        if code in COMPETITIONS:
            filtered.append(match)

    return filtered


def to_rome_time(utc_date):
    dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
    return dt.astimezone(ROME_TZ).strftime("%H:%M")


def clean_team_name(name):
    replacements = {
        "FC Internazionale Milano": "Inter",
        "Inter Milan": "Inter",
        "AS Roma": "Roma",
        "Juventus FC": "Juventus",
        "AC Milan": "Milan",
        "SS Lazio": "Lazio",
        "SSC Napoli": "Napoli",
        "Atalanta BC": "Atalanta",
        "Parma Calcio 1913": "Parma",
        "Hellas Verona FC": "Verona",
        "Sevilla FC": "Siviglia",
        "1. FC Union Berlin": "Union Berlino",
        "1. FC Köln": "Colonia",
        "Olympique Lyonnais": "Lione",
        "Paris Saint-Germain FC": "PSG",
        "FC Bayern München": "Bayern",
        "FC Barcelona": "Barcellona",
    }
    return replacements.get(name, name)


def team_with_emoji(name):
    emoji = TEAM_EMOJIS.get(name, "⚪")
    return f"{emoji} {name}"


def esc(text):
    return html.escape(str(text), quote=True)


def build_message(matches):
    _, day_msg = get_today_strings()

    lines = [
        "<b>Lexo Calcio ⚽</b>",
        "",
        f"📅 <b><u>Palinsesto {esc(day_msg)}</u></b>",
        ""
    ]

    grouped = defaultdict(list)
    for match in matches:
        code = match.get("competition", {}).get("code")
        grouped[code].append(match)

    order = ["SA", "PL", "BL1", "PD", "FL1", "CL", "EL", "ECL", "CIT"]

    shown_any = False

    for code in order:
        section_matches = grouped.get(code, [])
        if not section_matches:
            continue

        shown_any = True
        section_matches.sort(key=lambda m: m.get("utcDate", ""))

        lines.append(f"<b>{esc(COMPETITIONS[code])}</b>")
        lines.append("")

        quote_lines = []
        for match in section_matches:
            kickoff = to_rome_time(match["utcDate"])
            home = clean_team_name(match.get("homeTeam", {}).get("name", "Casa"))
            away = clean_team_name(match.get("awayTeam", {}).get("name", "Trasferta"))

            quote_lines.append(esc(kickoff))
            quote_lines.append(f"{esc(team_with_emoji(home))} 🆚 {esc(team_with_emoji(away))}")
            quote_lines.append("")

        while quote_lines and quote_lines[-1] == "":
            quote_lines.pop()

        lines.append("<blockquote>" + "\n".join(quote_lines) + "</blockquote>")
        lines.append("")

    if not shown_any:
        lines.append("<blockquote>Nessuna partita trovata oggi per le competizioni selezionate.</blockquote>")
        lines.append("")

    lines.append("🌟 @LexoCalcio")
    lines.append("💬 @LexoCalcioChat")
    lines.append("🌟 @LexoSport")

    return "\n".join(lines).strip()


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()


def main():
    validate_env()
    matches = fetch_matches_for_today()
    message = build_message(matches)
    send_telegram_message(message)
    print("Messaggio pubblicato correttamente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        sys.exit(1)

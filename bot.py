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
OVERRIDE_DATE = os.getenv("OVERRIDE_DATE", "").strip()

ROME_TZ = ZoneInfo("Europe/Rome")

# Competizioni tenute sul piano free più affidabile
COMPETITIONS = {
    "SA": "🇮🇹 Serie A",
    "PL": "🏴 Premier League",
    "BL1": "🇩🇪 Bundesliga",
    "PD": "🇪🇸 LaLiga",
    "FL1": "🇫🇷 Ligue 1",
    "CL": "🏆 Champions League",
}

API_BASE_URL = "https://api.football-data.org/v4/competitions"

TEAM_EMOJIS = {
    # Serie A 2025-26
    "Atalanta": "🔵",
    "Bologna": "🔴",
    "Cagliari": "🔴",
    "Como": "🔵",
    "Cremonese": "🔴",
    "Fiorentina": "🟣",
    "Genoa": "🔴",
    "Inter": "⚫",
    "Juventus": "⚪",
    "Lazio": "🔵",
    "Lecce": "🟡",
    "Milan": "🔴",
    "Napoli": "🔵",
    "Parma": "🟡",
    "Pisa": "🔵",
    "Roma": "🟡",
    "Sassuolo": "🟢",
    "Torino": "🟤",
    "Udinese": "⚫",
    "Verona": "🟡",

    # Premier League 2025-26
    "Arsenal": "🔴",
    "Aston Villa": "🟣",
    "Bournemouth": "🔴",
    "Brentford": "🔴",
    "Brighton": "🔵",
    "Brighton & Hove Albion": "🔵",
    "Burnley": "🟣",
    "Chelsea": "🔵",
    "Crystal Palace": "🔴",
    "Everton": "🔵",
    "Fulham": "⚪",
    "Leeds": "⚪",
    "Leeds United": "⚪",
    "Liverpool": "🔴",
    "Manchester City": "🔵",
    "Manchester United": "🔴",
    "Newcastle": "⚫",
    "Newcastle United": "⚫",
    "Nottingham Forest": "🔴",
    "Sunderland": "🔴",
    "Tottenham": "⚪",
    "West Ham": "🟣",
    "West Ham United": "🟣",
    "Wolverhampton": "🟠",
    "Wolverhampton Wanderers": "🟠",

    # Bundesliga 2025-26
    "Augsburg": "⚪",
    "Bayern": "🔴",
    "Bayern Munich": "🔴",
    "Bayer Leverkusen": "🔴",
    "Leverkusen": "🔴",
    "Borussia Dortmund": "🟡",
    "Dortmund": "🟡",
    "Borussia Mönchengladbach": "⚫",
    "M'gladbach": "⚫",
    "Eintracht Frankfurt": "⚪",
    "Frankfurt": "⚪",
    "Freiburg": "⚫",
    "Heidenheim": "🔴",
    "Hoffenheim": "🔵",
    "Hamburger SV": "🔵",
    "Hamburgo": "🔵",
    "Köln": "⚪",
    "Colonia": "⚪",
    "Mainz": "🔴",
    "RB Leipzig": "🔴",
    "Leipzig": "🔴",
    "St. Pauli": "🟤",
    "Stuttgart": "🔴",
    "Union Berlin": "🔴",
    "Union Berlino": "🔴",
    "Werder Bremen": "🟢",
    "Bremen": "🟢",
    "Wolfsburg": "🟢",

    # LaLiga 2025-26
    "Alavés": "🔵",
    "Athletic Club": "🔴",
    "Athletic Bilbao": "🔴",
    "Atlético Madrid": "🔴",
    "Atletico Madrid": "🔴",
    "Barcelona": "🔵",
    "Barcellona": "🔵",
    "Celta Vigo": "🔵",
    "Celta": "🔵",
    "Elche": "🟢",
    "Espanyol": "🔵",
    "Getafe": "🔵",
    "Girona": "🔴",
    "Levante": "🔵",
    "Mallorca": "🔴",
    "Osasuna": "🔴",
    "Oviedo": "🔵",
    "Real Oviedo": "🔵",
    "Rayo Vallecano": "🔴",
    "Real Betis": "🟢",
    "Betis": "🟢",
    "Real Madrid": "⚪",
    "Real Sociedad": "🔵",
    "Sociedad": "🔵",
    "Sevilla": "🔴",
    "Siviglia": "🔴",
    "Valencia": "⚪",
    "Villarreal": "🟡",

    # Ligue 1 2025-26
    "Angers": "⚫",
    "Auxerre": "🔵",
    "Brest": "🔴",
    "Le Havre": "🔵",
    "Lens": "🟡",
    "Lille": "🔴",
    "Lorient": "🟠",
    "Lyon": "⚪",
    "Lione": "⚪",
    "Marseille": "🔵",
    "Marsiglia": "🔵",
    "Metz": "🟣",
    "Monaco": "🔴",
    "Nantes": "🟢",
    "Nice": "🔴",
    "Paris FC": "🔵",
    "Paris Saint-Germain": "🔵",
    "PSG": "🔵",
    "Rennes": "🔴",
    "Strasbourg": "🔵",
    "Toulouse": "🟣",
}


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


def get_target_date_strings():
    if OVERRIDE_DATE:
        dt = datetime.strptime(OVERRIDE_DATE, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d"), dt.strftime("%d/%m/%Y")

    now_rome = datetime.now(ROME_TZ)
    return now_rome.strftime("%Y-%m-%d"), now_rome.strftime("%d/%m/%Y")


def fetch_matches_for_day():
    day_api, _ = get_target_date_strings()

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_API_KEY,
    }

    all_matches = []

    for code in COMPETITIONS.keys():
        url = f"{API_BASE_URL}/{code}/matches"
        params = {
            "dateFrom": day_api,
            "dateTo": day_api,
        }

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        payload = response.json()
        matches = payload.get("matches", [])
        all_matches.extend(matches)

    return all_matches


def to_rome_time(utc_date):
    dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
    return dt.astimezone(ROME_TZ).strftime("%H:%M")


def clean_team_name(name):
    replacements = {
        # Italia
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
        "US Sassuolo Calcio": "Sassuolo",
        "Pisa Sporting Club": "Pisa",
        "US Cremonese": "Cremonese",

        # Inghilterra
        "Arsenal FC": "Arsenal",
        "Aston Villa FC": "Aston Villa",
        "AFC Bournemouth": "Bournemouth",
        "Brentford FC": "Brentford",
        "Brighton & Hove Albion FC": "Brighton",
        "Burnley FC": "Burnley",
        "Chelsea FC": "Chelsea",
        "Crystal Palace FC": "Crystal Palace",
        "Everton FC": "Everton",
        "Fulham FC": "Fulham",
        "Leeds United FC": "Leeds",
        "Liverpool FC": "Liverpool",
        "Manchester City FC": "Manchester City",
        "Manchester United FC": "Manchester United",
        "Newcastle United FC": "Newcastle",
        "Nottingham Forest FC": "Nottingham Forest",
        "Sunderland AFC": "Sunderland",
        "Tottenham Hotspur FC": "Tottenham",
        "West Ham United FC": "West Ham",
        "Wolverhampton Wanderers FC": "Wolverhampton",

        # Germania
        "FC Bayern München": "Bayern",
        "Bayer 04 Leverkusen": "Bayer Leverkusen",
        "BV Borussia 09 Dortmund": "Borussia Dortmund",
        "Borussia Mönchengladbach": "M'gladbach",
        "Eintracht Frankfurt": "Eintracht Frankfurt",
        "Sport-Club Freiburg": "Freiburg",
        "1. FC Heidenheim 1846": "Heidenheim",
        "TSG 1899 Hoffenheim": "Hoffenheim",
        "Hamburger SV": "Amburgo",
        "1. FC Köln": "Colonia",
        "1. FSV Mainz 05": "Mainz",
        "RB Leipzig": "RB Leipzig",
        "FC St. Pauli 1910": "St. Pauli",
        "VfB Stuttgart": "Stuttgart",
        "1. FC Union Berlin": "Union Berlino",
        "SV Werder Bremen": "Werder Bremen",
        "VfL Wolfsburg": "Wolfsburg",
        "FC Augsburg": "Augsburg",

        # Spagna
        "Deportivo Alavés": "Alavés",
        "Athletic Club": "Athletic Club",
        "Club Atlético de Madrid": "Atletico Madrid",
        "FC Barcelona": "Barcellona",
        "RC Celta de Vigo": "Celta Vigo",
        "Elche CF": "Elche",
        "RCD Espanyol de Barcelona": "Espanyol",
        "Getafe CF": "Getafe",
        "Girona FC": "Girona",
        "Levante UD": "Levante",
        "RCD Mallorca": "Mallorca",
        "CA Osasuna": "Osasuna",
        "Real Oviedo": "Oviedo",
        "Rayo Vallecano de Madrid": "Rayo Vallecano",
        "Real Betis Balompié": "Betis",
        "Real Madrid CF": "Real Madrid",
        "Real Sociedad de Fútbol": "Real Sociedad",
        "Sevilla FC": "Siviglia",
        "Valencia CF": "Valencia",
        "Villarreal CF": "Villarreal",

        # Francia
        "Angers SCO": "Angers",
        "AJ Auxerre": "Auxerre",
        "Stade Brestois 29": "Brest",
        "Le Havre AC": "Le Havre",
        "RC Lens": "Lens",
        "LOSC Lille": "Lille",
        "FC Lorient": "Lorient",
        "Olympique Lyonnais": "Lione",
        "Olympique de Marseille": "Marsiglia",
        "FC Metz": "Metz",
        "AS Monaco FC": "Monaco",
        "FC Nantes": "Nantes",
        "OGC Nice": "Nice",
        "Paris FC": "Paris FC",
        "Paris Saint-Germain FC": "PSG",
        "Stade Rennais FC 1901": "Rennes",
        "RC Strasbourg Alsace": "Strasbourg",
        "Toulouse FC": "Toulouse",
    }
    return replacements.get(name, name)


def home_team_with_emoji(name):
    emoji = TEAM_EMOJIS.get(name, "⚪")
    return f"{emoji} {name}"


def away_team_with_emoji(name):
    emoji = TEAM_EMOJIS.get(name, "⚪")
    return f"{name} {emoji}"


def esc(text):
    return html.escape(str(text), quote=True)


def build_message(matches):
    _, day_msg = get_target_date_strings()

    lines = [
        f"📅 <b><u>Palinsesto {esc(day_msg)}</u></b>",
        ""
    ]

    grouped = defaultdict(list)
    for match in matches:
        code = match.get("competition", {}).get("code")
        grouped[code].append(match)

    order = ["SA", "PL", "BL1", "PD", "FL1", "CL"]

    shown_any = False

    for code in order:
        section_matches = grouped.get(code, [])
        if not section_matches:
            continue

        shown_any = True
        section_matches.sort(key=lambda m: m.get("utcDate", ""))

        lines.append(f"<i>{esc(COMPETITIONS[code])}</i>")
        lines.append("")

        quote_lines = []
        for match in section_matches:
            kickoff = to_rome_time(match["utcDate"])
            home = clean_team_name(match.get("homeTeam", {}).get("name", "Casa"))
            away = clean_team_name(match.get("awayTeam", {}).get("name", "Trasferta"))

            quote_lines.append(esc(kickoff))
            quote_lines.append(
                f"{esc(home_team_with_emoji(home))} 🆚 {esc(away_team_with_emoji(away))}"
            )
            quote_lines.append("")

        while quote_lines and quote_lines[-1] == "":
            quote_lines.pop()

        lines.append("<blockquote>" + "\n".join(quote_lines) + "</blockquote>")
        lines.append("")

    if not shown_any:
        return None

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
    matches = fetch_matches_for_day()

    print(f"Data usata: {get_target_date_strings()[0]}")
    print(f"Match trovati dopo il filtro: {len(matches)}")

    for m in matches[:30]:
        comp = m.get("competition", {}).get("code")
        home = m.get("homeTeam", {}).get("name")
        away = m.get("awayTeam", {}).get("name")
        date = m.get("utcDate")
        print(comp, date, home, "vs", away)

    message = build_message(matches)

    if not message:
        print("Nessuna partita trovata: non pubblico nulla.")
        return

    send_telegram_message(message)
    print("Messaggio pubblicato correttamente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        sys.exit(1)

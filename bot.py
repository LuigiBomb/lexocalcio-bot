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
    # Serie A
    "Inter": "⚫",
    "Napoli": "🔵",
    "Milan": "🔴",
    "Juventus": "⚪",
    "Como": "🔵",
    "Roma": "🟡",
    "Atalanta": "🔵",
    "Bologna": "🔴",
    "Lazio": "🔵",
    "Udinese": "⚫",
    "Sassuolo": "🟢",
    "Torino": "🟤",
    "Genoa": "🔴",
    "Parma": "🟡",
    "Fiorentina": "🟣",
    "Cagliari": "🔴",
    "Cremonese": "🔴",
    "Lecce": "🟡",
    "Verona": "🔵",
    "Pisa": "🔵",

    # Premier League
    "Arsenal": "🔴",
    "Man. City": "🔵",
    "Man. United": "🔴",
    "Aston Villa": "🟣",
    "Liverpool": "🔴",
    "Chelsea": "🔵",
    "Brentford": "🔴",
    "Everton": "🔵",
    "Brighton": "🔵",
    "Sunderland": "🔴",
    "Bournemouth": "🔴",
    "Fulham": "⚪",
    "Crystal Palace": "🔵",
    "Newcastle": "⚫",
    "Leeds": "🟡",
    "Nottingham Forest": "🔴",
    "West Ham": "🟣",
    "Tottenham": "⚪",
    "Burnley": "🟣",
    "Wolverhampton": "🟡",

    # Bundesliga
    "Bayern Monaco": "🔴",
    "Dortmund": "🟡",
    "Stoccarda": "🔴",
    "RB Lipsia": "🔴",
    "Leverkusen": "🔴",
    "Hoffenheim": "🔵",
    "Eintracht": "⚪",
    "Friburgo": "⚫",
    "Mainz": "🔴",
    "Augsburg": "🔴",
    "Union Berlino": "🔴",
    "Amburgo": "🔵",
    "Colonia": "⚪",
    "Borussia M'Gladbach": "⚫",
    "Werder Brema": "🟢",
    "St. Pauli": "🟤",
    "Wolfsburg": "🟢",
    "Heidenheim": "🔴",

    # LaLiga
    "Barcellona": "🔵",
    "Real Madrid": "⚪",
    "Atlético Madrid": "🔴",
    "Villarreal": "🟡",
    "Betis": "🟢",
    "Celta Vigo": "🔵",
    "Real Sociedad": "🔵",
    "Getafe": "🔵",
    "Osasuna": "🔴",
    "Espanyol": "🔵",
    "Girona": "🔴",
    "Athletic Club": "🔴",
    "Rayo Vallecano": "🔴",
    "Valencia": "⚪",
    "Mallorca": "🔴",
    "Siviglia": "🔴",
    "Alavés": "🔵",
    "Elche": "🔴",
    "Levante": "🔵",
    "Real Oviedo": "🔵",

    # Ligue 1
    "PSG": "🔵",
    "Lens": "🔴",
    "Lilla": "🔴",
    "Marsiglia": "🔵",
    "Lione": "⚪",
    "Rennes": "🔴",
    "Monaco": "🔴",
    "Strasburgo": "🔵",
    "Lorient": "🟠",
    "Tolosa": "🟣",
    "Brest": "🔴",
    "Paris": "🔵",
    "Angers": "⚫",
    "Le Havre": "🔵",
    "Nizza": "🔴",
    "Auxerre": "🔵",
    "Nantes": "🟢",
    "Metz": "🔴",
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
        # Serie A
        "FC Internazionale Milano": "Inter",
        "Inter Milan": "Inter",
        "AS Roma": "Roma",
        "Juventus FC": "Juventus",
        "AC Milan": "Milan",
        "SS Lazio": "Lazio",
        "SSC Napoli": "Napoli",
        "Atalanta BC": "Atalanta",
        "Bologna FC 1909": "Bologna",
        "Udinese Calcio": "Udinese",
        "Torino FC": "Torino",
        "Genoa CFC": "Genoa",
        "Parma Calcio 1913": "Parma",
        "ACF Fiorentina": "Fiorentina",
        "Cagliari Calcio": "Cagliari",
        "US Cremonese": "Cremonese",
        "US Lecce": "Lecce",
        "Hellas Verona FC": "Verona",
        "Pisa Sporting Club": "Pisa",
        "Como 1907": "Como",
        "US Sassuolo Calcio": "Sassuolo",

        # Premier League
        "Manchester City FC": "Man. City",
        "Manchester United FC": "Man. United",
        "Brighton & Hove Albion FC": "Brighton",
        "AFC Bournemouth": "Bournemouth",
        "Newcastle United FC": "Newcastle",
        "Tottenham Hotspur FC": "Tottenham",
        "West Ham United FC": "West Ham",
        "Wolverhampton Wanderers FC": "Wolverhampton",
        "Leeds United FC": "Leeds",
        "Sunderland AFC": "Sunderland",
        "Arsenal FC": "Arsenal",
        "Liverpool FC": "Liverpool",
        "Chelsea FC": "Chelsea",
        "Everton FC": "Everton",
        "Fulham FC": "Fulham",
        "Crystal Palace FC": "Crystal Palace",
        "Burnley FC": "Burnley",
        "Nottingham Forest FC": "Nottingham Forest",
        "Aston Villa FC": "Aston Villa",
        "Brentford FC": "Brentford",

        # LaLiga
        "FC Barcelona": "Barcellona",
        "Real Madrid CF": "Real Madrid",
        "Club Atlético de Madrid": "Atlético Madrid",
        "Atlético de Madrid": "Atlético Madrid",
        "Villarreal CF": "Villarreal",
        "Real Betis Balompié": "Betis",
        "RC Celta de Vigo": "Celta Vigo",
        "Real Sociedad de Fútbol": "Real Sociedad",
        "Getafe CF": "Getafe",
        "CA Osasuna": "Osasuna",
        "RCD Espanyol de Barcelona": "Espanyol",
        "Girona FC": "Girona",
        "Athletic Club": "Athletic Club",
        "Rayo Vallecano de Madrid": "Rayo Vallecano",
        "Valencia CF": "Valencia",
        "RCD Mallorca": "Mallorca",
        "Sevilla FC": "Siviglia",
        "Deportivo Alavés": "Alavés",
        "Elche CF": "Elche",
        "Levante UD": "Levante",
        "Real Oviedo": "Real Oviedo",

        # Bundesliga
        "FC Bayern München": "Bayern Monaco",
        "Borussia Dortmund": "Dortmund",
        "VfB Stuttgart": "Stoccarda",
        "RB Leipzig": "RB Lipsia",
        "Bayer 04 Leverkusen": "Leverkusen",
        "TSG 1899 Hoffenheim": "Hoffenheim",
        "Eintracht Frankfurt": "Eintracht",
        "SC Freiburg": "Friburgo",
        "1. FSV Mainz 05": "Mainz",
        "FC Augsburg": "Augsburg",
        "1. FC Union Berlin": "Union Berlino",
        "Hamburger SV": "Amburgo",
        "1. FC Köln": "Colonia",
        "Borussia Mönchengladbach": "Borussia M'Gladbach",
        "SV Werder Bremen": "Werder Brema",
        "FC St. Pauli": "St. Pauli",
        "VfL Wolfsburg": "Wolfsburg",
        "1. FC Heidenheim 1846": "Heidenheim",

        # Ligue 1
        "Paris Saint-Germain FC": "PSG",
        "RC Lens": "Lens",
        "LOSC Lille": "Lilla",
        "Olympique de Marseille": "Marsiglia",
        "Olympique Lyonnais": "Lione",
        "Stade Rennais FC": "Rennes",
        "AS Monaco FC": "Monaco",
        "RC Strasbourg Alsace": "Strasburgo",
        "FC Lorient": "Lorient",
        "Toulouse FC": "Tolosa",
        "Stade Brestois 29": "Brest",
        "Paris FC": "Paris",
        "Angers SCO": "Angers",
        "Le Havre AC": "Le Havre",
        "OGC Nice": "Nizza",
        "AJ Auxerre": "Auxerre",
        "FC Nantes": "Nantes",
        "FC Metz": "Metz",
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

        lines.append(f"<b>{esc(COMPETITIONS[code])}</b>")
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

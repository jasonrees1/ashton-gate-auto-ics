print("SCRAPER STARTED")

from datetime import datetime, timedelta
import os
import pytz
import requests
import json
from bs4 import BeautifulSoup

# UK timezone
uk_tz = pytz.timezone("Europe/London")
today_uk = datetime.now(uk_tz).date()
print("Today's UK date:", today_uk)


# ---------------------------------------------------------
#  BRISTOL CITY FIXTURES (API-FOOTBALL)
# ---------------------------------------------------------
def fetch_bristol_city_fixtures():
    print("\n=== Fetching Bristol City Fixtures from API-Football ===")

    api_key = os.environ.get("API_FOOTBALL_KEY")
    if not api_key:
        print("No API_FOOTBALL_KEY found in environment")
        return []

    team_id = 52  # Bristol City

    from_date = today_uk.strftime("%Y-%m-%d")
    to_date = (today_uk.replace(year=today_uk.year + 1)).strftime("%Y-%m-%d")

    url = "https://v3.football.api-sports.io/fixtures"
    params = {"team": team_id, "from": from_date, "to": to_date}
    headers = {"x-apisports-key": api_key}

    response = requests.get(url, headers=headers, params=params)
    print("HTTP status:", response.status_code)

    try:
        data = response.json()
    except:
        return []

    matches = data.get("response", [])
    fixtures = []

    for m in matches:
        try:
            fixture = m["fixture"]
            teams = m["teams"]
            venue = fixture.get("venue", {}) or {}

            home_team = teams["home"]["name"]
            away_team = teams["away"]["name"]
            venue_name = venue.get("name", "") or ""

            if home_team.lower() != "bristol city":
                continue
            if "ashton gate" not in venue_name.lower():
                continue

            kickoff_str = fixture["date"]
            kickoff_dt = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            kickoff_uk = kickoff_dt.astimezone(uk_tz)

            if kickoff_uk.date() < today_uk:
                continue

            fixtures.append({
                "id": f"football-{fixture['id']}",
                "title": f"{home_team} vs {away_team}",
                "start": kickoff_uk.isoformat(),
                "category": "football"
            })

        except Exception as e:
            print("Error parsing fixture:", e)

    print("Total future HOME fixtures:", len(fixtures))
    return fixtures


# ---------------------------------------------------------
#  BRISTOL BEARS FIXTURES (PREMIERSHIP RUGBY JSON)
# ---------------------------------------------------------
def fetch_bristol_bears_fixtures():
    print("\n=== Fetching Bristol Bears Fixtures (Premiership Rugby JSON) ===")

    url = "https://www.premiershiprugby.com/wp-json/wp/v2/clubs/bristol-bears/fixtures"

    response = requests.get(url)
    print("HTTP status:", response.status_code)

    try:
        data = response.json()
    except:
        return []

    fixtures = []

    for e in data:
        try:
            title = e.get("title", {}).get("rendered", "")
            venue = e.get("acf", {}).get("venue", "")
            date_str = e.get("acf", {}).get("date", "")
            time_str = e.get("acf", {}).get("time", "")

            if "ashton gate" not in venue.lower():
                continue

            if not date_str:
                continue

            dt_str = f"{date_str} {time_str or '15:00'}"
            kickoff_uk = uk_tz.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))

            if kickoff_uk.date() < today_uk:
                continue

            fixtures.append({
                "id": f"rugby-{int(kickoff_uk.timestamp())}",
                "title": title,
                "start": kickoff_uk.isoformat(),
                "category": "rugby"
            })

        except Exception as e:
            print("Error parsing rugby fixture:", e)

    print("Total future HOME rugby fixtures:", len(fixtures))
    return fixtures


# ---------------------------------------------------------
#  ASHTON GATE HTML SCRAPER (OFFICIAL WHAT'S ON)
# ---------------------------------------------------------
def fetch_ashton_gate_html():
    print("\n=== Fetching Ashton Gate HTML Events ===")

    url = "https://www.ashtongatestadium.co.uk/whats-on/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    print("HTTP status:", response.status_code)

    if response.status_code != 200:
        print("Ashton Gate HTML blocked or unavailable")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select(".event-card")

    events = []

    for card in cards:
        try:
            title = card.select_one(".event-card__title").get_text(strip=True)
            date_text = card.select_one(".event-card__date").get_text(strip=True)

            dt = datetime.strptime(date_text, "%d %B %Y")
            kickoff_uk = uk_tz.localize(dt.replace(hour=19, minute=0))

            if kickoff_uk.date() < today_uk:
                continue

            events.append({
                "id": f"ashton-{int(kickoff_uk.timestamp())}",
                "title": title,
                "start": kickoff_uk.isoformat(),
                "category": "ashton"
            })

        except Exception as e:
            print("Error parsing Ashton Gate HTML:", e)

    print("Total Ashton Gate HTML events:", len(events))
    return events




# ---------------------------------------------------------
#  TICKETMASTER DISCOVERY API
# ---------------------------------------------------------
def fetch_ticketmaster_events():
    print("\n=== Fetching Ticketmaster Events ===")

    api_key = os.environ.get("TICKETMASTER_KEY")
    if not api_key:
        print("No TICKETMASTER_KEY found")
        return []

    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "venueId": "KovZpZA7AAEA",
        "apikey": api_key
    }

    response = requests.get(url, params=params)
    print("HTTP status:", response.status_code)

    try:
        data = response.json()
    except:
        return []

    events_raw = data.get("_embedded", {}).get("events", [])
    events = []

    for e in events_raw:
        try:
            title = e.get("name", "")
            start_str = e.get("dates", {}).get("start", {}).get("dateTime", None)
            if not start_str:
                continue

            kickoff_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            kickoff_uk = kickoff_dt.astimezone(uk_tz)

            if kickoff_uk.date() < today_uk:
                continue

            events.append({
                "id": f"tm-{e['id']}",
                "title": title,
                "start": kickoff_uk.isoformat(),
                "category": "ticketmaster"
            })

        except Exception as e:
            print("Error parsing Ticketmaster event:", e)

    print("Total Ticketmaster events:", len(events))
    return events


# ---------------------------------------------------------
#  ICS GENERATION
# ---------------------------------------------------------
def generate_ics(events):
    print("\n=== Generating ICS file ===")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Ashton Gate Auto Feed//EN"
    ]

    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for e in events:
        start_dt = datetime.fromisoformat(e["start"])
        end_dt = start_dt + timedelta(hours=2)

        dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
        dtend = end_dt.strftime("%Y%m%dT%H%M%S")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{e['id']}@ashton-gate-auto",
            f"DTSTAMP:{now_utc}",
            f"DTSTART;TZID=Europe/London:{dtstart}",
            f"DTEND;TZID=Europe/London:{dtend}",
            f"SUMMARY:{e['title']}",
            "LOCATION:Ashton Gate Stadium",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    return "\n".join(lines)


# ---------------------------------------------------------
#  MAIN EXECUTION
# ---------------------------------------------------------
print("\n=== Running main scraper ===")

football = fetch_bristol_city_fixtures()
rugby = fetch_bristol_bears_fixtures()
ashton_html = fetch_ashton_gate_html()
ticketmaster = fetch_ticketmaster_events()

events = football + rugby + ashton_html + ticketmaster

print("Total events being written to events.json:", len(events))

with open("events.json", "w") as f:
    json.dump(events, f, indent=2)

print("events.json written successfully")

ics_content = generate_ics(events)
with open("calendar.ics", "w") as f:
    f.write(ics_content)

print("calendar.ics written successfully")
print("SCRAPER FINISHED")

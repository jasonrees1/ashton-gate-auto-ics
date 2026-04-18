print("SCRAPER STARTED")

from datetime import datetime, timedelta
import os
import pytz
import requests
import json

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

    print("Requesting:", url, params)
    response = requests.get(url, headers=headers, params=params)
    print("HTTP status:", response.status_code)

    try:
        data = response.json()
    except Exception as e:
        print("Error decoding JSON:", e)
        return []

    matches = data.get("response", [])
    print("Total fixtures from API-Football:", len(matches))

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
#  BRISTOL BEARS FIXTURES (ESPN RUGBY API)
# ---------------------------------------------------------
def fetch_bristol_bears_fixtures():
    print("\n=== Fetching Bristol Bears Fixtures (ESPN API) ===")

    url = "https://site.api.espn.com/apis/site/v2/sports/rugby/eng.1/teams/bristol-bears/schedule"

    print("Requesting:", url)
    response = requests.get(url)
    print("Rugby HTTP status:", response.status_code)

    try:
        data = response.json()
    except Exception as e:
        print("Error decoding ESPN Rugby JSON:", e)
        return []

    events = data.get("events", [])
    print("Total rugby fixtures returned:", len(events))

    fixtures = []

    for e in events:
        try:
            competitions = e.get("competitions", [{}])[0]
            venue = competitions.get("venue", {}).get("fullName", "")
            competitors = competitions.get("competitors", [])

            home = next((c["team"]["displayName"] for c in competitors if c["homeAway"] == "home"), "")
            away = next((c["team"]["displayName"] for c in competitors if c["homeAway"] == "away"), "")

            if home.lower() != "bristol bears":
                continue
            if "ashton gate" not in venue.lower():
                continue

            kickoff_str = competitions.get("date")
            kickoff_dt = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            kickoff_uk = kickoff_dt.astimezone(uk_tz)

            if kickoff_uk.date() < today_uk:
                continue

            fixtures.append({
                "id": f"rugby-{int(kickoff_uk.timestamp())}",
                "title": f"{home} vs {away}",
                "start": kickoff_uk.isoformat(),
                "category": "rugby"
            })

        except Exception as e:
            print("Error parsing rugby fixture:", e)

    print("Total future HOME rugby fixtures:", len(fixtures))
    return fixtures


# ---------------------------------------------------------
#  ASHTON GATE EVENTS (EVENTBRITE API)
# ---------------------------------------------------------
def fetch_ashton_gate_events():
    print("\n=== Fetching Ashton Gate Events from Eventbrite ===")

    token = os.environ.get("EVENTBRITE_TOKEN")
    if not token:
        print("No EVENTBRITE_TOKEN found in environment")
        return []

    url = "https://www.eventbriteapi.com/v3/events/search/"
    params = {
        "q": "Ashton Gate",
        "location.address": "Bristol",
        "expand": "venue",
        "page_size": 50
    }
    headers = {"Authorization": f"Bearer {token}"}

    print("Requesting:", url)
    response = requests.get(url, headers=headers, params=params)
    print("Eventbrite HTTP status:", response.status_code)

    try:
        data = response.json()
    except Exception as e:
        print("Error decoding Eventbrite JSON:", e)
        return []

    events_raw = data.get("events", [])
    print("Eventbrite events returned:", len(events_raw))

    events = []

    for e in events_raw:
        try:
            venue = e.get("venue", {})
            venue_name = venue.get("name", "") or ""

            if "ashton gate" not in venue_name.lower():
                continue

            name = e.get("name", {}).get("text", "Event")
            start_str = e.get("start", {}).get("utc", None)
            if not start_str:
                continue

            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            start_uk = start_dt.astimezone(uk_tz)

            if start_uk.date() < today_uk:
                continue

            events.append({
                "id": f"event-{e['id']}",
                "title": name,
                "start": start_uk.isoformat(),
                "category": "event"
            })

        except Exception as e:
            print("Error parsing Eventbrite event:", e)

    print("Total future Ashton Gate events:", len(events))
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
events_api = fetch_ashton_gate_events()

events = football + rugby + events_api

print("Total events being written to events.json:", len(events))

with open("events.json", "w") as f:
    json.dump(events, f, indent=2)

print("events.json written successfully")

ics_content = generate_ics(events)
with open("calendar.ics", "w") as f:
    f.write(ics_content)

print("calendar.ics written successfully")
print("SCRAPER FINISHED")

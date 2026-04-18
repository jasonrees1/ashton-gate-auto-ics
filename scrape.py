print("SCRAPER STARTED")

from datetime import datetime
import os
import pytz
import requests
from bs4 import BeautifulSoup  # you can keep or remove later
import json


# UK timezone
uk_tz = pytz.timezone("Europe/London")
today_uk = datetime.now(uk_tz).date()
print("Today's UK date:", today_uk)


# ---------------------------------------------------------
#  BRISTOL CITY FIXTURES (BBC SPORT)
# ---------------------------------------------------------
def fetch_bristol_city_fixtures():
    print("\n=== Fetching Bristol City Fixtures from API-Football ===")

    api_key = os.environ.get("API_FOOTBALL_KEY")
    if not api_key:
        print("No API_FOOTBALL_KEY found in environment")
        return []

    # Bristol City team ID in API-Football
    team_id = 48  # if this is wrong we can adjust, but it's the usual ID

    # Date range: today → 1 year ahead
    from_date = today_uk.strftime("%Y-%m-%d")
    to_date = (today_uk.replace(year=today_uk.year + 1)).strftime("%Y-%m-%d")

    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        "team": team_id,
        "from": from_date,
        "to": to_date,
    }
    headers = {
        "x-apisports-key": api_key
    }

    print("Requesting:", url, params)
    response = requests.get(url, headers=headers, params=params)
    print("HTTP status:", response.status_code)

    try:
        data = response.json()
    except Exception as e:
        print("Error decoding JSON:", e)
        return []

    if "response" not in data:
        print("Unexpected API-Football response structure")
        return []

    matches = data["response"]
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

            # HOME ONLY at Ashton Gate
            if home_team.lower() != "bristol city":
                continue
            if "ashton gate" not in venue_name.lower():
                continue

            kickoff_str = fixture["date"]  # ISO string
            kickoff_dt = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            kickoff_uk = kickoff_dt.astimezone(uk_tz)

            if kickoff_uk.date() < today_uk:
                continue

            fixtures.append({
                "id": fixture["id"],
                "home": home_team,
                "away": away_team,
                "kickoff": kickoff_uk.isoformat()
            })

        except Exception as e:
            print("Error parsing fixture:", e)

    print("Total future HOME fixtures (all competitions):", len(fixtures))
    return fixtures






# ---------------------------------------------------------
#  MAIN EXECUTION
# ---------------------------------------------------------
print("\n=== Running main scraper ===")

fixtures = fetch_bristol_city_fixtures()
print("Fixtures fetched:", len(fixtures))

events = []

for f in fixtures:
    events.append({
        "id": f"football-{f['id']}",
        "title": f"{f['home']} vs {f['away']}",
        "start": f["kickoff"],
        "category": "football"
    })

print("Total events being written to events.json:", len(events))

with open("events.json", "w") as f:
    json.dump(events, f, indent=2)

print("events.json written successfully")

with open("calendar.ics", "w") as f:
    f.write("BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Ashton Gate Auto Feed//EN\nEND:VCALENDAR\n")

print("calendar.ics written successfully")
print("SCRAPER FINISHED")

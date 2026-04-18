print("SCRAPER STARTED")

from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import json

# UK timezone
uk_tz = pytz.timezone("Europe/London")
today_uk = datetime.now(uk_tz).date()
print("Today's UK date:", today_uk)


# ---------------------------------------------------------
#  BRISTOL CITY FIXTURES (BBC SPORT)
# ---------------------------------------------------------
def fetch_bristol_city_fixtures():
    print("\n=== Fetching Bristol City Fixtures from BBC JSON API ===")

    url = "https://push.api.bbci.co.uk/batch?sport=football&team=bristol-city"
    print("Requesting:", url)

    response = requests.get(url)
    print("HTTP status:", response.status_code)

    data = response.json()

    # BBC JSON structure:
    # data["payload"][0]["body"]["fixtures"]["matches"]
    try:
        matches = data["payload"][0]["body"]["fixtures"]["matches"]
    except Exception as e:
        print("Error parsing JSON:", e)
        return []

    print("Total matches in JSON:", len(matches))

    fixtures = []

    for m in matches:
        try:
            # Extract basic fields
            event_id = m.get("id")
            home_team = m["homeTeam"]["name"]
            away_team = m["awayTeam"]["name"]
            venue = m.get("venue", {}).get("name", "")

            # Filter: HOME MATCHES ONLY at Ashton Gate
            if home_team.lower() != "bristol city":
                continue
            if "ashton gate" not in venue.lower():
                continue

            # Extract kickoff time
            # Example: "2026-08-12T14:00:00Z"
            kickoff_str = m["startTime"]
            kickoff_dt = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            kickoff_uk = kickoff_dt.astimezone(uk_tz)

            # Skip past fixtures
            if kickoff_uk.date() < today_uk:
                continue

            fixtures.append({
                "id": event_id,
                "home": home_team,
                "away": away_team,
                "kickoff": kickoff_uk.isoformat()
            })

        except Exception as e:
            print("Error parsing match:", e)

    print("Total future HOME fixtures:", len(fixtures))
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

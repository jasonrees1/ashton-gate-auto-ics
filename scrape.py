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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    print("HTTP status:", response.status_code)

    data = response.json()





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

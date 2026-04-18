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
    print("\n=== Fetching Bristol City Fixtures from BBC Sport ===")

    url = "https://www.bbc.co.uk/sport/football/teams/bristol-city/scores-fixtures"
    print("Requesting:", url)

    response = requests.get(url)
    print("HTTP status:", response.status_code)

    soup = BeautifulSoup(response.text, "html.parser")

    fixtures = []

    matches = soup.select("li[data-event-id]")
    print("Total matches found on page:", len(matches))

    for m in matches:
        try:
            # Date header above the fixture group
            date_header = m.find_previous("h3")
            if not date_header:
                continue

            date_str = date_header.get_text(strip=True)
            match_date = datetime.strptime(date_str, "%A %d %B %Y").date()

            # Skip past matches
            if match_date < today_uk:
                continue

            # Teams
            teams = m.select_one(".sp-c-fixture__teams")
            if not teams:
                continue

            home_el = teams.select_one(".sp-c-fixture__team--home .sp-c-fixture__team-name")
            away_el = teams.select_one(".sp-c-fixture__team--away .sp-c-fixture__team-name")
            if not home_el or not away_el:
                continue

            home = home_el.get_text(strip=True)
            away = away_el.get_text(strip=True)

            # Time (may be TBC)
            time_el = m.select_one(".sp-c-fixture__number--time")
            if time_el:
                kickoff_time = time_el.get_text(strip=True)
            else:
                kickoff_time = "15:00"  # default if TBC

            # Combine date + time into ISO
            kickoff_dt = uk_tz.localize(
                datetime.strptime(f"{date_str} {kickoff_time}", "%A %d %B %Y %H:%M")
            )
            kickoff_iso = kickoff_dt.isoformat()

            fixtures.append({
                "id": m["data-event-id"],
                "home": home,
                "away": away,
                "kickoff": kickoff_iso
            })

        except Exception as e:
            print("Error parsing match:", e)

    print("Total future fixtures:", len(fixtures))
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

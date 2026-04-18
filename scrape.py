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

    # BBC Sport now uses <div class="sp-c-fixture"> for each match
    matches = soup.select("div.sp-c-fixture")
    print("Total matches found on page:", len(matches))

    for m in matches:
        try:
            # Extract event ID
            event_id = m.get("data-event-id", None)
            if not event_id:
                continue

            # Extract date (from nearest h3 above)
            date_header = m.find_previous("h3")
            if not date_header:
                continue

            date_str = date_header.get_text(strip=True)
            match_date = datetime.strptime(date_str, "%A %d %B %Y").date()

            # Skip past matches
            if match_date < today_uk:
                continue

            # Extract teams
            team_names = m.select(".sp-c-fixture__team-name")
            if len(team_names) != 2:
                continue

            home = team_names[0].get_text(strip=True)
            away = team_names[1].get_text(strip=True)

            # Extract time
            time_el = m.select_one(".sp-c-fixture__number--time")
            kickoff_time = time_el.get_text(strip=True) if time_el else "15:00"

            # Combine date + time
            kickoff_dt = uk_tz.localize(
                datetime.strptime(f"{date_str} {kickoff_time}", "%A %d %B %Y %H:%M")
            )
            kickoff_iso = kickoff_dt.isoformat()

            fixtures.append({
                "id": event_id,
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

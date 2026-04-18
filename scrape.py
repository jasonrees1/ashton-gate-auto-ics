print("SCRAPER STARTED")

from datetime import datetime, date
import pytz
import requests
import os

API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
print("API key loaded:", "YES" if API_FOOTBALL_KEY else "NO")

def fetch_bristol_city_fixtures():
    print("\n=== Fetching Bristol City Fixtures ===")

    team_id = 55  # Bristol City
    start_season = 2026
    end_season = 2050

    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    all_fixtures = []

    # UK timezone for date-based filtering
    uk_tz = pytz.timezone("Europe/London")
    today_uk = datetime.now(uk_tz).date()
    print("Today's UK date:", today_uk)

    print("Season loop starting...")
    for season in range(start_season, end_season + 1):
        print(f"Requesting season {season}...")

        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&season={season}"
        response = requests.get(url, headers=headers).json()

        print("API response results:", response.get("results"))
        print("API response errors:", response.get("errors"))

        season_fixtures = response.get("response", [])
        print(f"Fixtures returned for season {season}: {len(season_fixtures)}")

        all_fixtures.extend(season_fixtures)

    print("\nTotal fixtures fetched before filtering:", len(all_fixtures))

    # Filter out fixtures before today's UK date
    future_fixtures = []
    for fixture in all_fixtures:
        kickoff_str = fixture["fixture"]["date"]  # ISO format
        kickoff_dt = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
        kickoff_uk = kickoff_dt.astimezone(uk_tz)

        if kickoff_uk.date() >= today_uk:
            future_fixtures.append(fixture)

    print("Total fixtures after filtering:", len(future_fixtures))

    # Sort by kickoff time
    future_fixtures.sort(
        key=lambda f: datetime.fromisoformat(
            f["fixture"]["date"].replace("Z", "+00:00")
        )
    )

    print("Returning fixtures:", len(future_fixtures))
    return future_fixtures


# MAIN EXECUTION
print("\n=== Running main scraper ===")

fixtures = fetch_bristol_city_fixtures()

print("\nFixtures fetched:", len(fixtures))

# Convert fixtures into events.json format
events = []

for f in fixtures:
    fixture_id = f["fixture"]["id"]
    home = f["teams"]["home"]["name"]
    away = f["teams"]["away"]["name"]
    kickoff = f["fixture"]["date"]

    events.append({
        "id": f"football-{fixture_id}",
        "title": f"{home} vs {away}",
        "start": kickoff,
        "category": "football"
    })

print("Total events being written to events.json:", len(events))

# Write events.json
import json
with open("events.json", "w") as f:
    json.dump(events, f, indent=2)

print("events.json written successfully")

# Write calendar.ics (empty for now — debug focus)
with open("calendar.ics", "w") as f:
    f.write("BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Ashton Gate Auto Feed//EN\nEND:VCALENDAR\n")

print("calendar.ics written successfully")

print("SCRAPER FINISHED")

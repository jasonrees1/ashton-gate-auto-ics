from datetime import datetime, date
import pytz
import requests
import os

API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")

def fetch_bristol_city_fixtures():
    team_id = 55  # Bristol City
    start_season = 2026
    end_season = 2050

    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    all_fixtures = []

    # UK timezone for date-based filtering
    uk_tz = pytz.timezone("Europe/London")
    today_uk = datetime.now(uk_tz).date()

    for season in range(start_season, end_season + 1):
        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&season={season}"
        response = requests.get(url, headers=headers).json()

        season_fixtures = response.get("response", [])
        all_fixtures.extend(season_fixtures)

    # Filter out fixtures before today's UK date
    future_fixtures = []
    for fixture in all_fixtures:
        kickoff_str = fixture["fixture"]["date"]  # ISO format
        kickoff_dt = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
        kickoff_uk = kickoff_dt.astimezone(uk_tz)

        if kickoff_uk.date() >= today_uk:
            future_fixtures.append(fixture)

    # Sort by kickoff time
    future_fixtures.sort(
        key=lambda f: datetime.fromisoformat(
            f["fixture"]["date"].replace("Z", "+00:00")
        )
    )

    return future_fixtures

import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from ics import Calendar, Event

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TZ = ZoneInfo(CONFIG["timezone"])

API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
EVENTBRITE_TOKEN = os.environ.get("EVENTBRITE_TOKEN")

def fetch_bristol_city():
    team_id = CONFIG["football"]["team_id"]
    next_n = CONFIG["football"]["next_fixtures"]

    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&next={next_n}"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}

    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()

    events = []
    for item in data.get("response", []):
        fixture = item["fixture"]
        teams = item["teams"]
        league = item["league"]

        dt = datetime.fromisoformat(fixture["date"].replace("Z", "+00:00")).astimezone(TZ)

        home = teams["home"]["name"]
        away = teams["away"]["name"]
        title = f"{home} vs {away} ({league['name']})"

        events.append({
            "title": title,
            "start": dt.isoformat(),
            "location": fixture.get("venue", {}).get("name", "Ashton Gate Stadium")
        })

    return events

def fetch_bristol_bears():
    url = "https://push.api.bbci.co.uk/batch?t=Sport%2Fteams%2Frugby-union%2Fbristol-bears"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()

    events = []
    fixtures = data["payload"][0]["body"]["fixtures"]

    for fx in fixtures:
        dt = datetime.fromisoformat(fx["startTime"]).astimezone(TZ)
        title = f"Bristol Bears vs {fx['opponent']}"
        events.append({
            "title": title,
            "start": dt.isoformat(),
            "location": "Ashton Gate Stadium" if fx["homeAway"] == "home" else fx["venue"]
        })

    return events

def fetch_ashton_gate_events():
    url = "https://www.eventbriteapi.com/v3/events/search/"
    params = {
        "location.address": CONFIG["events"]["city"],
        "q": CONFIG["events"]["venue"],
        "sort_by": "date",
        "start_date.range_start": datetime.now(TZ).isoformat()
    }
    headers = {"Authorization": f"Bearer {EVENTBRITE_TOKEN}"}

    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()

    events = []
    for ev in data.get("events", []):
        if not ev.get("start", {}).get("utc"):
            continue

        dt = datetime.fromisoformat(ev["start"]["utc"].replace("Z", "+00:00")).astimezone(TZ)

        events.append({
            "title": ev["name"]["text"],
            "start": dt.isoformat(),
            "location": CONFIG["events"]["venue"]
        })

    return events

def generate_ics(events):
    cal = Calendar()
    for ev in events:
        e = Event()
        e.name = ev["title"]
        e.begin = ev["start"]
        e.location = ev["location"]
        cal.events.add(e)

    with open(CONFIG["output"]["ics_file"], "w", encoding="utf-8") as f:
        f.writelines(cal)

def main():
    all_events = []

    try:
        all_events.extend(fetch_bristol_city())
    except Exception as e:
        print("Football API failed:", e)

    try:
        all_events.extend(fetch_bristol_bears())
    except Exception as e:
        print("Rugby API failed:", e)

    try:
        all_events.extend(fetch_ashton_gate_events())
    except Exception as e:
        print("Eventbrite API failed:", e)

    if not all_events:
        print("No events found — keeping previous events.json")
        return

    with open(CONFIG["output"]["events_json"], "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2)

    generate_ics(all_events)

if __name__ == "__main__":
    main()

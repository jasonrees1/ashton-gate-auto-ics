import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def fetch_bcfc():
    url = "https://www.bcfc.co.uk/matches/fixtures/"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    events = []

    for item in soup.select(".fixture-item"):
        title = item.select_one("h3").get_text(strip=True)
        date = item.select_one(".fixture-date").get_text(strip=True)
        time = item.select_one(".fixture-time").get_text(strip=True)
        dt = datetime.strptime(f"{date} {time}", "%A %d %B %Y %H:%M")
        events.append({
            "title": f"Bristol City – {title}",
            "start": dt.isoformat(),
            "duration": 120
        })
    return events

def fetch_bears():
    url = "https://www.bristolbearsrugby.com/fixtures/"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    events = []

    for item in soup.select(".fixture"):
        title = item.select_one("h3").get_text(strip=True)
        date = item.select_one(".date").get_text(strip=True)
        time = item.select_one(".time").get_text(strip=True)
        dt = datetime.strptime(f"{date} {time}", "%A %d %B %Y %H:%M")
        events.append({
            "title": f"Bristol Bears – {title}",
            "start": dt.isoformat(),
            "duration": 120
        })
    return events

def fetch_ashton_gate():
    url = "https://www.ashtongatestadium.co.uk/whats-on/"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    events = []

    for card in soup.select(".event-card"):
        title = card.select_one("h3").get_text(strip=True)
        date = card.select_one(".date").get_text(strip=True)
        time = card.select_one(".time").get_text(strip=True)
        dt = datetime.strptime(f"{date} {time}", "%A %d %B %Y %H:%M")
        events.append({
            "title": f"Ashton Gate – {title}",
            "start": dt.isoformat(),
            "duration": 180
        })
    return events

all_events = fetch_bcfc() + fetch_bears() + fetch_ashton_gate()

with open("events.json", "w") as f:
    json.dump(all_events, f, indent=2)

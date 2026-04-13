import json
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def fetch_page(url, selector_to_wait_for):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector(selector_to_wait_for)
        html = page.content()
        browser.close()
        return html

def fetch_bcfc():
    url = "https://www.bcfc.co.uk/matches/fixtures/"
    html = fetch_page(url, ".fixtures-list")
    soup = BeautifulSoup(html, "html.parser")
    events = []

    for item in soup.select(".fixtures-list .fixture"):
        title = item.select_one(".fixture__opposition").get_text(strip=True)
        date = item.select_one(".fixture__date").get_text(strip=True)
        time = item.select_one(".fixture__time").get_text(strip=True)

        dt = datetime.strptime(f"{date} {time}", "%A %d %B %Y %H:%M")
        events.append({
            "title": f"Bristol City – {title}",
            "start": dt.isoformat(),
            "duration": 120
        })
    return events

def fetch_bears():
    url = "https://www.bristolbearsrugby.com/fixtures/"
    html = fetch_page(url, ".fixtures")
    soup = BeautifulSoup(html, "html.parser")
    events = []

    for item in soup.select(".fixtures .fixture"):
        title = item.select_one(".fixture__opposition").get_text(strip=True)
        date = item.select_one(".fixture__date").get_text(strip=True)
        time = item.select_one(".fixture__time").get_text(strip=True)

        dt = datetime.strptime(f"{date} {time}", "%A %d %B %Y %H:%M")
        events.append({
            "title": f"Bristol Bears – {title}",
            "start": dt.isoformat(),
            "duration": 120
        })
    return events

def fetch_ashton_gate():
    url = "https://www.ashtongatestadium.co.uk/whats-on/"
    html = fetch_page(url, ".event-card")
    soup = BeautifulSoup(html, "html.parser")
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

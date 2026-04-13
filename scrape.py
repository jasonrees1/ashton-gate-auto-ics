import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TZ = ZoneInfo(CONFIG["timezone"])


def parse_bbc_date(date_str: str, time_str: str | None):
    now = datetime.now(TZ)

    candidates = [
        "%a %d %b %Y",
        "%A %d %B %Y",
        "%a, %d %b %Y",
        "%A, %d %B %Y",
        "%d %B %Y",
        "%d %b %Y"
    ]

    base = f"{date_str} {now.year}"
    dt = None
    for fmt in candidates:
        try:
            dt = datetime.strptime(base, fmt)
            break
        except ValueError:
            continue

    if dt is None:
        return None

    if time_str:
        try:
            t = datetime.strptime(time_str, "%H:%M").time()
            dt = datetime.combine(dt.date(), t)
        except ValueError:
            dt = datetime.combine(dt.date(), datetime.min.time())
    else:
        dt = datetime.combine(dt.date(), datetime.min.time())

    if dt.replace(tzinfo=TZ) < now and (now - dt.replace(tzinfo=TZ)).days > 270:
        dt = dt.replace(year=dt.year + 1)

    return dt.replace(tzinfo=TZ)


def scrape_bbc_team(team_name: str, url: str, sport: str):
    print(f"Scraping BBC for {team_name}: {url}")
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    events = []

    fixture_blocks = soup.find_all(["article", "div"], attrs={"data-event-id": True})
    if not fixture_blocks:
        fixture_blocks = soup.find_all(["article", "div"], class_=lambda c: c and "fixture" in c.lower())

    for block in fixture_blocks:
        text = " ".join(block.stripped_strings)

        if team_name.lower() not in text.lower():
            continue

        line_candidates = [l for l in text.split("\n") if " v " in l or " vs " in l]
        fixture_line = line_candidates[0] if line_candidates else text

        is_home = False
        opponent = None
        for sep in [" v ", " vs "]:
            if sep in fixture_line:
                left, right = fixture_line.split(sep, 1)
                if team_name.lower() in left.lower():
                    is_home = True
                    opponent = right.strip()
                elif team_name.lower() in right.lower():
                    is_home = False
                    opponent = left.strip()
                break

        if not is_home:
            continue

        date_el = block.find(["time", "span"], attrs={"data-testid": "date"})
        if not date_el:
            date_el = block.find(["time", "span"])
        date_str = date_el.get_text(strip=True) if date_el else None

        time_el = block.find

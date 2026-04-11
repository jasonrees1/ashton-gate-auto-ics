import json
from datetime import datetime, timedelta

def to_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Ashton Gate Auto Feed//EN"
    ]

    for e in events:
        start = datetime.fromisoformat(e["start"])
        end = start + timedelta(minutes=e["duration"])

        lines += [
            "BEGIN:VEVENT",
            f"SUMMARY:{e['title']}",
            f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
            "BEGIN:VALARM",
            "TRIGGER:-PT12H",
            "ACTION:DISPLAY",
            "DESCRIPTION:Event reminder",
            "END:VALARM",
            "END:VEVENT"
        ]

    lines.append("END:VCALENDAR")
    return "\n".join(lines)

with open("events.json") as f:
    events = json.load(f)

with open("calendar.ics", "w") as f:
    f.write(to_ics(events))

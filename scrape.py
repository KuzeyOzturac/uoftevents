"""Refresh the public U of T events index into one JSON feed."""
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path


SOURCE = "https://www.utoronto.ca/events"
OUT = Path(__file__).parent / "site" / "events.json"
ICS = Path(__file__).parent / "site" / "events.ics"
MONTHS = "January February March April May June July August September October November December".split()


class EventTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.link = None
        self.in_cell = False
        self.section = ""
        self.heading = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.row = []
        elif tag == "h3":
            self.heading = ""
        elif tag in ("td", "th") and self.row is not None:
            self.cell = {"text": "", "url": ""}
            self.in_cell = True
        elif tag == "a" and self.in_cell and self.cell and not self.cell["url"]:
            self.cell["url"] = attrs.get("href", "")

    def handle_data(self, data):
        if self.heading is not None:
            self.heading += data
        if self.in_cell and self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        if tag == "h3" and self.heading is not None:
            self.section = " ".join(self.heading.split())
            self.heading = None
        elif tag in ("td", "th") and self.cell is not None:
            self.cell["text"] = " ".join(self.cell["text"].split())
            self.row.append(self.cell)
            self.cell = None
            self.in_cell = False
        elif tag == "tr" and self.row is not None:
            if len(self.row) >= 2:
                self.rows.append((self.row, self.section))
            self.row = None


def parse(html):
    parser = EventTable()
    parser.feed(html)
    events = []
    by_url = {}
    for row, section in parser.rows:
        title, date = row[0]["text"], row[1]["text"]
        url = row[0]["url"]
        if not url or not re.search(r"\b20\d{2}\b", date):
            continue
        url = urllib.parse.urljoin(SOURCE, url)
        if urllib.parse.urlparse(url).scheme not in ("http", "https"):
            continue
        department = section if section != "Upcoming U of T events" else ""
        if url in by_url:
            existing = by_url[url]
            if department:
                if not existing["departments"]:
                    existing["departments"] = [department]
                elif department not in existing["departments"]:
                    existing["departments"].append(department)
            continue
        event = {"title": title, "date": date, "url": url,
                 "departments": [department] if department else [], "sources": ["U of T"]}
        events.append(event)
        by_url[url] = event
    for event in events:
        if not event["departments"]:
            event["departments"] = ["U of T"]
    return events


def first_day(label):
    match = re.search(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})\b.*?\b(20\d{2})\b", label, re.I)
    if not match:
        return None
    try:
        return datetime.strptime(f"{match[1]} {match[2]} {match[3]}", "%B %d %Y").date()
    except ValueError:
        return None


def ics_escape(value):
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def make_ics(events):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//UofT Event Scout//EN", "X-WR-CALNAME:U of T Events"]
    for event in events:
        day = first_day(event["date"])
        if not day:
            continue
        lines += ["BEGIN:VEVENT", f"UID:{urllib.parse.quote(event['url'], safe='')}@uoftevents",
                  f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{day + timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{ics_escape(event['title'])}",
                  f"DESCRIPTION:{ics_escape('Verify time, location, and registration: ' + event['url'])}",
                  f"URL:{event['url']}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main():
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "UofTEventsCalendar/1.0 (public events index)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        events = parse(response.read().decode("utf-8"))
    if len(events) < 5:
        raise RuntimeError(f"Found only {len(events)} U of T events; refusing to replace the feed")
    ICS.write_text(make_ics(events))
    if OUT.exists() and json.loads(OUT.read_text()).get("events") == events:
        print(f"No changes in {len(events)} events")
        return
    OUT.write_text(json.dumps({"updated_at": datetime.now().astimezone().isoformat(),
                               "sources": [SOURCE], "events": events}, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(events)} events")


if __name__ == "__main__":
    main()

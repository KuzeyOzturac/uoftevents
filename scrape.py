"""Refresh the public U of T events index into a small, reviewable JSON feed."""
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

SOURCE = "https://www.utoronto.ca/events"
OUT = Path(__file__).parent / "site" / "events.json"


class EventTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.link = None
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = {"text": "", "url": ""}
            self.in_cell = True
        elif tag == "a" and self.in_cell and self.cell and not self.cell["url"]:
            self.cell["url"] = attrs.get("href", "")

    def handle_data(self, data):
        if self.in_cell and self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.cell["text"] = " ".join(self.cell["text"].split())
            self.row.append(self.cell)
            self.cell = None
            self.in_cell = False
        elif tag == "tr" and self.row is not None:
            if len(self.row) >= 2:
                self.rows.append(self.row)
            self.row = None


def parse(html):
    parser = EventTable()
    parser.feed(html)
    events = []
    seen = set()
    for row in parser.rows:
        title, date = row[0]["text"], row[1]["text"]
        url = row[0]["url"]
        if not url or not re.search(r"\b20\d{2}\b", date):
            continue
        url = urllib.parse.urljoin(SOURCE, url)
        if urllib.parse.urlparse(url).scheme not in ("http", "https"):
            continue
        if url in seen:
            continue
        seen.add(url)
        events.append({"title": title, "date": date, "url": url,
                       "unit": row[2]["text"] if len(row) > 2 else ""})
    return events


def main():
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "UofTEventsCalendar/1.0 (public events index)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        events = parse(response.read().decode("utf-8"))
    if len(events) < 5:
        raise RuntimeError(f"Found only {len(events)} events; refusing to replace the feed")
    if OUT.exists() and json.loads(OUT.read_text()).get("events") == events:
        print(f"No changes in {len(events)} events")
        return
    OUT.write_text(json.dumps({"updated_at": datetime.now().astimezone().isoformat(),
                               "source": SOURCE, "events": events}, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(events)} events")


if __name__ == "__main__":
    main()

# U of T Event Scout

A public, searchable view of the [University of Toronto events index](https://www.utoronto.ca/events). The daily GitHub Action refreshes `site/events.json` and `site/events.ics`. The site reads the JSON feed and offers individual calendar downloads. Subscribe to the `.ics` URL in a separate calendar for ongoing updates.

The website is configured for GitHub Pages at https://kuzeyozturac.github.io/uoftevents/ . In repository Settings → Pages, select **GitHub Actions** as the publishing source. The same workflow refreshes the feed and deploys the `site/` folder after every run.

The calendar entry is all-day because the index often omits times. Always check the organizer's page for time, location, registration, and eligibility. This first version covers only the public U of T events index, which does not contain every St. George event.

Run `python scrape.py` to refresh locally. The script refuses to overwrite the feed when it finds fewer than five events, so a changed source layout fails visibly in GitHub Actions. Open `site/index.html` through a local web server to preview the page.

# U of T Event Scout

A public, searchable view of the [University of Toronto events index](https://www.utoronto.ca/events) and [Hart House monthly calendar](https://harthouse.ca/events/month). The page supports text search, multiple department selections, and date ranges. The GitHub Action refreshes U of T events and deploys the site. A local scheduled refresh updates Hart House events because Hart House blocks GitHub-hosted runners. Hart House coverage includes the current month and next two months.

The website is configured for GitHub Pages at https://kuzeyozturac.github.io/uoftevents/ . In repository Settings → Pages, select **GitHub Actions** as the publishing source. The same workflow refreshes the feed and deploys the `site/` folder after every run.

Always check the organizer's page for time, location, registration, and eligibility. These public sources do not contain every St. George event.

Install `requirements.txt`, then run `python scrape.py` to refresh both sources locally. GitHub Actions runs `python scrape.py --university-only`, retaining the last Hart House snapshot. The script refuses to overwrite the feed when a source yields fewer than five events. Open `site/index.html` through a local web server to preview the page.

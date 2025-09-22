import csv
import requests
from bs4 import BeautifulSoup

INPUT_CSV = "tal_episodes.csv"
OUTPUT_CSV = "tal_episodes_full.csv"

def scrape_episode(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")

    # releaseDate
    release_span = soup.select_one("span.date-display-single")
    release_date = release_span.get_text(strip=True) if release_span else ""

    # Acts
    acts_divs = soup.select("div.field-item article.node-act")
    act_texts = []
    seen_headers = set()
    for act in acts_divs:
        header = act.select_one("header .field-item")
        header_text = header.get_text(strip=True) if header else ""
        if header_text in seen_headers:
            continue  # skip duplicate Prologue etc.
        seen_headers.add(header_text)

        # Act title (h2)
        h2 = act.select_one("h2.act-header a")
        act_title = h2.get_text(strip=True) if h2 else header_text

        # Body
        body_div = act.select_one("div.field-name-body")
        body_text = body_div.get_text(" ", strip=True) if body_div else ""

        # Contributor
        contributor_div = act.select_one("div.field-name-field-contributor .field-item")
        contributor = contributor_div.get_text(strip=True) if contributor_div else ""

        # Song (optional)
        song_div = act.select_one("div.field-name-field-song .field-item a")
        song = song_div.get_text(strip=True) if song_div else ""

        parts = [f"{header_text}: {act_title}", body_text]
        if contributor:
            parts.append(f"By {contributor}")
        if song:
            parts.append(f"Song:{song}")
        act_texts.append("\n".join(parts))

    description = "\n\n".join(act_texts)
    return release_date, description

# Read CSV and update
with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for row in rows:
    if not row["link"]:
        continue
    try:
        release_date, description = scrape_episode(row["link"])
        row["releaseDate"] = release_date
        row["description"] = description
    except Exception as e:
        print(f"Error scraping {row['link']}: {e}")

# Write updated CSV
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved updated CSV to {OUTPUT_CSV}")

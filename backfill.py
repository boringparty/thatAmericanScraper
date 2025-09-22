import requests
from bs4 import BeautifulSoup
import csv
import time
import feedparser

RSS_URL = "https://awk.space/tal.xml"
CSV_FILE = "tal_episodes_full.csv"

def fetch_episode_page(url, retries=3):
    for attempt in range(retries):
        try:
            time.sleep(1)  # throttle requests
            r = requests.get(url)
            r.raise_for_status()
            return BeautifulSoup(r.text, "lxml")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error {e} on {url}, attempt {attempt+1}")
            if attempt == retries - 1:
                print(f"Skipping {url}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request exception {e} on {url}, skipping")
            return None

def parse_episode(entry):
    title_raw = entry.title.strip()
    if not title_raw[0].isdigit():
        return None  # skip non-numbered episodes

    ep_num, ep_title = title_raw.split(":", 1)
    ep_num = ep_num.strip()
    ep_title = ep_title.strip()

    link = entry.link
    subtitle = entry.description.strip()
    release_date = entry.pubDate.strip()
    pub_date = ""  # leave blank for now

    soup = fetch_episode_page(link)
    description_parts = []

    if soup:
        # get top release date if available
        date_tag = soup.find("span", class_="date-display-single")
        if date_tag:
            release_date = date_tag.get_text(strip=True)

        # get acts / prologue
        acts = soup.select("article.node-act")
        for act in acts:
            header = act.find("div", class_="field-name-field-act-label")
            header_text = header.get_text(strip=True) if header else ""
            body = act.find("div", class_="field-name-body")
            body_text = body.get_text(separator="\n", strip=True) if body else ""
            by = act.select_one(".field-name-field-contributor .field-item")
            by_text = f"By {by.get_text(strip=True)}" if by else ""
            song = act.select_one(".field-name-field-song .field-item a")
            song_text = f"Song:{song.get_text(strip=True)}" if song else ""
            if header_text or body_text or by_text or song_text:
                description_parts.append("\n".join(filter(None, [header_text, body_text, by_text, song_text])))

        # find clean version
        clean_link_tag = soup.find("a", href=lambda x: x and "clean" in x)
        clean_url = clean_link_tag["href"] if clean_link_tag else ""

    else:
        description_parts.append(subtitle)
        clean_url = ""

    description_full = "\n\n".join(description_parts)

    return {
        "title": f"{ep_num}: {ep_title}",
        "link": link,
        "description": f"{subtitle}\n\n{description_full}",
        "pubDate": pub_date,
        "releaseDate": release_date,
        "guid": "",
        "episodeType": "Full",
        "episode": ep_num,
        "itunes_title": ep_title,
        "author": "This American Life",
        "explicit": "no",
        "image": "",
        "enclosure": "",  # will populate from main RSS
        "duration": "",
        "subtitle": subtitle,
        "summary": "",
        "clean": clean_url
    }

def main():
    feed = feedparser.parse(RSS_URL)
    rows = []

    for entry in feed.entries:
        ep_data = parse_episode(entry)
        if ep_data:
            rows.append(ep_data)

    # write CSV with proper quoting
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    main()

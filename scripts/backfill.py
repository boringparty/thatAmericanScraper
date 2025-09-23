import requests
from bs4 import BeautifulSoup
import feedparser
import csv
import time
import re

RSS_URL = "https://awk.space/tal.xml"
CSV_FILE = "../tal_episodes_full.csv"

# Sleep between page requests
DELAY = 1  # seconds

# CSV columns
COLUMNS = [
    "title","link","description","pubDate","releaseDate","guid","episodeType","episode",
    "itunes_title","author","explicit","image","enclosure","duration","subtitle","summary","clean"
]

def fetch_episode_page(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        time.sleep(DELAY)
        return BeautifulSoup(r.text, "lxml")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_episode(entry):
    link = entry.link
    soup = fetch_episode_page(link)
    
    subtitle = entry.description.strip() if hasattr(entry, "description") else ""

    # Use pubDate from RSS
    pub_date = getattr(entry, "published", None) or getattr(entry, "pubDate", None) or getattr(entry, "updated", "")
    pub_date = pub_date.strip() if pub_date else ""

    # Release date from page
    release_date = ""
    if soup:
        span = soup.find("span", class_="date-display-single")
        if span:
            raw = span.text.strip()
            try:
                from datetime import datetime
                dt = datetime.strptime(raw, "%B %d, %Y")
                release_date = dt.strftime("%Y-%m-%dT%H:%M:%S-00:00")
            except ValueError:
                release_date = raw

    # Title parsing
    title_text = entry.title.strip()
    episode_match = re.match(r"(\d+):\s*(.*)", title_text)
    if episode_match:
        episode_num, episode_title = episode_match.groups()
    else:
        episode_num, episode_title = "", title_text

    # Acts and description
    description_parts = []
    clean_url = ""
    if soup:
        content_div = soup.select_one("div.content")
        if content_div:
            for act in content_div.select("article.node-act"):
                header = act.select_one("div.field-name-field-act-label")
                act_name = header.get_text(strip=True) if header else ""
                
                body = act.select_one("div.field-name-body")
                body_text = body.get_text(" ", strip=True) if body else ""
                
                contributor = act.select_one("div.field-name-field-contributor")
                author_text = contributor.get_text(" ", strip=True) if contributor else ""
                
                song_field = act.select_one("div.field-name-field-song a")
                song_text = f'Song:{song_field.get_text(strip=True)}' if song_field else ""
                
                if act_name or body_text or author_text or song_text:
                    parts = []
                    if act_name: parts.append(act_name)
                    if body_text: parts.append(body_text)
                    if author_text: parts.append(f"{author_text}")
                    if song_text: parts.append(song_text)
                    description_parts.append("\n".join(parts))
        
        # Find clean episode
        clean_link_tag = soup.find("a", href=re.compile(r"clean.*\.mp3"))
        if clean_link_tag:
            clean_url = clean_link_tag["href"]
    
    description_text = "\n\n".join(description_parts)

    row = {
        "title": title_text,
        "link": link,
        "description": description_text,
        "pubDate": pub_date,
        "releaseDate": release_date,
        "guid": "",
        "episodeType": "Full",
        "episode": episode_num,
        "itunes_title": episode_title,
        "author": "This American Life",
        "explicit": "yes",
        "image": "",
        "enclosure": "",  # weekly RSS will fill this
        "duration": "",
        "subtitle": subtitle,
        "summary": "",
        "clean": clean_url
    }
    return row

def main():
    feed = feedparser.parse(RSS_URL)
    rows = []
    for entry in feed.entries:
        if re.match(r"\d+:.*", entry.title):
            ep_data = parse_episode(entry)
            rows.append(ep_data)
    
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Saved {len(rows)} episodes to {CSV_FILE}")

if __name__ == "__main__":
    main()

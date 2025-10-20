import csv
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "..", "tal_episodes.csv")
RSS_URL = "https://thisamericanlife.org/podcast/rss.xml"

# Namespace map
ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}

# CSV columns
fields = [
    "title","link","description","pubDate","releaseDate","guid",
    "episodeType","episode","itunes_title","author","explicit",
    "image","enclosure","duration","subtitle","summary","clean"
]

def fetch_episode_page(url):
    time.sleep(1)  # avoid hammering the site
    try:
        r = requests.get(url)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def normalize_description(text):
    text = text.strip()
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'^(Prologue|Act \w+):\s*', r'\1\n', text, flags=re.MULTILINE)
    return text

def get_release_date(soup):
    span = soup.find("span", class_="date-display-single")
    if not span:
        return ""
    raw = span.text.strip()  # e.g., "November 6, 2020"
    try:
        dt = datetime.strptime(raw, "%B %d, %Y")
        return dt.strftime("%Y-%m-%dT%H:%M:%S-00:00")  # ISO 8601
    except ValueError:
        return raw

def get_clean_episode(soup):
    link = soup.find("a", href=re.compile(r"clean"))
    return link['href'] if link else ""

# --- Fetch RSS ---
resp = requests.get(RSS_URL)
resp.raise_for_status()
root = ET.fromstring(resp.content)
items = root.findall(".//item")

# --- Read existing CSV ---
try:
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
except FileNotFoundError:
    existing = []

# --- Build set of normalized existing keys (releaseDate, title) ---
existing_keys = {
    (row['releaseDate'].strip(), row['title'].strip().lower())
    for row in existing
}

# --- Prepare new rows ---
new_rows = []

for item in items[:1]:  # latest only
    link = item.findtext("link", default="").strip()
    soup = fetch_episode_page(link)
    if soup is None:
        print(f"Skipping episode {link}")
        continue

    # Normalize releaseDate and title for deduplication
    release_date = get_release_date(soup)
    release_date_key = release_date.split("T")[0].strip()
    title = item.findtext("title", default="").strip()
    title_key = title.lower()

    # Skip duplicates
    if (release_date_key, title_key) in existing_keys:
        print(f"Skipping duplicate: {title} ({release_date_key})")
        continue

    # Normalize description
    raw_desc = item.findtext("itunes:summary", default="", namespaces=ns)
    description = normalize_description(raw_desc)
    clean_url = get_clean_episode(soup)

    # Explicit flag
    explicit_raw = item.findtext("itunes:explicit", default="no", namespaces=ns).lower()
    explicit_flag = "true" if (explicit_raw in ("yes", "true") or not clean_url) else "false"

    row = {
        "title": title,
        "link": link,
        "description": description,
        "pubDate": item.findtext("pubDate", default="").strip(),
        "releaseDate": release_date_key,
        "guid": item.findtext("guid", default="").strip(),
        "episodeType": "full",
        "episode": item.findtext("itunes:episode", default="", namespaces=ns).strip(),
        "itunes_title": item.findtext("itunes:title", default="", namespaces=ns).strip(),
        "author": "This American Life",
        "explicit": explicit_flag,
        "image": item.find("itunes:image", ns).attrib.get("href").strip() if item.find("itunes:image", ns) is not None else "",
        "enclosure": item.find("enclosure").attrib.get("url").strip() if item.find("enclosure") is not None else "",
        "duration": item.findtext("itunes:duration", default="", namespaces=ns).strip(),
        "subtitle": item.findtext("itunes:subtitle", default="", namespaces=ns).strip(),
        "summary": "",
        "clean": clean_url
    }
    new_rows.append(row)
    existing_keys.add((release_date_key, title_key))  # prevent duplicates within the same run

# --- Write CSV: prepend new episodes ---
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in new_rows + existing:
        writer.writerow(row)

print(f"Saved {len(new_rows)} new episode(s) to {CSV_FILE}")

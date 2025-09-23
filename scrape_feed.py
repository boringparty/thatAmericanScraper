import csv
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime

RSS_URL = "https://www.thisamericanlife.org/podcast/rss.xml"
CSV_FILE = "tal_episodes.csv"

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
    # ensure a blank line between paragraphs
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    # put a newline after Prologue: or Act One:, Act Two:, etc.
    text = re.sub(r'(Prologue:|Act \w+:) ', r'\1\n', text)
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

# Fetch RSS
resp = requests.get(RSS_URL)
resp.raise_for_status()
root = ET.fromstring(resp.content)
items = root.findall(".//item")

# Read existing CSV if exists
try:
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
except FileNotFoundError:
    existing = []

# Prepare new rows (latest episode only)
new_rows = []

for item in items[:1]:  # only the latest
    link = item.findtext("link", default="")
    soup = fetch_episode_page(link)
    if soup is None:
        print(f"Skipping episode {link}")
        continue
    
    raw_desc = item.findtext("itunes:summary", default="", namespaces=ns)
    description = normalize_description(raw_desc)
    
    row = {
        "title": item.findtext("title", default=""),
        "link": link,
        "description": normalize_description(item.findtext("itunes:summary", default="", namespaces=ns)),
        "pubDate": item.findtext("pubDate", default=""),
        "releaseDate": get_release_date(soup),
        "guid": item.findtext("guid", default=""),
        "episodeType": "full",
        "episode": item.findtext("itunes:episode", default="", namespaces=ns),
        "itunes_title": item.findtext("itunes:title", default="", namespaces=ns),
        "author": "This American Life",
        "explicit": "no" if item.findtext("itunes:explicit", default="", namespaces=ns) == "false" else item.findtext("itunes:explicit", default="", namespaces=ns),
        "image": item.find("itunes:image", ns).attrib.get("href") if item.find("itunes:image", ns) is not None else "",
        "enclosure": item.find("enclosure").attrib.get("url") if item.find("enclosure") is not None else "",
        "duration": item.findtext("itunes:duration", default="", namespaces=ns),
        "subtitle": item.findtext("itunes:subtitle", default="", namespaces=ns),
        "summary": "",
        "clean": get_clean_episode(soup)
    }
    new_rows.append(row)

# Write CSV: new episode(s) at the top
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in new_rows + existing:
        writer.writerow(row)

print(f"Saved {len(new_rows)} new episode(s) to {CSV_FILE}")

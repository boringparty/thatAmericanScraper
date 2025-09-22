import csv
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time

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
    r = requests.get(url)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")

def get_release_date(soup):
    span = soup.find("span", class_="date-display-single")
    return span.text.strip() if span else ""

def get_clean_episode(soup):
    link = soup.find("a", href=re.compile(r"clean"))
    return link['href'] if link else ""

def normalize_description(text):
    return re.sub(r'\n\s*\n+', '\n', text.strip())

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

# We'll prepend the new episode
new_rows = []

for item in items[:1]:  # only the latest episode
    link = item.findtext("link", default="")
    soup = fetch_episode_page(link)
    
    raw_desc = item.findtext("itunes:summary", default="", namespaces=ns)
    description = normalize_description(raw_desc)
    
    row = {
        "title": item.findtext("title", default=""),
        "link": link,
        "description": description,
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
        "summary": item.findtext("itunes:summary", default="", namespaces=ns),
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
